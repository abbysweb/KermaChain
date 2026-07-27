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
