#!/usr/bin/env python3
"""
Simple CPU Miner for KermaChain

Usage:
    python scripts/miner.py <miner_pubkey_hex>

Example:
    # Generate keypair first:
    python -c "from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey; k=Ed25519PrivateKey.generate(); print('pub:', k.public_key().public_bytes_raw().hex()); print('priv:', k.private_bytes_raw().hex())"
    
    # Then mine:
    python scripts/miner.py <pubkey_hex>
"""

import sys
import time
import json
import hashlib
import requests

# Add both root and backend to path
sys.path.insert(0, '.')
sys.path.insert(0, 'backend')
from kerma.crypto.jcs import canonicalize
from kerma.crypto.hashing import get_objid

# Constants from kerma/constants.py
TARGET = "0000abc000000000000000000000000000000000000000000000000000000000"
TARGET_INT = int(TARGET, 16)
BLOCK_REWARD = 50_000_000_000_000
API_BASE = "http://localhost:3001"

def fetch_json(path):
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"API error {path}: {e}")
        return None

def get_chaintip():
    stats = fetch_json("/api/stats")
    return stats["tipId"] if stats else None

def get_tip_height():
    stats = fetch_json("/api/stats")
    return stats["height"] if stats else 0

def get_mempool_txids():
    mempool = fetch_json("/api/mempool")
    return [tx["txid"] for tx in mempool] if mempool else []

def build_block(miner_pubkey, prev_block_id, txids, height):
    # Coinbase transaction
    coinbase = {
        "type": "transaction",
        "height": height,
        "outputs": [{"pubkey": miner_pubkey, "value": BLOCK_REWARD}]
    }
    coinbase_id = get_objid(coinbase)
    
    block = {
        "type": "block",
        "txids": [coinbase_id] + txids,
        "previd": prev_block_id,
        "created": int(time.time()),
        "T": TARGET,
        "miner": "SimpleMiner",
        "nonce": "0" * 64
    }
    return block, coinbase

def mine_block(block, max_nonce=None):
    """CPU mine until valid nonce found. Returns (block, block_id) or (None, None)."""
    nonce = 0
    start = time.time()
    
    while max_nonce is None or nonce < max_nonce:
        block["nonce"] = f"{nonce:064x}"
        block_id = get_objid(block)
        
        if int(block_id, 16) < TARGET_INT:
            elapsed = time.time() - start
            hashrate = nonce / elapsed if elapsed > 0 else 0
            print(f"\n✓ Block found! nonce={nonce:,} hashrate={hashrate:,.0f} H/s")
            print(f"  Block ID: {block_id}")
            return block, block_id
        
        nonce += 1
        
        # Progress indicator
        if nonce % 100000 == 0:
            elapsed = time.time() - start
            hashrate = nonce / elapsed if elapsed > 0 else 0
            print(f"\r  tried {nonce:,} nonces ({hashrate:,.0f} H/s)", end="", flush=True)
    
    return None, None

def print_block_summary(block, block_id, coinbase):
    print("\n" + "="*60)
    print("MINED BLOCK SUMMARY")
    print("="*60)
    print(f"Block ID:   {block_id}")
    print(f"Height:     {coinbase['height']}")
    print(f"Previous:   {block['previd'][:16]}...")
    print(f"Timestamp:  {block['created']} ({time.ctime(block['created'])})")
    print(f"Tx count:   {len(block['txids'])} (1 coinbase + {len(block['txids'])-1} from mempool)")
    print(f"Miner:      {block['miner']}")
    print(f"Nonce:      {block['nonce'][:16]}...")
    print(f"Target:     {block['T']}")
    print("="*60)
    print("\nTo submit via P2P, you would:")
    print("  1. Connect to a peer on port 18018")
    print("  2. Send 'hello' handshake")
    print("  3. Send 'ihaveobject' with block ID")
    print("  4. Wait for 'getobject' request")
    print("  5. Send full 'object' message")
    print("\nFull block JSON:")
    print(json.dumps(block, indent=2))

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    miner_pubkey = sys.argv[1].strip()
    
    # Validate pubkey format
    if len(miner_pubkey) != 64 or not all(c in "0123456789abcdef" for c in miner_pubkey.lower()):
        print("Error: pubkey must be 64 hex characters")
        sys.exit(1)
    
    print(f"🔨 Simple Miner starting...")
    print(f"   Miner pubkey: {miner_pubkey[:16]}...")
    print(f"   API:          {API_BASE}")
    print(f"   Target:       {TARGET}")
    print()
    
    # Check API connectivity
    stats = fetch_json("/api/health")
    if not stats:
        print("❌ Cannot reach API server. Is backend running on :3001?")
        sys.exit(1)
    print(f"✓ API healthy: {stats}")
    
    try:
        while True:
            tip_id = get_chaintip()
            tip_height = get_tip_height()
            txids = get_mempool_txids()
            
            print(f"\n📦 Tip: {tip_id[:16]}... (height {tip_height}) | Mempool: {len(txids)} txs")
            
            block, coinbase = build_block(miner_pubkey, tip_id, txids, tip_height + 1)
            mined_block, block_id = mine_block(block)
            
            if mined_block:
                print_block_summary(mined_block, block_id, coinbase)
                
                # Wait a bit before next round
                print("\n⏳ Waiting 5s before next mining round...")
                time.sleep(5)
            else:
                print("Mining interrupted or max nonce reached")
                break
                
    except KeyboardInterrupt:
        print("\n\n👋 Miner stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()