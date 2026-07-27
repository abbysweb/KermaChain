from __future__ import annotations
import json
import time
import asyncio
from typing import TYPE_CHECKING

from aiohttp import web

if TYPE_CHECKING:
    from kerma.network.node import Node


class APIServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 3001):
        self.host = host
        self.port = port
        self.node: Node | None = None
        self.ws_clients: set[web.WebSocketResponse] = set()
        self.start_time = time.time()

    async def start(self, node: Node) -> None:
        self.node = node
        app = web.Application()
        app.router.add_get("/", self.index)
        app.router.add_get("/api/health", self.health)
        app.router.add_get("/api/stats", self.stats)
        app.router.add_get("/api/chain", self.chain)
        app.router.add_get("/api/blocks/{id}", self.block_detail)
        app.router.add_get("/api/mempool", self.mempool)
        app.router.add_get("/api/peers", self.peers)
        app.router.add_get("/api/objects/{id}", self.get_object)
        app.router.add_get("/ws/live", self.websocket)
        app.middlewares.append(self.cors_middleware)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        print(f"API server running at http://{self.host}:{self.port}")

    @web.middleware
    async def cors_middleware(self, request, handler):
        resp = await handler(request)
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp

    def _json(self, data, status=200):
        return web.json_response(data, status=status, content_type="application/json")

    async def index(self, request):
        return self._json({
            "name": "KermaChain API",
            "version": "1.0.0",
            "endpoints": {
                "health": "/api/health",
                "stats": "/api/stats",
                "chain": "/api/chain",
                "block": "/api/blocks/{id}",
                "mempool": "/api/mempool",
                "peers": "/api/peers",
                "object": "/api/objects/{id}",
                "websocket": "/ws/live"
            },
            "docs": "https://github.com/abbysweb/KermaChain"
        })

    async def health(self, request):
        return self._json({"status": "ok", "version": "1.0.0", "uptime": int(time.time() - self.start_time)})

    async def stats(self, request):
        s = self.node.get_stats()
        s["uptime"] = int(time.time() - self.start_time)
        return self._json(s)

    async def chain(self, request):
        limit = int(request.query.get("limit", "50"))
        blocks = self.node.blockchain.get_chain(limit)
        result = []
        for b in blocks:
            result.append({
                "id": b.get("id", ""),
                "height": b.get("height", 0),
                "timestamp": b.get("created", 0),
                "txCount": len(b.get("txids", [])),
                "miner": b.get("miner", ""),
                "nonce": b.get("nonce", ""),
                "target": b.get("T", ""),
                "previd": b.get("previd"),
                "txids": b.get("txids", []),
            })
        return self._json(result)

    async def block_detail(self, request):
        block_id = request.match_info["id"]
        info = self.node.blockchain.get_block_info(block_id)
        if info is None:
            return self._json({"error": "block not found"}, 404)
        return self._json({
            "id": block_id,
            "height": info.get("height", 0),
            "timestamp": info.get("created", 0),
            "txCount": len(info.get("txids", [])),
            "miner": info.get("miner", ""),
            "nonce": info.get("nonce", ""),
            "target": info.get("T", ""),
            "previd": info.get("previd"),
            "txids": info.get("txids", []),
        })

    async def mempool(self, request):
        entries = self.node.mempool.get_entries() if self.node.mempool else []
        return self._json(entries)

    async def peers(self, request):
        result = []
        for peer in self.node.peers.get_all():
            connected = peer in self.node.connections
            result.append({
                "host": peer.host,
                "port": peer.port,
                "connected": connected,
                "connectedSince": None,
            })
        return self._json(result)

    async def get_object(self, request):
        obj_id = request.match_info["id"]
        obj = self.node.db.get_object(obj_id)
        if obj is None:
            return self._json({"error": "object not found"}, 404)
        return self._json({"id": obj_id, **obj})

    async def websocket(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.ws_clients.add(ws)
        try:
            async for msg in ws:
                pass
        finally:
            self.ws_clients.discard(ws)
        return ws

    async def broadcast_ws(self, msg_type: str, data: dict) -> None:
        dead = set()
        for ws in self.ws_clients:
            try:
                await ws.send_json({"type": msg_type, "data": data})
            except Exception:
                dead.add(ws)
        self.ws_clients -= dead
