from __future__ import annotations
import asyncio
from typing import Optional

from kerma.network.peer import Peer


class Connection:
    def __init__(self, peer: Peer, queue: asyncio.Queue):
        self.peer = peer
        self.queue = queue
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None

    async def send(self, msg_dict: dict) -> None:
        await self.queue.put(msg_dict)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Connection):
            return False
        return self.peer == other.peer

    def __hash__(self) -> int:
        return hash(self.peer)

    def __repr__(self) -> str:
        return f"Connection({self.peer})"
