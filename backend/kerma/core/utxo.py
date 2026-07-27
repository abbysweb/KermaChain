from __future__ import annotations
import copy
from typing import Optional


class UTXOSet:
    def __init__(self, utxo: Optional[dict] = None):
        self.utxo: dict = utxo if utxo is not None else {}

    def copy(self) -> UTXOSet:
        return UTXOSet(copy.deepcopy(self.utxo))

    def get(self, txid: str, index: str) -> Optional[int]:
        return self.utxo.get(txid, {}).get(index)

    def to_dict(self) -> dict:
        return self.utxo

    @classmethod
    def from_dict(cls, data: dict) -> UTXOSet:
        return cls(data)

    def __repr__(self) -> str:
        total = sum(v for sub in self.utxo.values() for v in sub.values())
        return f"UTXOSet(entries={len(self.utxo)}, total_value={total})"
