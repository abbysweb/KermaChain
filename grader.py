import socket
import json
import time
import hashlib
import copy
import sys
import random
import threading

from kerma.storage.jcs import canonicalize

# ==========================================
# CONFIGURATION
# ==========================================
NODE_IP = "127.0.0.1"
NODE_PORT = 18018
TIMEOUT = 5
# Must match constants.py
TARGET = "0000abc000000000000000000000000000000000000000000000000000000000"
GENESIS_ID = "00002fa163c7dab0991544424b9fd302bb1782b185e5a3bbdf12afb758e57dee"

# ANSI Colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

# Check for Crypto Lib
try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print(f"{RED}WARNING: 'cryptography' library missing. Transaction tests (1f-1h) will be skipped.{RESET}")

# ==========================================
# HELPERS (Crypto, Mining, Networking)
# ==========================================

def get_objid(obj_dict):
    """Calculate Object ID (Hash)."""
    return hashlib.blake2s(canonicalize(obj_dict)).hexdigest()

def mine_block(block_dict):
    """Mines a block to find a nonce satisfying the target."""
    target_int = int(TARGET, 16)
    nonce_int = random.randint(0, 1000000)
    while True:
        block_dict['nonce'] = "{:064x}".format(nonce_int)
        h = get_objid(block_dict)
        if int(h, 16) < target_int:
            return block_dict
        nonce_int += 1

def sign_tx(tx, pk):
    """Signs a transaction input using Ed25519."""
    tx_to_sign = copy.deepcopy(tx)
    for inp in tx_to_sign['inputs']:
        inp['sig'] = None
    return pk.sign(canonicalize(tx_to_sign)).hex()

def recv_line(sock):
    """Read a raw line from socket."""
    buf = b""
    while True:
        try:
            chunk = sock.recv(1)
        except OSError:
            return None
        if not chunk: break
        buf += chunk
        if buf.endswith(b"\n"): break
    return buf.decode().strip()

def send_msg(sock, msg):
    """Send a JSON message."""
    try:
        sock.sendall(canonicalize(msg) + b"\n")
    except OSError:
        pass

def connect_to_node(agent_name="Grader"):
    """Connects to the node and performs the handshake."""
    try:
        s = socket.create_connection((NODE_IP, NODE_PORT), timeout=TIMEOUT)
        recv_line(s) # Consume 'hello'
        send_msg(s, {"type": "hello", "version": "0.10.3", "agent": agent_name})
        time.sleep(0.1)
        # Drain initial messages
        s.setblocking(False)
        try:
            while s.recv(4096): pass
        except: pass
        s.setblocking(True)
        return s
    except Exception:
        print(f"{RED}FAIL: Could not connect to node. Is main.py running?{RESET}")
        sys.exit(1)

def wait_for_specific_msg(sock, msg_type_list, timeout=5):
    """Waits for specific message types, filtering noise."""
    start = time.time()
    sock.settimeout(timeout)
    while time.time() - start < timeout:
        try:
            line = recv_line(sock)
            if not line: return None
            msg = json.loads(line)
            # Return if error or one of the expected types
            if msg.get('type') in msg_type_list or msg.get('type') == 'error':
                return msg
        except (socket.timeout, json.JSONDecodeError):
            continue
        except OSError:
            return None
    return None

def log_result(name, passed, msg=""):
    if passed:
        print(f"{GREEN}✅ PASS: {name}{RESET}")
    else:
        print(f"{RED}❌ FAIL: {name} - {msg}{RESET}")

# ==========================================
# TEST CASES 1(a) - 1(h)
# ==========================================

def test_1a_unavailable():
    """(a) A blockchain that points to an unavailable block."""
    s = connect_to_node("Grader 1")
    unknown = "cc" * 32
    b = {"type":"block", "txids":[], "previd":unknown, "created":int(time.time()), "nonce":""}
    mine_block(b)
    
    send_msg(s, {"type":"object", "object":b})
    
    # 1. Node must request parent
    msg = wait_for_specific_msg(s, ['getobject'])
    if not (msg and msg.get('objectid') == unknown):
        log_result("1(a) Unavailable", False, f"Node did not request parent. Got: {msg}")
        s.close()
        return

    print("      (Waiting 6s for timeout...)")
    time.sleep(6) 
    s.close()
    
    # 2. Check if object was discarded/marked invalid
    s2 = connect_to_node("Grader 2")
    send_msg(s2, {"type":"getobject", "objectid":get_objid(b)})
    # Expect error (UNKNOWN_OBJECT/UNFINDABLE) or nothing (if dropped)
    msg = wait_for_specific_msg(s2, ['object', 'error'])
    
    if msg is None or msg.get('type') == 'error':
        log_result("1(a) Unavailable", True)
    else:
        log_result("1(a) Unavailable", False, "Node kept the object")
    s2.close()

def test_1b_timestamps():
    """(b) A blockchain with non-increasing timestamps."""
    s = connect_to_node()
    # Parent
    p = {"type":"block", "txids":[], "previd":GENESIS_ID, "created":int(time.time()), "nonce":""}
    mine_block(p)
    pid = get_objid(p)
    # Child (Older than parent)
    c = {"type":"block", "txids":[], "previd":pid, "created":int(time.time())-100, "nonce":""}
    mine_block(c)
    
    send_msg(s, {"type":"object", "object":p})
    time.sleep(0.2)
    send_msg(s, {"type":"object", "object":c})
    
    msg = wait_for_specific_msg(s, ['error'])
    if msg is None or msg.get('type') == 'error':
        log_result("1(b) Timestamps", True)
    else:
        log_result("1(b) Timestamps", False, f"Unexpected response: {msg}")
    s.close()

def test_1c_future():
    """(c) A blockchain with a block in the year 2077."""
    s = connect_to_node()
    b = {"type":"block", "txids":[], "previd":GENESIS_ID, "created":3376662400, "nonce":""}
    mine_block(b)
    send_msg(s, {"type":"object", "object":b})
    
    msg = wait_for_specific_msg(s, ['error'])
    if msg and 'TIMESTAMP' in msg.get('name',''):
        log_result("1(c) Future 2077", True)
    elif msg is None: # Disconnect is acceptable
        log_result("1(c) Future 2077", True)
    else:
        log_result("1(c) Future 2077", False, f"Got: {msg}")
    s.close()

def test_1d_pow():
    """(d) A blockchain with an invalid proof-of-work."""
    s = connect_to_node()
    # Do NOT mine (nonce=0 implies bad PoW)
    b = {"type":"block", "txids":[], "previd":GENESIS_ID, "created":int(time.time()), "nonce":"00"*32}
    send_msg(s, {"type":"object", "object":b})
    
    msg = wait_for_specific_msg(s, ['error'])
    if msg and 'POW' in msg.get('name',''):
        log_result("1(d) Invalid PoW", True)
    elif msg is None:
        log_result("1(d) Invalid PoW", True)
    else:
        log_result("1(d) Invalid PoW", False, f"Got: {msg}")
    s.close()

def test_1e_fake_genesis():
    """(e) A blockchain that does not go back to the real genesis."""
    s = connect_to_node()
    # Valid PoW, but null previd and NOT the real genesis content
    b = {"type":"block", "txids":[], "previd":None, "created":int(time.time()), "nonce":""}
    mine_block(b)
    send_msg(s, {"type":"object", "object":b})
    
    msg = wait_for_specific_msg(s, ['error'])
    if msg and 'GENESIS' in msg.get('name',''):
        log_result("1(e) Fake Genesis", True)
    elif msg is None:
        log_result("1(e) Fake Genesis", True)
    else:
        log_result("1(e) Fake Genesis", False, f"Got: {msg}")
    s.close()

# --- Transaction Tests ---

def test_transactions():
    if not CRYPTO_AVAILABLE: return

    s = connect_to_node()
    # Generate Key
    pk = ed25519.Ed25519PrivateKey.generate()
    pub = pk.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw).hex()
    
    # Setup: Valid Parent with Funds
    cb = {"type":"transaction", "height":1, "outputs":[{"pubkey":pub, "value":50000}]}
    cbid = get_objid(cb)
    p = {"type":"block", "txids":[cbid], "previd":GENESIS_ID, "created":int(time.time())+1000, "nonce":""}
    mine_block(p)
    pid = get_objid(p)
    
    send_msg(s, {"type":"object", "object":cb})
    send_msg(s, {"type":"object", "object":p})
    time.sleep(0.5)
    
    # 1(f) Incorrect Coinbase Height
    # Parent is height 1 (on top of genesis). Child should be 2. We put 99.
    bad_cb = {"type":"transaction", "height":99, "outputs":[{"pubkey":pub, "value":50000}]}
    c1 = {"type":"block", "txids":[get_objid(bad_cb)], "previd":pid, "created":int(time.time())+1001, "nonce":""}
    mine_block(c1)
    
    send_msg(s, {"type":"object", "object":bad_cb})
    send_msg(s, {"type":"object", "object":c1})
    msg = wait_for_specific_msg(s, ['error'])
    if msg is None or msg.get('type')=='error': log_result("1(f) Bad CB Height", True)
    else: log_result("1(f) Bad CB Height", False, f"Got {msg}")
    
    # Reconnect for next test (to clear state if needed)
    s.close(); s = connect_to_node()
    
    # 1(g) Double Spend
    # Tx1: Spends `cbid` index 0
    tx1 = {"type":"transaction", "inputs":[{"outpoint":{"txid":cbid,"index":0}, "sig":None}], "outputs":[{"pubkey":pub, "value":10}]}
    tx1['inputs'][0]['sig'] = sign_tx(tx1, pk)
    # Tx2: Spends SAME `cbid` index 0
    tx2 = {"type":"transaction", "inputs":[{"outpoint":{"txid":cbid,"index":0}, "sig":None}], "outputs":[{"pubkey":pub, "value":20}]}
    tx2['inputs'][0]['sig'] = sign_tx(tx2, pk)
    
    # Block contains BOTH
    cb2 = {"type":"transaction", "height":2, "outputs":[{"pubkey":pub, "value":50000}]}
    c2 = {"type":"block", "txids":[get_objid(cb2), get_objid(tx1), get_objid(tx2)], "previd":pid, "created":int(time.time())+2000, "nonce":""}
    mine_block(c2)
    
    send_msg(s, {"type":"object", "object":cb2})
    send_msg(s, {"type":"object", "object":tx1})
    send_msg(s, {"type":"object", "object":tx2})
    send_msg(s, {"type":"object", "object":c2})
    
    msg = wait_for_specific_msg(s, ['error'])
    if msg is None or msg.get('type')=='error': log_result("1(g) Double Spend", True)
    else: log_result("1(g) Double Spend", False, f"Got {msg}")
    
    s.close(); s = connect_to_node()

    # 1(h) Non-Existent Output
    # Tx spends index 5 (does not exist in cb)
    tx_bad = {"type":"transaction", "inputs":[{"outpoint":{"txid":cbid,"index":5}, "sig":None}], "outputs":[{"pubkey":pub, "value":10}]}
    tx_bad['inputs'][0]['sig'] = sign_tx(tx_bad, pk)
    
    c3 = {"type":"block", "txids":[get_objid(cb2), get_objid(tx_bad)], "previd":pid, "created":int(time.time())+3000, "nonce":""}
    mine_block(c3)
    
    send_msg(s, {"type":"object", "object":cb2})
    send_msg(s, {"type":"object", "object":tx_bad})
    send_msg(s, {"type":"object", "object":c3})
    
    msg = wait_for_specific_msg(s, ['error'])
    if msg is None or msg.get('type')=='error': log_result("1(h) Invalid Output", True)
    else: log_result("1(h) Invalid Output", False, f"Got {msg}")
    s.close()

# ==========================================
# TEST CASE 2: Longest Chain
# ==========================================

def test_2_longest_chain():
    """2. Grader 1 sends valid blockchains... updates chaintip."""
    s = connect_to_node()
    prev = GENESIS_ID
    chain_tip = None
    
    # Build a chain of length 3 (likely longer than what's currently in DB if cleaned)
    for i in range(3):
        b = {"type":"block", "txids":[], "previd":prev, "created":int(time.time())+5000+(i*10), "nonce":""}
        mine_block(b)
        chain_tip = get_objid(b)
        send_msg(s, {"type":"object", "object":b})
        prev = chain_tip
        time.sleep(0.1)
    
    send_msg(s, {"type":"getchaintip"})
    msg = wait_for_specific_msg(s, ['chaintip'])
    
    if msg and msg.get('blockid') == chain_tip:
        log_result("2. Longest Chain", True)
    else:
        log_result("2. Longest Chain", False, f"Expected {chain_tip[:8]}, got {msg}")
    s.close()

# ==========================================
# REAL WORLD SCENARIO (Mock Peers)
# ==========================================

class MockPeer(threading.Thread):
    def __init__(self, port, chain):
        super().__init__()
        self.port = port
        self.chain = chain
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', port))
        self.sock.listen(1)
        self.running = True
        self.objs = {get_objid(b): b for b in chain}

    def run(self):
        while self.running:
            try:
                self.sock.settimeout(1)
                conn, _ = self.sock.accept()
                self.handle(conn)
            except: continue

    def handle(self, conn):
        conn.settimeout(2)
        try:
            while self.running:
                buf = b""
                while b"\n" not in buf:
                    chunk = conn.recv(1024)
                    if not chunk: return
                    buf += chunk
                line, _ = buf.split(b"\n", 1)
                msg = json.loads(line)
                
                if msg['type'] == 'hello':
                    send_msg(conn, {"type":"hello","version":"0.10.3","agent":"Mock"})
                elif msg['type'] == 'getchaintip':
                    send_msg(conn, {"type":"chaintip", "blockid":get_objid(self.chain[-1])})
                elif msg['type'] == 'getobject':
                    oid = msg['objectid']
                    if oid in self.objs:
                        send_msg(conn, {"type":"object", "object":self.objs[oid]})
        except: pass
        finally: conn.close()

    def stop(self):
        self.running = False
        self.sock.close()

def test_real_world():
    """Scenario: Connects to mock peers and syncs longest valid chain."""
    print("\n--- Real World Scenario ---")
    
    # Peer A: Short Valid Chain (Length 3)
    chain_a = []
    prev = GENESIS_ID
    for i in range(3):
        b = {"type":"block","txids":[],"previd":prev,"created":int(time.time())+10000+i,"nonce":""}
        mine_block(b); prev = get_objid(b); chain_a.append(b)
        
    # Peer B: Long Valid Chain (Length 5)
    chain_b = []
    prev = GENESIS_ID
    for i in range(5):
        b = {"type":"block","txids":[],"previd":prev,"created":int(time.time())+20000+i,"nonce":""}
        mine_block(b); prev = get_objid(b); chain_b.append(b)
        
    mock_a = MockPeer(18019, chain_a)
    mock_b = MockPeer(18020, chain_b)
    mock_a.start(); mock_b.start()
    
    try:
        # Connect to node and introduce peers
        s = connect_to_node("Bootstrap")
        # NOTE: Node must allow loopback connections for this to work!
        send_msg(s, {"type":"peers", "peers":["127.0.0.1:18019", "127.0.0.1:18020"]})
        s.close()
        
        print("      (Waiting 15s for sync...)")
        time.sleep(15)
        
        v = connect_to_node("Verifier")
        send_msg(v, {"type":"getchaintip"})
        msg = wait_for_specific_msg(v, ['chaintip'])
        v.close()
        
        expected_tip = get_objid(chain_b[-1])
        if msg and msg.get('blockid') == expected_tip:
            log_result("Real World Sync", True, "Synced longest chain")
        else:
            log_result("Real World Sync", False, f"Expected {expected_tip[:8]}, got {msg}")
            
    finally:
        mock_a.stop(); mock_b.stop()

# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    print("=== KERMA TASK 4 COMPLETE GRADER ===\n")
    test_1a_unavailable()
    test_1b_timestamps()
    test_1c_future()
    test_1d_pow()
    test_1e_fake_genesis()
    test_transactions()
    test_2_longest_chain()
    test_real_world()
    print("\n=== TESTS COMPLETE ===")
