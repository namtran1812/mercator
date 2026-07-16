from __future__ import annotations

import asyncio
import json
import os
from collections import defaultdict
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from confluent_kafka import Consumer
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware


RFQ_QUOTED_TOPIC = "market.rfq.quoted"
TRADE_EXECUTED_TOPIC = "market.trade.executed"


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: dict[
            str,
            set[WebSocket],
        ] = defaultdict(set)

    async def connect(
        self,
        rfq_id: str,
        websocket: WebSocket,
    ) -> None:
        await websocket.accept()
        self.connections[rfq_id].add(
            websocket
        )

    def disconnect(
        self,
        rfq_id: str,
        websocket: WebSocket,
    ) -> None:
        self.connections[rfq_id].discard(
            websocket
        )

        if not self.connections[rfq_id]:
            self.connections.pop(
                rfq_id,
                None,
            )

    async def broadcast(
        self,
        rfq_id: str,
        payload: dict[str, object],
    ) -> None:
        sockets = list(
            self.connections.get(
                rfq_id,
                set(),
            )
        )

        disconnected: list[WebSocket] = []

        message = json.dumps(
            payload,
            default=str,
        )

        for websocket in sockets:
            try:
                await websocket.send_text(
                    message
                )
            except Exception:
                disconnected.append(
                    websocket
                )

        for websocket in disconnected:
            self.disconnect(
                rfq_id,
                websocket,
            )


manager = ConnectionManager()
consumer_task: asyncio.Task[None] | None = None


def build_consumer() -> Consumer:
    return Consumer(
        {
            "bootstrap.servers": os.getenv(
                "KAFKA_BOOTSTRAP_SERVERS",
                "localhost:9092",
            ),
            "group.id": (
                "mercator-rfq-websocket-gateway"
            ),
            "auto.offset.reset": "latest",
            "enable.auto.commit": True,
        }
    )


async def consume_events() -> None:
    consumer = build_consumer()

    consumer.subscribe(
        [
            RFQ_QUOTED_TOPIC,
            TRADE_EXECUTED_TOPIC,
        ]
    )

    try:
        while True:
            message = await asyncio.to_thread(
                consumer.poll,
                1.0,
            )

            if message is None:
                continue

            if message.error():
                print(message.error())
                continue

            payload = json.loads(
                message.value().decode(
                    "utf-8"
                )
            )

            rfq_id = str(
                payload["rfq_id"]
            )

            await manager.broadcast(
                rfq_id,
                payload,
            )

    finally:
        consumer.close()


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:
    del app

    global consumer_task

    consumer_task = asyncio.create_task(
        consume_events()
    )

    yield

    if consumer_task is not None:
        consumer_task.cancel()

        try:
            await consumer_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Mercator RFQ Stream",
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


@app.websocket("/ws/rfqs/{rfq_id}")
async def rfq_websocket(
    websocket: WebSocket,
    rfq_id: str,
) -> None:
    await manager.connect(
        rfq_id,
        websocket,
    )

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(
            rfq_id,
            websocket,
        )
