import socket
import json
import hashlib
import copy

from kerma.storage.jcs import canonicalize

GENESIS_ID = "00002fa163c7dab0991544424b9fd302bb1782b185e5a3bbdf12afb758e57dee"
TARGET = "0000abc000000000000000000000000000000000000000000000000000000000"
NODE_IP = "127.0.0.1"
NODE_PORT = 18018
TIMEOUT = 5


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
    try:
        sock.sendall(canonicalize_obj(msg) + b"\n")
    except OSError:
        pass


def connect_to_node(agent_name="KermaChain Test"):
    try:
        s = socket.create_connection((NODE_IP, NODE_PORT), timeout=TIMEOUT)
        recv_line(s)
        send_msg(s, {"type": "hello", "version": "0.10.3", "agent": agent_name})
        import time
        time.sleep(0.1)
        s.setblocking(False)
        try:
            while s.recv(4096):
                pass
        except Exception:
            pass
        s.setblocking(True)
        return s
    except Exception:
        print("FAIL: Could not connect to node. Is main.py running?")
        return None


def wait_for_specific_msg(sock, msg_type_list, timeout=5):
    import time
    start = time.time()
    sock.settimeout(timeout)
    while time.time() - start < timeout:
        try:
            line = recv_line(sock)
            if not line:
                return None
            msg = json.loads(line)
            if msg.get('type') in msg_type_list or msg.get('type') == 'error':
                return msg
        except (socket.timeout, json.JSONDecodeError):
            continue
        except OSError:
            return None
    return None
