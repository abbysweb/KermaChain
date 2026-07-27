from __future__ import annotations
import copy
import re
import time
from datetime import datetime, timezone
from typing import Optional

from kerma.crypto.hashing import get_objid
from kerma.crypto.jcs import canonicalize
from kerma.network.exceptions import (
    ErrorInvalidFormat, ErrorInvalidBlockPOW, ErrorInvalidBlockTimestamp,
    ErrorInvalidGenesis, ErrorInvalidBlockCoinbase,
)

OBJECTID_RE = re.compile(r"^[0-9a-f]{64}$")


def validate_objectid(objid: str) -> bool:
    return isinstance(objid, str) and bool(OBJECTID_RE.match(objid))


class Block:
    def __init__(self, data: dict):
        self.data = data
        self.id: Optional[str] = None

    def validate_format(self, block_target: str, genesis_block_id: str) -> None:
        d = self.data
        if not isinstance(d, dict):
            raise ErrorInvalidFormat("Block not a dictionary")
        if d.get("type") != "block":
            raise ErrorInvalidFormat("Block type not 'block'")

        self.id = get_objid(d)
        if int(self.id, 16) >= int(block_target, 16):
            raise ErrorInvalidBlockPOW(f"Block PoW invalid (id={self.id})")

        if "txids" not in d or not isinstance(d["txids"], list):
            raise ErrorInvalidFormat("txids missing or not a list")
        if not all(validate_objectid(t) for t in d["txids"]):
            raise ErrorInvalidFormat("txids contain invalid id")

        if "nonce" not in d or not isinstance(d["nonce"], str):
            raise ErrorInvalidFormat("nonce missing or not a string")
        if not validate_objectid(d["nonce"][:64].ljust(64, "0")):
            pass  # nonce format is flexible

        if "previd" not in d:
            raise ErrorInvalidFormat("previd missing")
        if d["previd"] is None:
            if self.id != genesis_block_id:
                raise ErrorInvalidGenesis("null previd but not genesis")
        elif not validate_objectid(d["previd"]):
            raise ErrorInvalidFormat("previd invalid format")

        if "created" not in d or not isinstance(d["created"], int):
            raise ErrorInvalidFormat("created missing or not int")
        if d["created"] < 0:
            raise ErrorInvalidFormat("negative timestamp")
        if d["created"] > time.time():
            raise ErrorInvalidBlockTimestamp("block in the future")

        if "T" not in d or not isinstance(d["T"], str):
            raise ErrorInvalidFormat("T missing")

        allowed = {"type", "txids", "nonce", "previd", "created", "T", "miner", "note"}
        if set(d.keys()) - allowed:
            raise ErrorInvalidFormat("unexpected keys in block")

    def validate_chaintip(self, block_target: str, blockid: str) -> None:
        if int(blockid, 16) >= int(block_target, 16):
            raise ErrorInvalidBlockPOW(f"chaintip PoW invalid (id={blockid})")

    def get_height(self) -> Optional[int]:
        return self.data.get("height")

    @property
    def txids(self) -> list[str]:
        return self.data.get("txids", [])

    @property
    def previd(self) -> Optional[str]:
        return self.data.get("previd")

    @property
    def created(self) -> int:
        return self.data.get("created", 0)

    def __repr__(self) -> str:
        return f"Block(height={self.get_height()}, id={self.id})"
