from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

REDIS_CHANNEL = "mercator:price-updates"


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: set[WebSocket] = set()

    async def connect(
        self,
        websocket: WebSocket,
    ) -> None:
        await websocket.accept()
        self.connections.add(websocket)

    def disconnect(
        self,
        websocket: WebSocket,
    ) -> None:
        self.connections.discard(websocket)

    async def broadcast(
        self,
        message: str,
    ) -> None:
        disconnected: list[WebSocket] = []

        for websocket in self.connections:
            try:
                await websocket.send_text(message)
            except Exception:
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(websocket)


manager = ConnectionManager()
listener_task: asyncio.Task[None] | None = None


async def redis_listener() -> None:
    redis = Redis.from_url(
        os.getenv(
            "REDIS_URL",
            "redis://localhost:6379/0",
        ),
        decode_responses=True,
    )

    pubsub = redis.pubsub()
    await pubsub.subscribe(REDIS_CHANNEL)

    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue

            await manager.broadcast(
                str(message["data"])
            )
    finally:
        await pubsub.unsubscribe(
            REDIS_CHANNEL
        )
        await pubsub.close()
        await redis.aclose()


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:
    del app

    global listener_task

    listener_task = asyncio.create_task(
        redis_listener()
    )

    yield

    if listener_task is not None:
        listener_task.cancel()

        try:
            await listener_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Mercator Streaming Gateway",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.websocket("/ws/prices")
async def prices_websocket(
    websocket: WebSocket,
) -> None:
    await manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
