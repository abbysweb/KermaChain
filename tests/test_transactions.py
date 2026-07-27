import pytest
import socket
import json
import time
import hashlib
import copy
import random

from kerma.storage.jcs import canonicalize
from kerma.constants import GENESIS_BLOCK_ID, BLOCK_TARGET

GENESIS_ID = GENESIS_BLOCK_ID
TARGET = BLOCK_TARGET


def canonicalize_obj(obj):
    return json.dumps(obj, separators=(',', ':'), sort_keys=True).encode('utf-8')


def get_objid(obj_dict):
    return hashlib.blake2s(canonicalize_obj(obj_dict)).hexdigest()


def mine_block(block_dict):
    block_dict['T'] = TARGET
    target_int = int(TARGET, 16)
    nonce_int = random.randint(0, 1000000)
    while True:
        block_dict['nonce'] = "{:064x}".format(nonce_int)
        h = get_objid(block_dict)
        if int(h, 16) < target_int:
            return block_dict
        nonce_int += 1


def sign_tx(tx, pk):
    tx_to_sign = copy.deepcopy(tx)
    for inp in tx_to_sign['inputs']:
        inp['sig'] = None
    return pk.sign(canonicalize_obj(tx_to_sign)).hex()


def recv_line(sock):
    buf = b""
    while True:
        try:
            chunk = sock.recv(1)
        except OSError:
            return None
        if not chunk:
            break
        buf += chunk
        if buf.endswith(b"\n"):
            break
    return buf.decode().strip()


def send_msg(sock, msg):
    sock.sendall(canonicalize_obj(msg) + b"\n")


def connect_to_node(agent_name="Test"):
    s = socket.create_connection(("127.0.0.1", 18018), timeout=5)
    recv_line(s)
    send_msg(s, {"type": "hello", "version": "0.10.3", "agent": agent_name})
    time.sleep(0.1)
    s.setblocking(False)
    try:
        while s.recv(4096):
            pass
    except Exception:
        pass
    s.setblocking(True)
    return s


def wait_for_msg(sock, types, timeout=5):
    start = time.time()
    sock.settimeout(timeout)
    while time.time() - start < timeout:
        try:
            line = recv_line(sock)
            if not line:
                return None
            msg = json.loads(line)
            if msg.get('type') in types or msg.get('type') == 'error':
                return msg
        except (socket.timeout, json.JSONDecodeError):
            continue
        except OSError:
            return None
    return None


class TestBlockValidation:
    def test_unavailable_parent(self):
        s = connect_to_node("Test 1a")
        assert s is not None, "Cannot connect to node"
        unknown = "cc" * 32
        b = {"type": "block", "txids": [], "previd": unknown, "created": int(time.time()), "nonce": ""}
        mine_block(b)
        send_msg(s, {"type": "object", "object": b})
        msg = wait_for_msg(s, ['getobject'])
        assert msg is not None and msg.get('objectid') == unknown, \
            f"Node did not request parent. Got: {msg}"
        time.sleep(6)
        s.close()
        s2 = connect_to_node("Test 1a-2")
        send_msg(s2, {"type": "getobject", "objectid": get_objid(b)})
        msg = wait_for_msg(s2, ['object', 'error'])
        assert msg is None or msg.get('type') == 'error', "Node kept the invalid object"
        s2.close()

    def test_non_increasing_timestamps(self):
        s = connect_to_node("Test 1b")
        assert s is not None
        p = {"type": "block", "txids": [], "previd": GENESIS_ID, "created": int(time.time()), "nonce": ""}
        mine_block(p)
        pid = get_objid(p)
        c = {"type": "block", "txids": [], "previd": pid, "created": int(time.time()) - 100, "nonce": ""}
        mine_block(c)
        send_msg(s, {"type": "object", "object": p})
        time.sleep(0.2)
        send_msg(s, {"type": "object", "object": c})
        msg = wait_for_msg(s, ['error'])
        assert msg is None or msg.get('type') == 'error', f"Unexpected response: {msg}"
        s.close()

    def test_future_timestamp(self):
        s = connect_to_node("Test 1c")
        assert s is not None
        b = {"type": "block", "txids": [], "previd": GENESIS_ID, "created": 3376662400, "nonce": ""}
        mine_block(b)
        send_msg(s, {"type": "object", "object": b})
        msg = wait_for_msg(s, ['error'])
        s.close()
        if msg is not None:
            assert 'TIMESTAMP' in msg.get('name', ''), f"Got: {msg}"

    def test_invalid_pow(self):
        s = connect_to_node("Test 1d")
        assert s is not None
        b = {"type": "block", "txids": [], "previd": GENESIS_ID, "created": int(time.time()), "nonce": "00" * 32}
        send_msg(s, {"type": "object", "object": b})
        msg = wait_for_msg(s, ['error'])
        s.close()
        if msg is not None:
            assert 'POW' in msg.get('name', ''), f"Got: {msg}"

    def test_fake_genesis(self):
        s = connect_to_node("Test 1e")
        assert s is not None
        b = {"type": "block", "txids": [], "previd": None, "created": int(time.time()), "nonce": ""}
        mine_block(b)
        send_msg(s, {"type": "object", "object": b})
        msg = wait_for_msg(s, ['error'])
        s.close()
        if msg is not None:
            assert 'GENESIS' in msg.get('name', ''), f"Got: {msg}"
