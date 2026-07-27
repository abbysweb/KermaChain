from __future__ import annotations
import re
from typing import Optional

from kerma.crypto.hashing import get_objid
from kerma.crypto.signing import verify_signature
from kerma.network.exceptions import (
    ErrorInvalidFormat, ErrorInvalidTxSignature,
    ErrorInvalidTxConservation, ErrorInvalidTxOutpoint, NeedMoreObjects,
)

PUBKEY_RE = re.compile(r"^[0-9a-f]{64}$")
SIG_RE = re.compile(r"^[0-9a-f]{128}$")


def validate_pubkey(s: str) -> bool:
    return isinstance(s, str) and bool(PUBKEY_RE.match(s))


def validate_signature_str(s: str) -> bool:
    return isinstance(s, str) and bool(SIG_RE.match(s))


class Transaction:
    def __init__(self, data: dict):
        self.data = data
        self.id: Optional[str] = None

    @property
    def is_coinbase(self) -> bool:
        return "height" in self.data

    @property
    def height(self) -> Optional[int]:
        return self.data.get("height")

    @property
    def inputs(self) -> list:
        return self.data.get("inputs", [])

    @property
    def outputs(self) -> list:
        return self.data.get("outputs", [])

    def validate_format(self) -> None:
        d = self.data
        if not isinstance(d, dict) or d.get("type") != "transaction":
            raise ErrorInvalidFormat("Not a transaction")

        if "outputs" not in d or not isinstance(d["outputs"], list):
            raise ErrorInvalidFormat("outputs missing")
        for i, out in enumerate(d["outputs"]):
            if not isinstance(out, dict):
                raise ErrorInvalidFormat(f"output {i} not dict")
            if "pubkey" not in out or not validate_pubkey(out["pubkey"]):
                raise ErrorInvalidFormat(f"output {i} invalid pubkey")
            if "value" not in out or not isinstance(out["value"], int) or out["value"] < 0:
                raise ErrorInvalidFormat(f"output {i} invalid value")

        if self.is_coinbase:
            if not isinstance(d["height"], int) or d["height"] < 0:
                raise ErrorInvalidFormat("coinbase height invalid")
            if len(d["outputs"]) > 1:
                raise ErrorInvalidFormat("coinbase > 1 output")
            if set(d.keys()) - {"type", "height", "outputs"}:
                raise ErrorInvalidFormat("coinbase extra keys")
        else:
            if "inputs" not in d or not isinstance(d["inputs"], list):
                raise ErrorInvalidFormat("inputs missing")
            if len(d["inputs"]) == 0:
                raise ErrorInvalidFormat("no inputs")
            for i, inp in enumerate(d["inputs"]):
                if not isinstance(inp, dict):
                    raise ErrorInvalidFormat(f"input {i} not dict")
                if "sig" not in inp or not validate_signature_str(inp["sig"]):
                    raise ErrorInvalidFormat(f"input {i} invalid sig")
                op = inp.get("outpoint", {})
                if not isinstance(op, dict) or "txid" not in op or "index" not in op:
                    raise ErrorInvalidFormat(f"input {i} invalid outpoint")
            if set(d.keys()) - {"type", "inputs", "outputs"}:
                raise ErrorInvalidFormat("tx extra keys")

    def verify_inputs(self, prev_txs: dict) -> None:
        if self.is_coinbase:
            return
        txid = get_objid(self.data)
        missing = [inp["outpoint"]["txid"] for inp in self.inputs if inp["outpoint"]["txid"] not in prev_txs]
        if missing:
            raise NeedMoreObjects(f"tx {txid} needs objects {missing}", missing)

        insum = 0
        seen: dict = {}
        for inp in self.inputs:
            ptxid = inp["outpoint"]["txid"]
            pidx = inp["outpoint"]["index"]
            if ptxid in seen and pidx in seen[ptxid]:
                raise ErrorInvalidTxConservation("double input")
            seen.setdefault(ptxid, set()).add(pidx)
            ptx = prev_txs[ptxid]
            if ptx["type"] != "transaction":
                raise ErrorInvalidFormat("spending from block")
            if pidx >= len(ptx["outputs"]):
                raise ErrorInvalidTxOutpoint(f"invalid outpoint index {ptxid}:{pidx}")
            if not verify_signature(self.data, inp["sig"], ptx["outputs"][pidx]["pubkey"]):
                raise ErrorInvalidTxSignature(f"bad sig for {ptxid}:{pidx}")
            insum += ptx["outputs"][pidx]["value"]

        outsum = sum(o["value"] for o in self.outputs)
        if insum < outsum:
            raise ErrorInvalidTxConservation("inputs < outputs")

    def update_utxo(self, utxo: dict) -> int:
        txid = get_objid(self.data)
        invalue = 0
        for inp in self.inputs:
            itxid = inp["outpoint"]["txid"]
            idx = str(inp["outpoint"]["index"])
            if itxid not in utxo or idx not in utxo[itxid]:
                raise ErrorInvalidTxOutpoint(f"UTXO missing for {itxid}:{idx}")
            invalue += utxo[itxid][idx]
            del utxo[itxid][idx]
            if not utxo[itxid]:
                del utxo[itxid]
        for i, out in enumerate(self.outputs):
            utxo.setdefault(txid, {})[str(i)] = out["value"]
        return invalue - sum(o["value"] for o in self.outputs)

    def __repr__(self) -> str:
        return f"Transaction(id={get_objid(self.data)[:8]}..., coinbase={self.is_coinbase})"
