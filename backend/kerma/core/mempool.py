from __future__ import annotations
import copy
import traceback
from typing import Optional

from kerma.crypto.hashing import get_objid
from kerma.storage.database import Database


class Mempool:
    def __init__(self, base_block_id: str, utxo: dict, db: Database):
        self.base_block_id = base_block_id
        self.utxo = utxo
        self.txs: list[dict] = []
        self.db = db

    def try_add_tx(self, tx: dict) -> bool:
        if "height" in tx:
            return False
        txid = get_objid(tx)
        current_ids = [get_objid(t) for t in self.txs]
        if txid in current_ids:
            return True
        try:
            temp_utxo = copy.deepcopy(self.utxo)
            from kerma.core.transaction import Transaction
            t = Transaction(tx)
            t.update_utxo(temp_utxo)
            self.utxo = temp_utxo
            self.txs.append(tx)
            return True
        except Exception:
            return False

    def rebase_to_block(self, new_tip: str) -> None:
        if self.base_block_id == new_tip:
            return
        try:
            tip_utxo = self.db.get_utxo(new_tip)
            if tip_utxo is None:
                return
            self.base_block_id = new_tip
            self.utxo = tip_utxo
            old_txs = self.txs
            self.txs = []
            new_chain_txids = set()
            chain = self.db.get_chain_path(new_tip)
            disconnect_ids, connect_ids = self._split_path(self.base_block_id, chain)
            for bid in connect_ids:
                block = self.db.get_object(bid)
                if block:
                    new_chain_txids.update(block.get("txids", []))
            to_readd = []
            for bid in reversed(disconnect_ids):
                block = self.db.get_object(bid)
                if block:
                    for tid in block.get("txids", []):
                        t = self.db.get_object(tid)
                        if t and "height" not in t:
                            to_readd.append(t)
            to_readd.extend(old_txs)
            for tx in to_readd:
                txid = get_objid(tx)
                if txid not in new_chain_txids:
                    self.try_add_tx(tx)
        except Exception as e:
            print(f"Mempool rebase error: {e}")

    def _split_path(self, old_tip: str, new_chain: list[str]):
        old_chain = self.db.get_chain_path(old_tip)
        min_len = min(len(old_chain), len(new_chain))
        split = 0
        while split < min_len and old_chain[split] == new_chain[split]:
            split += 1
        return list(reversed(old_chain[split:])), new_chain[split:]

    def get_txids(self) -> list[str]:
        return [get_objid(tx) for tx in self.txs]

    def get_entries(self) -> list[dict]:
        result = []
        for tx in self.txs:
            txid = get_objid(tx)
            inputs = tx.get("inputs", [])
            outputs = tx.get("outputs", [])
            total_value = sum(o.get("value", 0) for o in outputs)
            result.append({
                "txid": txid,
                "inputsCount": len(inputs),
                "outputsCount": len(outputs),
                "totalValue": total_value,
            })
        return result
