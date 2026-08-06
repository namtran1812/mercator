from __future__ import annotations

from datetime import datetime, timezone

from app.market_stream import SimulatedMarket
from app.models import LatestBondPrice


def make_price(
    instrument_id: int,
) -> LatestBondPrice:
    return LatestBondPrice(
        instrument_id=instrument_id,
        clean_price=100.0,
        dirty_price=101.0,
        yield_to_maturity=0.05,
        g_spread_bps=150.0,
        modified_duration=5.0,
        convexity=30.0,
        quality_score=0.95,
        quality_status="VALID",
        curve_version=1,
        reference_version=1,
        event_time=datetime.now(
            timezone.utc
        ),
    )


def test_tick_contains_all_instruments() -> None:
    market = SimulatedMarket(
        prices=[
            make_price(1),
            make_price(2),
        ],
        volatility_bps=2.0,
        seed=42,
    )

    tick = market.next_tick()

    assert tick["type"] == "market_data"
    assert tick["sequence"] == 1
    assert tick["instrument_count"] == 2

    assert {
        update["instrument_id"]
        for update in tick["updates"]
    } == {1, 2}


def test_sequence_increments() -> None:
    market = SimulatedMarket(
        prices=[make_price(1)],
        volatility_bps=2.0,
        seed=42,
    )

    first = market.next_tick()
    second = market.next_tick()

    assert first["sequence"] == 1
    assert second["sequence"] == 2


def test_zero_volatility_keeps_price_constant() -> None:
    market = SimulatedMarket(
        prices=[make_price(1)],
        volatility_bps=0.0,
        seed=42,
    )

    tick = market.next_tick()
    update = tick["updates"][0]

    assert update["clean_price"] == 100.0
    assert update["dirty_price"] == 101.0
    assert update["price_change"] == 0.0


def test_same_seed_is_deterministic() -> None:
    first_market = SimulatedMarket(
        prices=[make_price(1)],
        volatility_bps=2.0,
        seed=7,
    )

    second_market = SimulatedMarket(
        prices=[make_price(1)],
        volatility_bps=2.0,
        seed=7,
    )

    first_update = (
        first_market.next_tick()["updates"][0]
    )

    second_update = (
        second_market.next_tick()["updates"][0]
    )

    assert first_update == second_update
