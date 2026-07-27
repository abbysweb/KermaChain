from __future__ import annotations
from typing import Optional
from kerma.config import Config
from kerma.storage.database import Database
from kerma.crypto.hashing import get_objid


class Blockchain:
    def __init__(self, config: Config, db: Database):
        self.config = config
        self.db = db
        self.tip_id: str = config.genesis_block_id
        self.tip_height: int = 0

    def initialize(self) -> None:
        self.db.create_tables()
        self.db.ensure_genesis(self.config.genesis_block)
        tip = self.db.get_chaintip()
        if tip:
            self.tip_id, self.tip_height = tip
        print(f"Blockchain initialized at height {self.tip_height}, tip {self.tip_id[:8]}...")

    def get_height(self) -> int:
        return self.tip_height

    def get_tip_id(self) -> str:
        return self.tip_id

    def get_block(self, blockid: str) -> Optional[dict]:
        return self.db.get_object(blockid)

    def get_chain(self, limit: int = 50) -> list[dict]:
        blocks = []
        current = self.tip_id
        for _ in range(limit):
            obj = self.db.get_object(current)
            if obj is None:
                break
            height = self.db.get_height(current)
            obj["id"] = current
            obj["height"] = height
            blocks.append(obj)
            current = obj.get("previd")
            if current is None:
                break
        return blocks

    def get_block_info(self, blockid: str) -> Optional[dict]:
        obj = self.db.get_object(blockid)
        if obj is None:
            return None
        height = self.db.get_height(blockid)
        return {**obj, "id": blockid, "height": height}
