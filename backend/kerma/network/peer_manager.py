from __future__ import annotations
import json
import os
from typing import Set

from kerma.network.peer import Peer


class PeerManager:
    def __init__(self, peers_file: str = "peers.json"):
        self.peers_file = peers_file
        self.peers: Set[Peer] = set()
        self._dirty = False
        self._load()

    def _load(self) -> None:
        if os.path.isfile(self.peers_file):
            try:
                with open(self.peers_file, "r") as f:
                    data = json.load(f)
                for p in data:
                    host, port = p.rsplit(":", 1)
                    self.peers.add(Peer(host, int(port)))
            except Exception:
                pass

    def add(self, peer: Peer) -> None:
        if peer not in self.peers:
            self.peers.add(peer)
            self._dirty = True

    def remove(self, peer: Peer) -> None:
        if peer in self.peers:
            self.peers.remove(peer)
            self._dirty = True

    def save(self) -> None:
        if self._dirty:
            try:
                with open(self.peers_file, "w") as f:
                    json.dump([str(p) for p in self.peers], f)
                self._dirty = False
            except Exception:
                pass

    def get_all(self) -> Set[Peer]:
        return self.peers

    def __len__(self) -> int:
        return len(self.peers)
