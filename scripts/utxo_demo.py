#!/usr/bin/env python3
"""
UTXO Visual Example - Interactive demonstration of UTXO model

Run: python scripts/utxo_demo.py
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import copy

@dataclass
class UTXO:
    txid: str
    index: int
    value: int
    pubkey: str
    spent: bool = False
    
    @property
    def key(self):
        return f"{self.txid}#{self.index}"

@dataclass
class Transaction:
    txid: str
    inputs: List[Dict]  # [{"txid": "...", "index": 0, "sig": "..."}]
    outputs: List[Dict]  # [{"pubkey": "...", "value": 1000}]
    is_coinbase: bool = False
    height: Optional[int] = None

class UTXOSet:
    def __init__(self):
        self.utxos: Dict[str, UTXO] = {}
    
    def add_output(self, txid: str, index: int, value: int, pubkey: str):
        self.utxos[f"{txid}#{index}"] = UTXO(txid, index, value, pubkey)
    
    def spend(self, txid: str, index: int) -> Optional[UTXO]:
        key = f"{txid}#{index}"
        if key in self.utxos and not self.utxos[key].spent:
            self.utxos[key].spent = True
            return self.utxos[key]
        return None
    
    def get_unspent(self) -> List[UTXO]:
        return [u for u in self.utxos.values() if not u.spent]
    
    def total_value(self) -> int:
        return sum(u.value for u in self.get_unspent())
    
    def print_state(self, title: str):
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        unspent = self.get_unspent()
        if not unspent:
            print("  (empty)")
        else:
            for u in unspent:
                status = "🟢 UNSPENT" if not u.spent else "🔴 SPENT"
                print(f"  {u.key:20s} | {u.value:>15,} sat | {u.pubkey[:16]}... | {status}")
        print(f"  Total: {self.total_value():,} sat = {self.total_value()/1e12:.2f} TMC")

def demo():
    print("\n" + "## UTXO MODEL DEMO - Step by Step".center(60))
    print("="*60)
    
    utxo_set = UTXOSet()
    tx_counter = 0
    
    def next_txid():
        nonlocal tx_counter
        tx_counter += 1
        return f"tx{tx_counter:03d}"
    
    # Genesis: empty UTXO set
    utxo_set.print_state("GENESIS (empty UTXO set)")
    input("Press Enter to continue...")
    
    # Block 1: Coinbase to Miner
    print("\n📦 BLOCK 1: Coinbase (Miner reward)")
    cb_txid = next_txid()
    miner_pubkey = "miner_pubkey_abcdef1234567890"
    utxo_set.add_output(cb_txid, 0, 50_000_000_000_000, miner_pubkey)
    utxo_set.print_state("AFTER BLOCK 1: Miner has 50 TMC")
    input("Press Enter...")
    
    # Block 2: Miner sends 20 TMC to Alice
    print("\n💸 BLOCK 2: Miner → Alice (20 TMC) + change")
    spend_txid = next_txid()
    # Spend the coinbase
    spent = utxo_set.spend(cb_txid, 0)
    print(f"  Spent: {cb_txid}#0 ({spent.value:,} sat)")
    # Create outputs
    alice_pubkey = "alice_pubkey_1234567890abcdef"
    utxo_set.add_output(spend_txid, 0, 20_000_000_000_000, alice_pubkey)
    utxo_set.add_output(spend_txid, 1, 30_000_000_000_000, miner_pubkey)  # change
    utxo_set.print_state("AFTER BLOCK 2: Alice 20 TMC, Miner 30 TMC change")
    input("Press Enter...")
    
    # Block 3: Alice sends 5 TMC to Bob
    print("\n💸 BLOCK 3: Alice → Bob (5 TMC) + change")
    alice_to_bob_txid = next_txid()
    bob_pubkey = "bob_pubkey_abcdef1234567890"
    spent = utxo_set.spend(spend_txid, 0)  # Alice's 20 TMC
    print(f"  Spent: {spend_txid}#0 ({spent.value:,} sat)")
    utxo_set.add_output(alice_to_bob_txid, 0, 5_000_000_000_000, bob_pubkey)
    utxo_set.add_output(alice_to_bob_txid, 1, 15_000_000_000_000, alice_pubkey)  # change
    utxo_set.print_state("AFTER BLOCK 3: Bob 5, Alice 15, Miner 30")
    input("Press Enter...")
    
    # Block 4: Miner sends 10 TMC to Carol (from change)
    print("\n💸 BLOCK 4: Miner → Carol (10 TMC) + change")
    miner_to_carol_txid = next_txid()
    carol_pubkey = "carol_pubkey_fedcba0987654321"
    spent = utxo_set.spend(spend_txid, 1)  # Miner's 30 TMC change
    print(f"  Spent: {spend_txid}#1 ({spent.value:,} sat)")
    utxo_set.add_output(miner_to_carol_txid, 0, 10_000_000_000_000, carol_pubkey)
    utxo_set.add_output(miner_to_carol_txid, 1, 20_000_000_000_000, miner_pubkey)  # change
    utxo_set.print_state("AFTER BLOCK 4: Carol 10, Miner 20, Alice 15, Bob 5")
    input("Press Enter...")
    
    # Demonstrate double-spend prevention
    print("\n🚫 DOUBLE-SPEND ATTEMPT: Try to spend Alice's 20 TMC again")
    print("  (Already spent in Block 3)")
    try:
        spent = utxo_set.spend(spend_txid, 0)  # Already spent!
        if spent:
            print("  ❌ ERROR: Double-spend succeeded (should not happen!)")
        else:
            print("  ✅ Correctly rejected: UTXO already spent")
    except:
        print("  ✅ Correctly rejected: UTXO already spent")
    
    utxo_set.print_state("FINAL STATE (unchanged)")
    
    # Summary
    print("\n" + "="*60)
    print("KEY TAKEAWAYS")
    print("="*60)
    print("""
1. UTXOs are discrete "bills" - not a running balance
2. Each UTXO can be spent ONCE (prevents double-spend)
3. Transactions CONSUME old UTXOs and CREATE new ones
4. Change outputs go back to sender
5. Coinbase creates NEW coins (no inputs)
6. Sum(inputs) >= Sum(outputs)  |  difference = miner fee
7. To find your balance: sum all UTXOs where pubkey == yours
""")

if __name__ == "__main__":
    demo()