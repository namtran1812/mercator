from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.historical_var import (
    calculate_historical_var,
    generate_historical_shocks,
    percentile,
)
from app.models import (
    HistoricalVarRequest,
    LatestBondPrice,
)


def make_price(
    instrument_id: int,
    duration: float,
) -> LatestBondPrice:
    return LatestBondPrice(
        instrument_id=instrument_id,
        clean_price=100.0,
        dirty_price=101.0,
        yield_to_maturity=0.055,
        g_spread_bps=150.0,
        modified_duration=duration,
        convexity=30.0,
        quality_score=0.95,
        quality_status="VALID",
        curve_version=2,
        reference_version=1,
        event_time=datetime.now(
            timezone.utc
        ),
    )


def test_percentile_interpolates() -> None:
    assert percentile(
        [0.0, 10.0],
        0.5,
    ) == pytest.approx(5.0)


def test_shocks_are_deterministic() -> None:
    first = generate_historical_shocks(
        lookback_days=50,
        seed=42,
    )

    second = generate_historical_shocks(
        lookback_days=50,
        seed=42,
    )

    assert first == second


def test_historical_var_is_positive() -> None:
    response = calculate_historical_var(
        prices=[
            make_price(1, 5.0),
            make_price(2, 10.0),
        ],
        request=HistoricalVarRequest(
            instrument_ids=[1, 2],
            position_notional=1_000_000.0,
            confidence_level=0.99,
            lookback_days=250,
            seed=42,
        ),
    )

    assert response.value_at_risk > 0.0
    assert response.expected_shortfall > 0.0
    assert (
        response.expected_shortfall
        >= response.value_at_risk
    )


def test_longer_duration_increases_var() -> None:
    short_duration = calculate_historical_var(
        prices=[
            make_price(1, 2.0),
        ],
        request=HistoricalVarRequest(
            instrument_ids=[1],
            lookback_days=250,
            seed=42,
        ),
    )

    long_duration = calculate_historical_var(
        prices=[
            make_price(1, 12.0),
        ],
        request=HistoricalVarRequest(
            instrument_ids=[1],
            lookback_days=250,
            seed=42,
        ),
    )

    assert (
        long_duration.value_at_risk
        > short_duration.value_at_risk
    )


def test_contributions_exist_for_each_instrument() -> None:
    response = calculate_historical_var(
        prices=[
            make_price(1, 5.0),
            make_price(2, 7.0),
            make_price(3, 10.0),
        ],
        request=HistoricalVarRequest(
            instrument_ids=[1, 2, 3],
            lookback_days=100,
            seed=7,
        ),
    )

    assert (
        len(
            response.instrument_contributions
        )
        == 3
    )
