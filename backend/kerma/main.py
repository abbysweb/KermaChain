import asyncio
import sys
from kerma.config import Config
from kerma.network.node import Node
from kerma.api.server import APIServer


def main():
    config = Config()
    if len(sys.argv) == 3:
        config.address = sys.argv[1]
        config.port = int(sys.argv[2])

    node = Node(config)
    node.api_server = APIServer(host=config.api_host, port=config.api_port)

    print(f"Starting KermaChain node...")
    print(f"  P2P: {config.address}:{config.port}")
    print(f"  API: {config.api_host}:{config.api_port}")
    asyncio.run(node.start())


if __name__ == "__main__":
    main()
