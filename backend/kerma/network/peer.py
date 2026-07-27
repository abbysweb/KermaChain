from __future__ import annotations
import ipaddress


class Peer:
    def __init__(self, host: str, port: int):
        self.port = int(port)
        self.is_bootstrap = False
        try:
            ip = ipaddress.ip_address(host)
            self.host = ip.compressed
        except ValueError:
            self.host = host

    def tag_bootstrap(self) -> None:
        self.is_bootstrap = True

    def __str__(self) -> str:
        return f"{self.host}:{self.port}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Peer):
            return False
        return self.host == other.host and self.port == other.port

    def __hash__(self) -> int:
        return hash((self.host, self.port))

    def __repr__(self) -> str:
        return f"Peer({self.host}, {self.port})"
