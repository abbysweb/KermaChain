import random
import re
import ipaddress
import sqlite3
import json

import kerma.constants as const
import kerma.objects as objects

from kerma.network.peer import Peer
from kerma.network.exceptions import *
from kerma.storage.jcs import canonicalize


def mk_error_msg(error_str, error_name):
    return {"type": "error", "name": error_name, "msg": error_str}


def mk_hello_msg():
    return {"type": "hello", "version": const.VERSION, "agent": const.AGENT}


def mk_getpeers_msg():
    return {"type": "getpeers"}


def mk_peers_msg(peers_set):
    pl = [f'{peer}' for peer in peers_set]
    if len(pl) > 30:
        pl = random.sample(pl, 30)
    return {"type": "peers", "peers": pl}


def mk_getobject_msg(objid):
    return {"type": "getobject", "objectid": objid}


def mk_object_msg(obj_dict):
    return {"type": "object", "object": obj_dict}


def mk_ihaveobject_msg(objid):
    return {"type": "ihaveobject", "objectid": objid}


def mk_chaintip_msg(blockid):
    return {"type": "chaintip", "blockid": blockid}


def mk_mempool_msg(txids):
    return {"type": "mempool", "txids": txids}


def mk_getchaintip_msg():
    return {"type": "getchaintip"}


def mk_getmempool_msg():
    return {"type": "getmempool"}


def parse_msg(msg_str):
    try:
        msg = json.loads(msg_str)
    except Exception as e:
        raise ErrorInvalidFormat("JSON parse error: {}".format(str(e)))

    if not isinstance(msg, dict):
        raise ErrorInvalidFormat("Received message not a dictionary!")
    if 'type' not in msg:
        raise ErrorInvalidFormat("Key 'type' not set in message!")
    if not isinstance(msg['type'], str):
        raise ErrorInvalidFormat("Key 'type' is not a string!")

    return msg


async def write_msg(writer, msg_dict):
    msg_bytes = canonicalize(msg_dict)
    writer.write(msg_bytes)
    writer.write(b'\n')
    await writer.drain()


def validate_allowed_keys(msg_dict, allowed_keys, msg_type):
    if len(set(msg_dict.keys()) - set(allowed_keys)) != 0:
        raise ErrorInvalidFormat(
            "Message malformed: {} message contains invalid keys!".format(msg_type))


def validate_hello_msg(msg_dict):
    if msg_dict['type'] != 'hello':
        raise ErrorInvalidHandshake("Message type is not 'hello'!")

    try:
        if 'version' not in msg_dict:
            raise ErrorInvalidFormat("Message malformed: version is missing!")

        version = msg_dict['version']
        if not isinstance(version, str):
            raise ErrorInvalidFormat("Message malformed: version is not a string!")

        if not re.compile(r'0\.10\.\d').fullmatch(version):
            raise ErrorInvalidFormat("Version invalid")

        validate_allowed_keys(msg_dict, ['type', 'version', 'agent'], 'hello')

        if 'agent' not in msg_dict:
            raise ErrorInvalidFormat("Agent field not set")

        if not objects.validate_human_readable(msg_dict['agent']):
            raise ErrorInvalidFormat("Agent field not of the required format")

    except ErrorInvalidFormat as e:
        raise e
    except Exception as e:
        raise ErrorInvalidFormat("Message malformed: {}".format(str(e)))


def validate_hostname(host_str):
    if not re.compile(r'[a-zA-Z\d\.\-\_]{3,50}').fullmatch(host_str):
        return False
    if not re.compile(r'.*[a-zA-Z].*').fullmatch(host_str):
        return False
    if '.' not in host_str[1:-1]:
        return False
    return True


def validate_ipv4addr(host_str):
    if not re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}').fullmatch(host_str):
        return False
    try:
        ip = ipaddress.IPv4Address(host_str)
    except Exception:
        return False
    return True


def validate_peer_str(peer_str):
    peer_parts = peer_str.rsplit(':', 1)
    if len(peer_parts) != 2:
        raise ErrorInvalidFormat("No port given")

    host_str = peer_parts[0]
    port_str = peer_parts[1]

    try:
        port = int(port_str, 10)
    except Exception:
        raise ErrorInvalidFormat("Port not a decimal number")

    if port <= 0:
        raise ErrorInvalidFormat("Port too small")
    if port > 65535:
        raise ErrorInvalidFormat("Port too high")

    if (not validate_hostname(host_str)) and (not validate_ipv4addr(host_str)):
        raise ErrorInvalidFormat("Given peer address is neither a hostname nor an ipv4 address")

    return True


def validate_peers_msg(msg_dict):
    try:
        if 'peers' not in msg_dict:
            raise ErrorInvalidFormat("Message malformed: peers is missing!")

        peers = msg_dict['peers']
        if not isinstance(peers, list):
            raise ErrorInvalidFormat("Message malformed: peers is not a list!")

        validate_allowed_keys(msg_dict, ['type', 'peers'], 'peers')

        if len(msg_dict['peers']) > 30:
            raise ErrorInvalidFormat('Too many peers in peers msg')

        for p in peers:
            if not isinstance(p, str):
                raise ErrorInvalidFormat("Message malformed: peer is not a string!")
            validate_peer_str(p)

    except ErrorInvalidFormat as e:
        raise e
    except Exception as e:
        raise ErrorInvalidFormat("Message malformed: {}".format(str(e)))


def validate_getpeers_msg(msg_dict):
    if msg_dict['type'] != 'getpeers':
        raise ErrorInvalidFormat("Message type is not 'getpeers'!")
    validate_allowed_keys(msg_dict, ['type'], 'getpeers')


def validate_getchaintip_msg(msg_dict):
    if len(msg_dict) != 1:
        raise ErrorInvalidFormat("Invalid getchaintip message")


def validate_getmempool_msg(msg_dict):
    if msg_dict['type'] != 'getmempool':
        raise ErrorInvalidFormat("Invalid type")
    validate_allowed_keys(msg_dict, ['type'], 'getmempool')


def validate_mempool_msg(msg_dict):
    if msg_dict['type'] != 'mempool':
        raise ErrorInvalidFormat("Invalid type")
    if 'txids' not in msg_dict:
        raise ErrorInvalidFormat("txids missing")
    if not isinstance(msg_dict['txids'], list):
        raise ErrorInvalidFormat("txids must be a list")
    for txid in msg_dict['txids']:
        if not objects.validate_objectid(txid):
            raise ErrorInvalidFormat("Invalid txid format")
    validate_allowed_keys(msg_dict, ['type', 'txids'], 'mempool')


def validate_error_msg(msg_dict):
    if msg_dict['type'] != 'error':
        raise ErrorInvalidFormat("Message type is not 'error'!")

    try:
        if 'msg' not in msg_dict:
            raise ErrorInvalidFormat("Message malformed: msg is missing!")
        if not isinstance(msg_dict['msg'], str):
            raise ErrorInvalidFormat("Message malformed: msg is not a string!")
        if 'name' not in msg_dict:
            raise ErrorInvalidFormat("Message malformed: name is missing!")
        if not isinstance(msg_dict['name'], str):
            raise ErrorInvalidFormat("Message malformed: name is not a string!")
        validate_allowed_keys(msg_dict, ['type', 'msg', 'name'], 'error')
    except ErrorInvalidFormat as e:
        raise e
    except Exception as e:
        raise ErrorInvalidFormat("Message malformed: {}".format(str(e)))


def validate_ihaveobject_msg(msg_dict):
    if msg_dict['type'] != 'ihaveobject':
        raise ErrorInvalidFormat("Message type is not 'ihaveobject'!")

    try:
        if 'objectid' not in msg_dict:
            raise ErrorInvalidFormat("Message malformed: objectid is missing!")
        if not isinstance(msg_dict['objectid'], str):
            raise ErrorInvalidFormat("Message malformed: objectid is not a string!")
        if not objects.validate_objectid(msg_dict['objectid']):
            raise ErrorInvalidFormat("Message malformed: objectid invalid!")
        validate_allowed_keys(msg_dict, ['type', 'objectid'], 'ihaveobject')
    except ErrorInvalidFormat as e:
        raise e
    except Exception as e:
        raise ErrorInvalidFormat("Message malformed: {}".format(str(e)))


def validate_getobject_msg(msg_dict):
    if msg_dict['type'] != 'getobject':
        raise ErrorInvalidFormat("Message type is not 'getobject'!")

    try:
        if 'objectid' not in msg_dict:
            raise ErrorInvalidFormat("Message malformed: objectid is missing!")
        if not isinstance(msg_dict['objectid'], str):
            raise ErrorInvalidFormat("Message malformed: objectid is not a string!")
        if not objects.validate_objectid(msg_dict['objectid']):
            raise ErrorInvalidFormat("Message malformed: objectid invalid!")
        validate_allowed_keys(msg_dict, ['type', 'objectid'], 'getobject')
    except ErrorInvalidFormat as e:
        raise e
    except Exception as e:
        raise ErrorInvalidFormat("Message malformed: {}".format(str(e)))


def validate_object_msg(msg_dict):
    if msg_dict['type'] != 'object':
        raise ErrorInvalidFormat("Message type is not 'object'!")

    try:
        if 'object' not in msg_dict:
            raise ErrorInvalidFormat("Message malformed: object is missing!")
        validate_allowed_keys(msg_dict, ['type', 'object'], 'object')
        obj = msg_dict['object']
        objects.validate_object(obj)
    except FaultyNodeException as e:
        raise e
    except NonfaultyNodeException as e:
        raise e
    except Exception as e:
        raise ErrorInvalidFormat("Message malformed: {}".format(str(e)))


def validate_chaintip_msg(msg_dict):
    if len(msg_dict) != 2:
        raise ErrorInvalidFormat("More than two keys set")
    if "blockid" not in msg_dict:
        raise ErrorInvalidFormat("blockid not set")
    if not isinstance(msg_dict["blockid"], str):
        raise ErrorInvalidFormat("blockid not a string")
    if not objects.validate_objectid(msg_dict["blockid"]):
        raise ErrorInvalidFormat("Invalid format of blockid")

    if int(msg_dict["blockid"], 16) >= int(const.BLOCK_TARGET, 16):
        raise ErrorInvalidBlockPOW(f"Proposed chaintip does not satisfy proof-of-work equation (has an objectid of {msg_dict['blockid']})!")


def validate_msg(msg_dict):
    msg_type = msg_dict['type']
    if msg_type == 'hello':
        validate_hello_msg(msg_dict)
    elif msg_type == 'getpeers':
        validate_getpeers_msg(msg_dict)
    elif msg_type == 'peers':
        validate_peers_msg(msg_dict)
    elif msg_type == 'getchaintip':
        validate_getchaintip_msg(msg_dict)
    elif msg_type == 'getmempool':
        validate_getmempool_msg(msg_dict)
    elif msg_type == 'error':
        validate_error_msg(msg_dict)
    elif msg_type == 'ihaveobject':
        validate_ihaveobject_msg(msg_dict)
    elif msg_type == 'getobject':
        validate_getobject_msg(msg_dict)
    elif msg_type == 'object':
        validate_object_msg(msg_dict)
    elif msg_type == 'chaintip':
        validate_chaintip_msg(msg_dict)
    elif msg_type == 'mempool':
        validate_mempool_msg(msg_dict)
    else:
        raise ErrorInvalidFormat("Message type {} not valid!".format(msg_type))


def gather_previous_txs(db_cur, tx_dict):
    if 'height' in tx_dict:
        return {}

    prev_txs = {}
    for i in tx_dict['inputs']:
        ptxid = i['outpoint']['txid']
        res = db_cur.execute("SELECT obj FROM objects WHERE oid = ?", (ptxid,))
        first_res = res.fetchone()
        if first_res is not None:
            ptx_str = first_res[0]
            ptx_dict = objects.expand_object(ptx_str)
            if ptx_dict['type'] != 'transaction':
                raise ErrorInvalidFormat("Transaction attempts to spend from a block")
            prev_txs[ptxid] = ptx_dict
    return prev_txs


def handle_peers_msg(msg_dict, peers_set, add_peer_fn):
    for p in msg_dict['peers']:
        try:
            peer_parts = p.rsplit(':', 1)
            host_str, port_str = peer_parts
            port = int(port_str, 10)
            peer = Peer(host_str, port)
            add_peer_fn(peer)
        except Exception:
            pass
    peers_set.save()


def handle_error_msg(msg_dict, peer_self):
    print("{}: Received error of type {}: {}".format(peer_self, msg_dict['name'], msg_dict['msg']))


async def handle_ihaveobject_msg(msg_dict, writer):
    objid = msg_dict['objectid']
    con = sqlite3.connect(const.DB_NAME)
    try:
        cur = con.cursor()
        res = cur.execute("SELECT obj FROM objects WHERE oid = ?", (objid,))
        if not res.fetchone() is None:
            return
    finally:
        con.close()
    await write_msg(writer, mk_getobject_msg(objid))


async def handle_getobject_msg(msg_dict, writer):
    objid = msg_dict['objectid']
    obj_tuple = None
    con = sqlite3.connect(const.DB_NAME)
    try:
        cur = con.cursor()
        res = cur.execute("SELECT obj FROM objects WHERE oid = ?", (objid,))
        obj_tuple = res.fetchone()
        if obj_tuple is None:
            await write_msg(writer, mk_error_msg(f"Object {objid} not known", "UNKNOWN_OBJECT"))
            return
    finally:
        con.close()
    obj_dict = objects.expand_object(obj_tuple[0])
    await write_msg(writer, mk_object_msg(obj_dict))


async def handle_getchaintip_msg(msg_dict, writer, chaintip):
    await write_msg(writer, mk_chaintip_msg(chaintip))


async def handle_getmempool_msg(msg_dict, writer, mempool):
    txids = mempool.get_txids()
    await write_msg(writer, mk_mempool_msg(txids))


async def handle_chaintip_msg(msg_dict):
    objectid = msg_dict['blockid']
    obj = objects.get_object(objectid)
    if obj is None:
        return mk_getobject_msg(objectid)
    if obj['type'] != 'block':
        raise ErrorInvalidFormat(f"Proposed chaintip {objectid} is not a block")
    return None


async def handle_mempool_msg(msg_dict, mempool):
    con = sqlite3.connect(const.DB_NAME)
    try:
        cur = con.cursor()
        results = []
        for txid in msg_dict['txids']:
            res = cur.execute("SELECT obj FROM objects WHERE oid = ?", (txid,))
            row = res.fetchone()
            if row is None:
                results.append(mk_getobject_msg(txid))
            else:
                tx_dict = objects.expand_object(row[0])
                if tx_dict['type'] == 'transaction' and 'height' not in tx_dict:
                    if mempool.try_add_tx(tx_dict):
                        print(f"Added known tx {txid[:8]} to mempool via mempool msg")
        return results
    finally:
        con.close()
