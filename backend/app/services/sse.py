"""In-process Server-Sent Events for one backend worker; no Redis integration."""
from __future__ import annotations

import asyncio
import json
from typing import Any

_clients: set[asyncio.Queue] = set()


def broadcast(payload: dict[str, Any]) -> None:
    """Push an event to every connected SSE client."""
    data = json.dumps(payload, default=str)
    for q in list(_clients):
        try:
            q.put_nowait(f"data: {data}\n\n")
        except Exception:
            pass


async def event_generator():
    queue: asyncio.Queue = asyncio.Queue()
    _clients.add(queue)
    try:
        while True:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                yield msg
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"
    finally:
        _clients.discard(queue)
