import asyncio
from kerma.config import Config
from kerma.network.node import Node
from kerma.api.server import APIServer


async def run():
    config = Config()
    node = Node(config)
    node.api_server = APIServer(host="0.0.0.0", port=3001)
    await node.start()


if __name__ == "__main__":
    print("Starting KermaChain backend...")
    asyncio.run(run())
