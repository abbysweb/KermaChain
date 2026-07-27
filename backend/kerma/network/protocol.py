from __future__ import annotations
import re
import random
import ipaddress
import sqlite3
import json
from typing import Optional, TYPE_CHECKING

from kerma.crypto.hashing import get_objid
from kerma.crypto.jcs import canonicalize
from kerma.network.exceptions import *
from kerma.network.peer import Peer

if TYPE_CHECKING:
    from kerma.config import Config
    from kerma.storage.database import Database


class Protocol:
    def __init__(self, config: "Config", db: "Database"):
        self.config = config
        self.db = db

    def mk_hello_msg(self) -> dict:
        return {"type": "hello", "version": self.config.version, "agent": self.config.agent}

    def mk_getpeers_msg(self) -> dict:
        return {"type": "getpeers"}

    def mk_peers_msg(self, peers_set) -> dict:
        pl = [str(p) for p in peers_set]
        if len(pl) > 30:
            pl = random.sample(pl, 30)
        return {"type": "peers", "peers": pl}

    def mk_getobject_msg(self, objid: str) -> dict:
        return {"type": "getobject", "objectid": objid}

    def mk_object_msg(self, obj_dict: dict) -> dict:
        return {"type": "object", "object": obj_dict}

    def mk_ihaveobject_msg(self, objid: str) -> dict:
        return {"type": "ihaveobject", "objectid": objid}

    def mk_chaintip_msg(self, blockid: str) -> dict:
        return {"type": "chaintip", "blockid": blockid}

    def mk_mempool_msg(self, txids: list[str]) -> dict:
        return {"type": "mempool", "txids": txids}

    def mk_getchaintip_msg(self) -> dict:
        return {"type": "getchaintip"}

    def mk_getmempool_msg(self) -> dict:
        return {"type": "getmempool"}

    def mk_error_msg(self, error_str: str, error_name: str) -> dict:
        return {"type": "error", "name": error_name, "msg": error_str}

    async def write_msg(self, writer, msg_dict: dict) -> None:
        msg_bytes = canonicalize(msg_dict)
        writer.write(msg_bytes)
        writer.write(b"\n")
        await writer.drain()

    def parse_msg(self, msg_str: str) -> dict:
        try:
            msg = json.loads(msg_str)
        except Exception as e:
            raise ErrorInvalidFormat(f"JSON parse error: {e}")
        if not isinstance(msg, dict) or "type" not in msg:
            raise ErrorInvalidFormat("message not a dict or missing type")
        return msg

    def validate_hello(self, msg: dict) -> None:
        if msg.get("type") != "hello":
            raise ErrorInvalidHandshake("not hello")
        if "version" not in msg or not isinstance(msg["version"], str):
            raise ErrorInvalidFormat("version missing")
        if not re.compile(r"0\.10\.\d").fullmatch(msg["version"]):
            raise ErrorInvalidFormat("version invalid")
        if "agent" not in msg:
            raise ErrorInvalidFormat("agent missing")
        allowed = {"type", "version", "agent"}
        if set(msg.keys()) - allowed:
            raise ErrorInvalidFormat("extra keys in hello")

    def validate_msg(self, msg: dict) -> None:
        t = msg.get("type", "")
        if t in ("hello", "getpeers", "peers", "getchaintip", "getmempool", "mempool",
                  "error", "ihaveobject", "getobject", "object", "chaintip"):
            return
        raise ErrorInvalidFormat(f"unknown message type: {t}")

    def validate_peer_str(self, peer_str: str) -> None:
        parts = peer_str.rsplit(":", 1)
        if len(parts) != 2:
            raise ErrorInvalidFormat("no port")
        host_str, port_str = parts
        try:
            port = int(port_str, 10)
        except Exception:
            raise ErrorInvalidFormat("port not decimal")
        if port <= 0 or port > 65535:
            raise ErrorInvalidFormat("port out of range")
        hostname_re = re.compile(r"[a-zA-Z\d.\-_]{3,50}")
        ipv4_re = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
        if not hostname_re.fullmatch(host_str) and not ipv4_re.fullmatch(host_str):
            raise ErrorInvalidFormat("invalid host")

    def gather_previous_txs(self, db_cur, tx_dict: dict) -> dict:
        if "height" in tx_dict:
            return {}
        prev_txs = {}
        for inp in tx_dict.get("inputs", []):
            ptxid = inp["outpoint"]["txid"]
            res = db_cur.execute("SELECT obj FROM objects WHERE oid = ?", (ptxid,))
            row = res.fetchone()
            if row:
                ptx = json.loads(row[0])
                if ptx["type"] == "transaction":
                    prev_txs[ptxid] = ptx
        return prev_txs

    def handle_ihaveobject(self, msg: dict) -> Optional[str]:
        objid = msg.get("objectid")
        if objid and not self.db.object_exists(objid):
            return objid
        return None

    def handle_getobject(self, msg: dict) -> Optional[dict]:
        objid = msg.get("objectid")
        if not objid:
            return self.mk_error_msg("no objectid", "INVALID_FORMAT")
        obj = self.db.get_object(objid)
        if obj is None:
            return self.mk_error_msg(f"object {objid} not found", "UNKNOWN_OBJECT")
        return self.mk_object_msg(obj)

    def handle_peers_msg(self, msg: dict, add_peer_fn) -> None:
        for p in msg.get("peers", []):
            try:
                host, port_str = p.rsplit(":", 1)
                add_peer_fn(Peer(host, int(port_str)))
            except Exception:
                pass
