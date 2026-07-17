from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.models import (
    LatestBondPrice,
    RiskDecompositionRequest,
)
from app.risk_decomposition import (
    calculate_risk_decomposition,
    key_rate_weights,
)


def make_price(
    instrument_id: int,
    clean_price: float,
    duration: float,
) -> LatestBondPrice:
    return LatestBondPrice(
        instrument_id=instrument_id,
        clean_price=clean_price,
        dirty_price=clean_price + 1.0,
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


def test_key_rate_weights_sum_to_one() -> None:
    weights = key_rate_weights(6.0)

    assert sum(
        weight
        for _, _, weight in weights
    ) == pytest.approx(1.0)


def test_key_rate_dv01_sums_to_total_dv01() -> None:
    response = calculate_risk_decomposition(
        prices=[
            make_price(
                instrument_id=1,
                clean_price=100.0,
                duration=5.0,
            )
        ],
        request=RiskDecompositionRequest(
            instrument_ids=[1],
            position_notional=1_000_000.0,
        ),
    )

    instrument = response.instruments[0]

    decomposed_dv01 = sum(
        exposure.key_rate_dv01
        for exposure
        in instrument.key_rate_exposures
    )

    assert decomposed_dv01 == pytest.approx(
        instrument.aggregate_dv01
    )


def test_one_million_position_dv01() -> None:
    response = calculate_risk_decomposition(
        prices=[
            make_price(
                instrument_id=1,
                clean_price=100.0,
                duration=5.0,
            )
        ],
        request=RiskDecompositionRequest(
            instrument_ids=[1],
            position_notional=1_000_000.0,
        ),
    )

    assert response.total_market_value == (
        pytest.approx(1_000_000.0)
    )

    assert response.total_dv01 == (
        pytest.approx(500.0)
    )

    assert response.total_cs01 == (
        pytest.approx(500.0)
    )
