from __future__ import annotations
import sqlite3
import os
from typing import Optional

from kerma.crypto.hashing import get_objid
from kerma.crypto.jcs import canonicalize
from kerma.network.exceptions import ErrorInvalidGenesis


class Database:
    def __init__(self, db_name: str = "db.db"):
        self.db_name = db_name

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_name)

    def create_tables(self) -> None:
        con = self._connect()
        try:
            cur = con.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS objects(oid VARCHAR(64) PRIMARY KEY, obj TEXT NOT NULL)")
            cur.execute("CREATE TABLE IF NOT EXISTS utxo(blockid VARCHAR(64) PRIMARY KEY, utxoset TEXT NOT NULL)")
            cur.execute("CREATE TABLE IF NOT EXISTS heights(blockid VARCHAR(64) PRIMARY KEY, height INT NOT NULL)")
            con.commit()
        finally:
            con.close()

    def ensure_genesis(self, genesis_block: dict) -> None:
        con = self._connect()
        try:
            cur = con.cursor()
            gen_id = get_objid(genesis_block)
            res = cur.execute("SELECT obj FROM objects WHERE oid = ?", (gen_id,))
            if res.fetchone() is None:
                gen_str = canonicalize(genesis_block).decode("utf-8")
                cur.execute("INSERT INTO objects VALUES(?, ?)", (gen_id, gen_str))
                cur.execute("INSERT INTO utxo VALUES(?, ?)", (gen_id, "{}"))
                cur.execute("INSERT INTO heights VALUES(?, ?)", (gen_id, 0))
            con.commit()
        finally:
            con.close()

    def get_object(self, oid: str) -> Optional[dict]:
        import json
        con = self._connect()
        try:
            cur = con.cursor()
            res = cur.execute("SELECT obj FROM objects WHERE oid = ?", (oid,))
            row = res.fetchone()
            return json.loads(row[0]) if row else None
        finally:
            con.close()

    def store_object(self, oid: str, obj_dict: dict) -> None:
        con = self._connect()
        try:
            cur = con.cursor()
            obj_str = canonicalize(obj_dict).decode("utf-8")
            cur.execute("INSERT OR REPLACE INTO objects VALUES(?, ?)", (oid, obj_str))
            con.commit()
        finally:
            con.close()

    def store_block(self, block_dict: dict, utxo: dict, height: int) -> str:
        con = self._connect()
        try:
            cur = con.cursor()
            objid = get_objid(block_dict)
            obj_str = canonicalize(block_dict).decode("utf-8")
            utxo_str = canonicalize(utxo).decode("utf-8")
            cur.execute("INSERT OR REPLACE INTO objects VALUES(?, ?)", (objid, obj_str))
            cur.execute("INSERT OR REPLACE INTO utxo VALUES(?, ?)", (objid, utxo_str))
            cur.execute("INSERT OR REPLACE INTO heights VALUES(?, ?)", (objid, height))
            con.commit()
            return objid
        finally:
            con.close()

    def store_transaction(self, tx_dict: dict) -> str:
        con = self._connect()
        try:
            cur = con.cursor()
            objid = get_objid(tx_dict)
            obj_str = canonicalize(tx_dict).decode("utf-8")
            cur.execute("INSERT OR REPLACE INTO objects VALUES(?, ?)", (objid, obj_str))
            con.commit()
            return objid
        finally:
            con.close()

    def get_utxo(self, blockid: str) -> Optional[dict]:
        import json
        con = self._connect()
        try:
            cur = con.cursor()
            res = cur.execute("SELECT utxoset FROM utxo WHERE blockid = ?", (blockid,))
            row = res.fetchone()
            return json.loads(row[0]) if row else None
        finally:
            con.close()

    def get_height(self, blockid: str) -> Optional[int]:
        con = self._connect()
        try:
            cur = con.cursor()
            res = cur.execute("SELECT height FROM heights WHERE blockid = ?", (blockid,))
            row = res.fetchone()
            return row[0] if row else None
        finally:
            con.close()

    def get_chaintip(self) -> Optional[tuple[str, int]]:
        con = self._connect()
        try:
            cur = con.cursor()
            res = cur.execute("SELECT blockid, height FROM heights ORDER BY height DESC LIMIT 1")
            row = res.fetchone()
            return (row[0], row[1]) if row else None
        finally:
            con.close()

    def get_chain_path(self, tip: str) -> list[str]:
        import json
        path = []
        current = tip
        con = self._connect()
        try:
            cur = con.cursor()
            while current is not None:
                path.append(current)
                res = cur.execute("SELECT obj FROM objects WHERE oid = ?", (current,))
                row = res.fetchone()
                if not row:
                    break
                block = json.loads(row[0])
                current = block.get("previd")
        finally:
            con.close()
        return path

    def object_exists(self, oid: str) -> bool:
        con = self._connect()
        try:
            cur = con.cursor()
            res = cur.execute("SELECT 1 FROM objects WHERE oid = ?", (oid,))
            return res.fetchone() is not None
        finally:
            con.close()

    def get_all_objects(self) -> list[dict]:
        import json
        con = self._connect()
        try:
            cur = con.cursor()
            res = cur.execute("SELECT oid, obj FROM objects")
            return [{"id": row[0], **json.loads(row[1])} for row in res.fetchall()]
        finally:
            con.close()

    def drop(self) -> None:
        if os.path.exists(self.db_name):
            os.unlink(self.db_name)
