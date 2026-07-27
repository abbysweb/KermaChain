from __future__ import annotations
import os
from dataclasses import dataclass, field

from kerma.network.peer import Peer


@dataclass
class Config:
    port: int = int(os.getenv("KERMA_PORT", "18018"))
    address: str = os.getenv("KERMA_ADDRESS", "0.0.0.0")
    db_name: str = os.getenv("KERMA_DB", os.path.join(os.path.dirname(__file__), "..", "..", "db.db"))
    block_target: str = "0000abc000000000000000000000000000000000000000000000000000000000"
    block_reward: int = 50_000_000_000_000
    genesis_block_id: str = "00002fa163c7dab0991544424b9fd302bb1782b185e5a3bbdf12afb758e57dee"
    version: str = "0.10.3"
    agent: str = "KermaChain/1.0"
    service_loop_delay: int = 10
    hello_timeout: float = 20.0
    recv_buffer_limit: int = 512 * 1024
    low_connection_threshold: int = 10
    api_port: int = int(os.getenv("KERMA_API_PORT", "3001"))
    api_host: str = os.getenv("KERMA_API_HOST", "0.0.0.0")

    genesis_block: dict = field(default_factory=lambda: {
        "T": "0000abc000000000000000000000000000000000000000000000000000000000",
        "created": 1671062400,
        "miner": "Marabu",
        "nonce": "00000000000000000000000000000000000000000000000000000000005bb0f2",
        "note": "The New York Times 2022-12-13: Scientists Achieve Nuclear Fusion Breakthrough With Blast of 192 Lasers",
        "previd": None,
        "txids": [],
        "type": "block",
    })

    bootstrap_peers: list[Peer] = field(default_factory=lambda: [
        Peer("128.130.122.73", 18018),
    ])

    banned_hosts: list[str] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> Config:
        return cls()
