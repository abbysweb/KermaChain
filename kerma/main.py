from kerma.network.peer import Peer
from kerma.network.peers import Peers
from kerma.validator import Validator
from kerma import constants as const
from kerma.network.exceptions import *
from kerma.storage.jcs import canonicalize

import kerma.mempool as mempool
import kerma.objects as objects
import kerma.storage.db as create_db
from kerma.network import protocol

import asyncio
import ipaddress
import json
import random
import re
import sqlite3
import sys
import traceback

VALIDATOR = Validator()
PEERS = Peers()
CONNECTIONS = dict()
BACKGROUND_TASKS = set()

MEMPOOL = mempool.Mempool(const.GENESIS_BLOCK_ID, {})

LISTEN_CFG = {
    "address": const.ADDRESS,
    "port": const.PORT
}
CHAINTIP = const.GENESIS_BLOCK_ID
CHAINTIP_HEIGHT = 0


def add_peer(peer):
    if peer.host in const.BANNED_HOSTS:
        return
    try:
        ip = ipaddress.ip_address(peer.host)
        if ip.is_multicast:
            return
    except Exception:
        pass
    PEERS.addPeer(peer)


def add_connection(peer, queue):
    ip, port = peer
    p = Peer(ip, port)
    if p in CONNECTIONS:
        raise Exception("Connection with {} already open!".format(peer))
    CONNECTIONS[p] = queue


def del_connection(peer):
    ip, port = peer
    p = Peer(ip, port)
    if p in CONNECTIONS:
        del CONNECTIONS[p]
    PEERS.removePeer(p)
    PEERS.save()


async def broadcast_msg(msg):
    for k, q in CONNECTIONS.items():
        await q.put(msg)


async def handle_object_msg(msg_dict, queue):
    global CHAINTIP
    global CHAINTIP_HEIGHT
    obj_dict = msg_dict['object']
    objid = objects.get_objid(obj_dict)
    print(f"Received object: {objid} ({obj_dict['type']})")

    con = sqlite3.connect(const.DB_NAME)
    try:
        cur = con.cursor()

        res = cur.execute("SELECT obj FROM objects WHERE oid = ?", (objid,))
        already_known = res.fetchone() is not None

        if not already_known:
            print("Received new object '{}'".format(objid))
            VALIDATOR.received_object(objid)
            if VALIDATOR.is_pending(objid):
                VALIDATOR.add_peer(objid, queue)
                return

        if obj_dict['type'] == 'transaction':
            if not already_known:
                prev_txs = protocol.gather_previous_txs(cur, obj_dict)
                objects.verify_transaction(obj_dict, prev_txs)
                objects.store_transaction(obj_dict, cur)
                con.commit()

            if 'height' not in obj_dict:
                try:
                    if MEMPOOL.try_add_tx(obj_dict):
                        print(f"Added tx {objid} to mempool")
                    else:
                        print(f"Mempool rejected tx {objid} (likely valid but conflict/orphan)")
                except Exception as e:
                    print(f"CRITICAL: Mempool add crashed for {objid}: {e}")
                    traceback.print_exc()

        elif obj_dict['type'] == 'block':
            height = None
            if not already_known:
                new_utxo, height = objects.verify_block(obj_dict)
                objects.store_block(obj_dict, new_utxo, height, cur)
            else:
                res = cur.execute("SELECT height FROM heights WHERE blockid = ?", (objid,))
                row = res.fetchone()
                if row:
                    height = row[0]

            if height is not None:
                if height > CHAINTIP_HEIGHT:
                    CHAINTIP_HEIGHT = height
                    CHAINTIP = objid

                    con.commit()
                    print(f"New chaintip {objid[:8]} (h={height}), rebasing mempool...")
                    try:
                        MEMPOOL.rebase_to_block(objid)
                    except Exception as e:
                        print(f"Mempool rebase failed: {e}")
                        traceback.print_exc()

                    if not already_known:
                        await broadcast_msg(protocol.mk_chaintip_msg(CHAINTIP))

                con.commit()

            if not already_known:
                print("Added new object '{}'".format(objid))
                VALIDATOR.new_valid_object(objid)
                await broadcast_msg(protocol.mk_ihaveobject_msg(objid))

    except NeedMoreObjects as e:
        print(f"Need more elements: {e.message}")
        VALIDATOR.verification_pending(obj_dict, queue, e.missingobjids)
        for q in CONNECTIONS.values():
            for missingobjid in e.missingobjids:
                await q.put(protocol.mk_getobject_msg(missingobjid))
        return
    except NodeException as e:
        con.rollback()
        print("Failed to verify object '{}': {}".format(objid, str(e)))
        raise e
    except Exception as e:
        print(f"An exception occured: {str(e)}")
        traceback.print_exc()
        con.rollback()
        raise e
    finally:
        con.close()


def get_chaintip_blockid():
    con = sqlite3.connect(const.DB_NAME)
    try:
        cur = con.cursor()
        res = cur.execute("SELECT blockid, height FROM heights ORDER BY height DESC LIMIT 1")
        row = res.fetchone()
        if row is None:
            return (const.GENESIS_BLOCK_ID, 0)
        return (row[0], row[1])
    except Exception as e:
        con.rollback()
        raise e
    finally:
        con.close()


async def handle_queue_msg(msg_dict, writer):
    if msg_dict['type'] == 'resumeValidation':
        await handle_object_msg(msg_dict, None)
    else:
        await protocol.write_msg(writer, msg_dict)


async def handle_connection(reader, writer):
    read_task = None
    queue_task = None

    peer = None
    queue = asyncio.Queue()
    try:
        peer = writer.get_extra_info('peername')
        if not peer:
            raise Exception("Failed to get peername!")
        host, port = peer[0], peer[1]
        add_connection((host, port), queue)
        print("New connection with {}:{}".format(host, port))
    except Exception as e:
        print(str(e))
        try:
            writer.close()
        except Exception:
            pass
        return

    try:
        await protocol.write_msg(writer, protocol.mk_hello_msg())
        await protocol.write_msg(writer, protocol.mk_getpeers_msg())
        await protocol.write_msg(writer, protocol.mk_getchaintip_msg())
        await protocol.write_msg(writer, protocol.mk_getmempool_msg())

        firstmsg_str = await asyncio.wait_for(reader.readline(),
                timeout=const.HELLO_MSG_TIMEOUT)
        firstmsg = protocol.parse_msg(firstmsg_str)
        protocol.validate_hello_msg(firstmsg)

        msg_str = None
        while True:
            if read_task is None:
                read_task = asyncio.create_task(reader.readline())
            if queue_task is None:
                queue_task = asyncio.create_task(queue.get())

            done, pending = await asyncio.wait([read_task, queue_task],
                    return_when=asyncio.FIRST_COMPLETED)
            if read_task in done:
                msg_str = read_task.result()
                if not msg_str:
                    print(f"Disconnected.")
                    break
                read_task = None
            if queue_task in done:
                queue_msg = queue_task.result()
                queue_task = None
                await handle_queue_msg(queue_msg, writer)
                queue.task_done()

            if read_task is not None:
                continue

            try:
                msg = protocol.parse_msg(msg_str)
                protocol.validate_msg(msg)

                msg_type = msg['type']
                if msg_type == 'hello':
                    raise ErrorInvalidHandshake("Additional handshake initiated by peer!")
                elif msg_type == 'getpeers':
                    await protocol.write_msg(writer, protocol.mk_peers_msg(PEERS.getPeers()))
                elif msg_type == 'peers':
                    protocol.handle_peers_msg(msg, PEERS, add_peer)
                elif msg_type == 'error':
                    protocol.handle_error_msg(msg, peer)
                elif msg_type == 'ihaveobject':
                    await protocol.handle_ihaveobject_msg(msg, writer)
                elif msg_type == 'getobject':
                    await protocol.handle_getobject_msg(msg, writer)
                elif msg_type == 'object':
                    await handle_object_msg(msg, queue)
                elif msg_type == 'getchaintip':
                    await protocol.handle_getchaintip_msg(msg, writer, CHAINTIP)
                elif msg_type == 'chaintip':
                    result = await protocol.handle_chaintip_msg(msg)
                    if result is not None:
                        await broadcast_msg(result)
                elif msg_type == 'getmempool':
                    await protocol.handle_getmempool_msg(msg, writer, MEMPOOL)
                elif msg_type == 'mempool':
                    results = await protocol.handle_mempool_msg(msg, MEMPOOL)
                    for r in results:
                        await broadcast_msg(r)
            except NonfaultyNodeException as e:
                print("{}: A (nonfaulty) error occured: {}: {}".format(peer, e.error_name, e.message))
                await protocol.write_msg(writer, protocol.mk_error_msg(e.message, e.error_name))

    except asyncio.exceptions.TimeoutError:
        print("{}: Timeout".format(peer))
        try:
            await protocol.write_msg(writer, protocol.mk_error_msg("Timeout in handshake triggered", "INVALID_HANDSHAKE"))
        except Exception:
            pass
    except FaultyNodeException as e:
        PEERS.save()
        print("{}: Detected Faulty Node: {}: {}".format(peer, e.error_name, e.message))
        try:
            await protocol.write_msg(writer, protocol.mk_error_msg(e.message, e.error_name))
        except Exception:
            pass
    except Exception as e:
        print("{}: An error occured: {}".format(peer, str(e)))
        print(traceback.format_exc())
    finally:
        print("Closing connection")
        writer.close()
        if read_task is not None and not read_task.done():
            read_task.cancel()
        if queue_task is not None and not queue_task.done():
            queue_task.cancel()


async def connect_to_node(peer: Peer):
    try:
        reader, writer = await asyncio.open_connection(peer.host, peer.port,
                limit=const.RECV_BUFFER_LIMIT)
    except Exception as e:
        print(f"failed to connect to peer {peer.host}:{peer.port}: {str(e)}")
        if not peer.isBootstrap:
            PEERS.removePeer(peer)
            PEERS.save()
        return
    await handle_connection(reader, writer)


async def listen():
    server = await asyncio.start_server(handle_connection, LISTEN_CFG['address'],
            LISTEN_CFG['port'], limit=const.RECV_BUFFER_LIMIT)
    print("Listening on {}:{}".format(LISTEN_CFG['address'], LISTEN_CFG['port']))
    async with server:
        await server.serve_forever()


async def bootstrap():
    for p in const.PRELOADED_PEERS:
        p.tagBootstrap()
        add_peer(p)
        t = asyncio.create_task(connect_to_node(p))
        BACKGROUND_TASKS.add(t)
        t.add_done_callback(BACKGROUND_TASKS.discard)


def resupply_connections():
    cons = set(CONNECTIONS.keys())
    if len(cons) >= const.LOW_CONNECTION_THRESHOLD:
        return

    npeers = const.LOW_CONNECTION_THRESHOLD - len(cons)
    available_peers = PEERS.getPeers() - cons

    if len(available_peers) == 0:
        return

    if len(available_peers) < npeers:
        npeers = len(available_peers)

    print("Connecting to {} new peers.".format(npeers))

    chosen_peers = random.sample(tuple(available_peers), npeers)
    for p in chosen_peers:
        t = asyncio.create_task(connect_to_node(p))
        BACKGROUND_TASKS.add(t)
        t.add_done_callback(BACKGROUND_TASKS.discard)


async def init():
    global MEMPOOL
    global CHAINTIP
    global CHAINTIP_HEIGHT

    create_db.createDB()
    CHAINTIP, CHAINTIP_HEIGHT = get_chaintip_blockid()

    con = sqlite3.connect(const.DB_NAME)
    try:
        cur = con.cursor()
        res = cur.execute("SELECT utxoset FROM utxo WHERE blockid = ?", (CHAINTIP,))
        row = res.fetchone()
        tip_utxo = objects.expand_object(row[0]) if row else {}
        MEMPOOL = mempool.Mempool(CHAINTIP, tip_utxo)
        print(f"Mempool initialized at height {CHAINTIP_HEIGHT}, tip {CHAINTIP[:8]}")
    finally:
        con.close()

    bootstrap_task = asyncio.create_task(bootstrap())
    listen_task = asyncio.create_task(listen())

    while True:
        resupply_connections()
        await asyncio.sleep(const.SERVICE_LOOP_DELAY)

    await bootstrap_task
    await listen_task


def main():
    asyncio.run(init())


if __name__ == "__main__":
    if len(sys.argv) == 3:
        LISTEN_CFG['address'] = sys.argv[1]
        LISTEN_CFG['port'] = sys.argv[2]
    main()
