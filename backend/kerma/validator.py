from __future__ import annotations
import asyncio
import time
from copy import copy
from typing import Dict, Any


class Validator:
    def __init__(self):
        self.pending_objects: Dict[str, Any] = {}

    def verification_pending(self, obj: dict, queue, unknown_objects: list) -> None:
        from kerma.crypto.hashing import get_objid
        objid = get_objid(obj)
        self.pending_objects[objid] = {
            "object": obj,
            "queues": [queue] if queue else [],
            "unknown_objects": copy(unknown_objects),
            "unreceived_objects": copy(unknown_objects),
            "timeout": time.time() + 5,
        }
        asyncio.create_task(self._timeout_check())

    async def _timeout_check(self) -> None:
        await asyncio.sleep(5)
        now = time.time()
        for key in list(self.pending_objects.keys()):
            o = self.pending_objects[key]
            if o["timeout"] < now and len(o["unreceived_objects"]) > 0:
                self.pending_objects.pop(key, None)

    def is_pending(self, objectid: str) -> bool:
        return objectid in self.pending_objects

    def add_peer(self, objectid: str, queue) -> None:
        if objectid in self.pending_objects and queue:
            o = self.pending_objects[objectid]
            if queue not in o["queues"]:
                o["queues"].append(queue)

    def received_object(self, objid: str) -> None:
        for o in self.pending_objects.values():
            if objid in o["unreceived_objects"]:
                o["unreceived_objects"].remove(objid)

    def new_valid_object(self, objid: str) -> None:
        for key in list(self.pending_objects.keys()):
            o = self.pending_objects[key]
            if objid in o["unknown_objects"]:
                o["unknown_objects"].remove(objid)
                if not o["unknown_objects"]:
                    self.pending_objects.pop(key, None)
                    for q in o["queues"]:
                        try:
                            q.put_nowait({"type": "resumeValidation", "object": o["object"]})
                        except Exception:
                            pass
