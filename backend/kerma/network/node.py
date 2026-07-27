from __future__ import annotations
import asyncio
import ipaddress
import random
import time
import traceback
from typing import Dict, Set, Optional, TYPE_CHECKING

from kerma.config import Config
from kerma.storage.database import Database
from kerma.core.blockchain import Blockchain
from kerma.core.mempool import Mempool
from kerma.core.transaction import Transaction
from kerma.core.block import Block
from kerma.crypto.hashing import get_objid
from kerma.network.peer import Peer
from kerma.network.peer_manager import PeerManager
from kerma.network.connection import Connection
from kerma.network.protocol import Protocol
from kerma.network.exceptions import *
from kerma.validator import Validator

if TYPE_CHECKING:
    from kerma.api.server import APIServer


class Node:
    def __init__(self, config: Config):
        self.config = config
        self.db = Database(config.db_name)
        self.blockchain = Blockchain(config, self.db)
        self.mempool: Optional[Mempool] = None
        self.peers = PeerManager()
        self.protocol = Protocol(config, self.db)
        self.validator = Validator()
        self.connections: Dict[Peer, asyncio.Queue] = {}
        self.background_tasks: Set[asyncio.Task] = set()
        self.api_server: Optional[APIServer] = None
        self._running = False

    async def start(self) -> None:
        self._running = True
        self.blockchain.initialize()
        tip = self.db.get_chaintip()
        if tip:
            tip_utxo = self.db.get_utxo(tip[0]) or {}
        else:
            tip_utxo = {}
        self.mempool = Mempool(self.blockchain.tip_id, tip_utxo, self.db)

        for p in self.config.bootstrap_peers:
            p.tag_bootstrap()
            self._add_peer(p)
            t = asyncio.create_task(self._connect_to(p))
            self.background_tasks.add(t)
            t.add_done_callback(self.background_tasks.discard)

        server = await asyncio.start_server(
            self._handle_connection, self.config.address, self.config.port,
            limit=self.config.recv_buffer_limit
        )
        print(f"Listening on {self.config.address}:{self.config.port}")

        loop_task = asyncio.create_task(self._service_loop())

        if self.api_server:
            api_task = asyncio.create_task(self.api_server.start(self))
            self.background_tasks.add(api_task)

        async with server:
            await server.serve_forever()

    def _add_peer(self, peer: Peer) -> None:
        if peer.host in self.config.banned_hosts:
            return
        try:
            ip = ipaddress.ip_address(peer.host)
            if ip.is_multicast:
                return
        except Exception:
            pass
        self.peers.add(peer)

    def _add_connection(self, peer: Peer, queue: asyncio.Queue) -> None:
        if peer in self.connections:
            raise Exception(f"Connection with {peer} already open")
        self.connections[peer] = queue

    def _del_connection(self, peer: Peer) -> None:
        self.connections.pop(peer, None)
        self.peers.remove(peer)
        self.peers.save()

    async def broadcast(self, msg: dict) -> None:
        for q in self.connections.values():
            await q.put(msg)

    async def _service_loop(self) -> None:
        while self._running:
            self._resupply_connections()
            await asyncio.sleep(self.config.service_loop_delay)

    def _resupply_connections(self) -> None:
        n = len(self.connections)
        if n >= self.config.low_connection_threshold:
            return
        needed = self.config.low_connection_threshold - n
        available = self.peers.get_all() - set(self.connections.keys())
        if not available:
            return
        chosen = random.sample(list(available), min(needed, len(available)))
        for p in chosen:
            t = asyncio.create_task(self._connect_to(p))
            self.background_tasks.add(t)
            t.add_done_callback(self.background_tasks.discard)

    async def _connect_to(self, peer: Peer) -> None:
        try:
            reader, writer = await asyncio.open_connection(
                peer.host, peer.port, limit=self.config.recv_buffer_limit
            )
        except Exception:
            if not peer.is_bootstrap:
                self.peers.remove(peer)
                self.peers.save()
            return
        await self._handle_connection(reader, writer)

    async def _handle_connection(self, reader, writer) -> None:
        queue = asyncio.Queue()
        peer_info = writer.get_extra_info("peername")
        if not peer_info:
            writer.close()
            return
        peer = Peer(peer_info[0], peer_info[1])
        self._add_connection(peer, queue)
        print(f"New connection with {peer}")

        read_task = None
        queue_task = None
        try:
            await self.protocol.write_msg(writer, self.protocol.mk_hello_msg())
            await self.protocol.write_msg(writer, self.protocol.mk_getpeers_msg())
            await self.protocol.write_msg(writer, self.protocol.mk_getchaintip_msg())
            await self.protocol.write_msg(writer, self.protocol.mk_getmempool_msg())

            first_msg = await asyncio.wait_for(reader.readline(), timeout=self.config.hello_timeout)
            first = self.protocol.parse_msg(first_msg.decode().strip())
            self.protocol.validate_hello(first)

            while True:
                if read_task is None:
                    read_task = asyncio.create_task(reader.readline())
                if queue_task is None:
                    queue_task = asyncio.create_task(queue.get())

                done, _ = await asyncio.wait([read_task, queue_task], return_when=asyncio.FIRST_COMPLETED)
                if read_task in done:
                    msg_bytes = read_task.result()
                    if not msg_bytes:
                        break
                    read_task = None
                if queue_task in done:
                    qmsg = queue_task.result()
                    queue_task = None
                    if qmsg.get("type") == "resumeValidation":
                        await self._handle_object_msg(qmsg, writer)
                    else:
                        await self.protocol.write_msg(writer, qmsg)
                    queue.task_done()

                if read_task is not None:
                    continue

                msg = self.protocol.parse_msg(msg_bytes.decode().strip())
                self.protocol.validate_msg(msg)
                msg_type = msg["type"]

                if msg_type == "hello":
                    raise ErrorInvalidHandshake("additional handshake")
                elif msg_type == "getpeers":
                    await self.protocol.write_msg(writer, self.protocol.mk_peers_msg(self.peers.get_all()))
                elif msg_type == "peers":
                    self.protocol.handle_peers_msg(msg, self._add_peer)
                    self.peers.save()
                elif msg_type == "error":
                    print(f"{peer}: error {msg.get('name')}: {msg.get('msg')}")
                elif msg_type == "ihaveobject":
                    need = self.protocol.handle_ihaveobject(msg)
                    if need:
                        await self.protocol.write_msg(writer, self.protocol.mk_getobject_msg(need))
                elif msg_type == "getobject":
                    resp = self.protocol.handle_getobject(msg)
                    await self.protocol.write_msg(writer, resp)
                elif msg_type == "object":
                    await self._handle_object_msg(msg, writer)
                elif msg_type == "getchaintip":
                    await self.protocol.write_msg(writer, self.protocol.mk_chaintip_msg(self.blockchain.tip_id))
                elif msg_type == "chaintip":
                    objid = msg.get("blockid")
                    obj = self.db.get_object(objid) if objid else None
                    if obj is None and objid:
                        await self.protocol.write_msg(writer, self.protocol.mk_getobject_msg(objid))
                elif msg_type == "getmempool":
                    await self.protocol.write_msg(writer, self.protocol.mk_mempool_msg(self.mempool.get_txids()))
                elif msg_type == "mempool":
                    for txid in msg.get("txids", []):
                        obj = self.db.get_object(txid)
                        if obj and obj["type"] == "transaction" and "height" not in obj:
                            self.mempool.try_add_tx(obj)

        except asyncio.TimeoutError:
            try:
                await self.protocol.write_msg(writer, self.protocol.mk_error_msg("timeout", "INVALID_HANDSHAKE"))
            except Exception:
                pass
        except FaultyNodeException as e:
            self.peers.save()
            try:
                await self.protocol.write_msg(writer, self.protocol.mk_error_msg(e.message, e.error_name))
            except Exception:
                pass
        except Exception as e:
            print(f"{peer}: error: {e}")
        finally:
            writer.close()
            self._del_connection(peer)
            if read_task and not read_task.done():
                read_task.cancel()
            if queue_task and not queue_task.done():
                queue_task.cancel()

    async def _handle_object_msg(self, msg: dict, writer) -> None:
        obj_dict = msg["object"]
        objid = get_objid(obj_dict)
        already_known = self.db.object_exists(objid)

        if not already_known:
            self.validator.received_object(objid)
            if self.validator.is_pending(objid):
                self.validator.add_peer(objid, None)
                return

        if obj_dict["type"] == "transaction":
            if not already_known:
                con = self.db._connect()
                try:
                    cur = con.cursor()
                    prev_txs = self.protocol.gather_previous_txs(cur, obj_dict)
                    tx = Transaction(obj_dict)
                    tx.validate_format()
                    tx.verify_inputs(prev_txs)
                    self.db.store_transaction(obj_dict)
                    con.commit()
                finally:
                    con.close()
            if "height" not in obj_dict:
                self.mempool.try_add_tx(obj_dict)

        elif obj_dict["type"] == "block":
            height = None
            if not already_known:
                block = Block(obj_dict)
                block.validate_format(self.config.block_target, self.config.genesis_block_id)
                previd = obj_dict.get("previd")
                prev_utxo = self.db.get_utxo(previd) if previd else ({} if objid == self.config.genesis_block_id else None)
                prev_height = self.db.get_height(previd) if previd else (-1 if objid == self.config.genesis_block_id else None)
                if prev_utxo is None or prev_height is None:
                    raise NeedMoreObjects(f"block {objid} missing parents", [previd] if previd else [])
                txs_data = {}
                for txid in obj_dict.get("txids", []):
                    t = self.db.get_object(txid)
                    if t:
                        txs_data[txid] = t
                missing = set(obj_dict.get("txids", [])) - set(txs_data.keys())
                if missing:
                    raise NeedMoreObjects(f"block {objid} missing txs", list(missing))
                new_utxo, height = self._verify_block_tail(obj_dict, prev_utxo, prev_height, txs_data)
                self.db.store_block(obj_dict, new_utxo, height)
            else:
                height = self.db.get_height(objid)

            if height is not None and height > self.blockchain.tip_height:
                self.blockchain.tip_height = height
                self.blockchain.tip_id = objid
                self.mempool.rebase_to_block(objid)
                if not already_known:
                    await self.broadcast(self.protocol.mk_chaintip_msg(self.blockchain.tip_id))

            if not already_known:
                self.validator.new_valid_object(objid)
                await self.broadcast(self.protocol.mk_ihaveobject_msg(objid))

    def _verify_block_tail(self, block_dict: dict, prev_utxo: dict, prev_height: int, txs_data: dict):
        import copy
        block = Block(block_dict)
        previd = block_dict.get("previd")
        if previd:
            prev_block = self.db.get_object(previd)
            if prev_block and prev_block["created"] >= block_dict["created"]:
                raise ErrorInvalidBlockTimestamp("not created after prev")

        utxo = copy.deepcopy(prev_utxo)
        height = prev_height + 1
        remaining_txids = list(block_dict.get("txids", []))
        cbtx = None
        if remaining_txids:
            first_txid = remaining_txids[0]
            first_tx = txs_data.get(first_txid)
            if first_tx and "height" in first_tx:
                cbtx = first_tx
                utxo[first_txid] = {"0": cbtx["outputs"][0]["value"]}
                if cbtx["height"] != height:
                    raise ErrorInvalidBlockCoinbase("height mismatch")
                remaining_txids = remaining_txids[1:]

        txfees = 0
        tx_obj = None
        for txid in remaining_txids:
            tx_data = txs_data.get(txid)
            if not tx_data:
                raise ErrorInvalidFormat(f"tx {txid} missing")
            if "height" in tx_data:
                raise ErrorInvalidBlockCoinbase("coinbase not at index 0")
            tx_obj = Transaction(tx_data)
            tx_obj.validate_format()
            tx_obj.verify_inputs(self._gather_tx_inputs(tx_data, txs_data, block_dict.get("txids", [])))
            fee = tx_obj.update_utxo(utxo)
            txfees += fee

        if cbtx and cbtx["outputs"][0]["value"] > self.config.block_reward + txfees:
            raise ErrorInvalidBlockCoinbase("reward too big")

        return utxo, height

    def _gather_tx_inputs(self, tx_data: dict, txs_data: dict, all_txids: list) -> dict:
        prev_txs = {}
        for inp in tx_data.get("inputs", []):
            ptxid = inp["outpoint"]["txid"]
            if ptxid in txs_data:
                prev_txs[ptxid] = txs_data[ptxid]
            else:
                obj = self.db.get_object(ptxid)
                if obj:
                    prev_txs[ptxid] = obj
        return prev_txs

    def get_stats(self) -> dict:
        return {
            "height": self.blockchain.get_height(),
            "tipId": self.blockchain.get_tip_id(),
            "peerCount": len(self.connections),
            "mempoolSize": len(self.mempool.get_txids()) if self.mempool else 0,
            "uptime": 0,
            "blocksTotal": self.blockchain.get_height() + 1,
        }
