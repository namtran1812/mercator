from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket

from .models import LatestBondPrice


@dataclass
class StreamingInstrument:
    instrument_id: int
    clean_price: float
    dirty_price: float
    yield_to_maturity: float
    g_spread_bps: float
    modified_duration: float
    convexity: float
    quality_status: str


class SimulatedMarket:
    def __init__(
        self,
        *,
        prices: list[LatestBondPrice],
        volatility_bps: float,
        seed: int = 42,
    ) -> None:
        self._random = random.Random(seed)
        self._volatility_bps = volatility_bps
        self._sequence = 0

        self._instruments = {
            price.instrument_id: StreamingInstrument(
                instrument_id=price.instrument_id,
                clean_price=float(price.clean_price),
                dirty_price=float(price.dirty_price),
                yield_to_maturity=float(
                    price.yield_to_maturity
                ),
                g_spread_bps=float(price.g_spread_bps),
                modified_duration=float(
                    price.modified_duration
                ),
                convexity=float(price.convexity),
                quality_status=str(price.quality_status),
            )
            for price in prices
        }

    @property
    def instrument_count(self) -> int:
        return len(self._instruments)

    @property
    def sequence(self) -> int:
        return self._sequence

    def next_tick(self) -> dict[str, Any]:
        self._sequence += 1
        event_time = datetime.now(
            timezone.utc
        ).isoformat()

        updates: list[dict[str, Any]] = []

        for instrument in self._instruments.values():
            spread_move_bps = self._random.gauss(
                0.0,
                self._volatility_bps,
            )

            yield_move = (
                spread_move_bps
                / 10_000.0
            )

            price_return = (
                -instrument.modified_duration
                * yield_move
            )

            old_clean_price = instrument.clean_price

            instrument.clean_price = max(
                old_clean_price
                * (1.0 + price_return),
                0.01,
            )

            accrued_interest = (
                instrument.dirty_price
                - old_clean_price
            )

            instrument.dirty_price = max(
                instrument.clean_price
                + accrued_interest,
                0.01,
            )

            instrument.yield_to_maturity = max(
                instrument.yield_to_maturity
                + yield_move,
                0.0,
            )

            instrument.g_spread_bps = max(
                instrument.g_spread_bps
                + spread_move_bps,
                0.0,
            )

            updates.append(
                {
                    "instrument_id": (
                        instrument.instrument_id
                    ),
                    "clean_price": round(
                        instrument.clean_price,
                        6,
                    ),
                    "dirty_price": round(
                        instrument.dirty_price,
                        6,
                    ),
                    "yield_to_maturity": round(
                        instrument.yield_to_maturity,
                        8,
                    ),
                    "g_spread_bps": round(
                        instrument.g_spread_bps,
                        4,
                    ),
                    "modified_duration": (
                        instrument.modified_duration
                    ),
                    "convexity": instrument.convexity,
                    "quality_status": (
                        instrument.quality_status
                    ),
                    "price_change": round(
                        instrument.clean_price
                        - old_clean_price,
                        6,
                    ),
                }
            )

        return {
            "type": "market_data",
            "sequence": self._sequence,
            "event_time": event_time,
            "instrument_count": len(updates),
            "updates": updates,
        }


class MarketDataHub:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    @property
    def client_count(self) -> int:
        return len(self._clients)

    async def connect(
        self,
        websocket: WebSocket,
    ) -> None:
        await websocket.accept()

        async with self._lock:
            self._clients.add(websocket)

    async def disconnect(
        self,
        websocket: WebSocket,
    ) -> None:
        async with self._lock:
            self._clients.discard(websocket)

    async def broadcast(
        self,
        message: dict[str, Any],
    ) -> None:
        async with self._lock:
            clients = list(self._clients)

        disconnected: list[WebSocket] = []

        for client in clients:
            try:
                await client.send_json(message)
            except Exception:
                disconnected.append(client)

        if disconnected:
            async with self._lock:
                for client in disconnected:
                    self._clients.discard(client)


class MarketStreamRuntime:
    def __init__(self) -> None:
        self.hub = MarketDataHub()
        self.task: asyncio.Task[None] | None = None
        self.market: SimulatedMarket | None = None
        self.interval_ms: int | None = None

    @property
    def running(self) -> bool:
        return (
            self.task is not None
            and not self.task.done()
        )

    async def start(
        self,
        *,
        prices: list[LatestBondPrice],
        interval_ms: int,
        volatility_bps: float,
    ) -> None:
        if self.running:
            raise RuntimeError(
                "Market stream is already running."
            )

        if not prices:
            raise ValueError(
                "No pricing data found for requested instruments."
            )

        self.market = SimulatedMarket(
            prices=prices,
            volatility_bps=volatility_bps,
        )

        self.interval_ms = interval_ms

        self.task = asyncio.create_task(
            self._run(),
            name="mercator-market-stream",
        )

    async def stop(self) -> None:
        task = self.task

        self.task = None
        self.market = None
        self.interval_ms = None

        if task is None:
            return

        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

    async def _run(self) -> None:
        try:
            while True:
                market = self.market

                if market is None:
                    return

                message = market.next_tick()

                await self.hub.broadcast(message)

                await asyncio.sleep(
                    (self.interval_ms or 500)
                    / 1_000.0
                )
        except asyncio.CancelledError:
            raise


market_stream_runtime = MarketStreamRuntime()
