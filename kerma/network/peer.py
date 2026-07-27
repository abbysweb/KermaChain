import ipaddress


class Peer:
    def __init__(self, host_str, port: int):
        self.port = int(port)
        self.isBootstrap = False
        try:
            ip = ipaddress.ip_address(host_str)
            self.host = ip.compressed
            self.host_formated = self.host
        except ValueError:
            self.host = host_str
            self.host_formated = host_str

    def tagBootstrap(self):
        self.isBootstrap = True

    def __str__(self) -> str:
        return f"{self.host_formated}:{self.port}"

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Peer):
            return False
        return self.host == o.host and self.port == o.port

    def __hash__(self) -> int:
        return hash((self.host, self.port))

    def __repr__(self) -> str:
        return f"Peer({self.host}, {self.port})"
