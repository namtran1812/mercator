from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.models import (
    LatestBondPrice,
    StressRequest,
    StressScenario,
)
from app.stress import (
    calculate_stress,
    interpolate_treasury_shock_bps,
)


def make_price(
    instrument_id: int,
    clean_price: float = 100.0,
    duration: float = 5.0,
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


def test_treasury_shock_interpolation() -> None:
    shock = interpolate_treasury_shock_bps(
        7.5,
        treasury_2y_bps=10.0,
        treasury_5y_bps=20.0,
        treasury_10y_bps=40.0,
        treasury_30y_bps=60.0,
    )

    assert shock == pytest.approx(30.0)


def test_parallel_rate_increase_loses_money() -> None:
    response = calculate_stress(
        prices=[make_price(1)],
        request=StressRequest(
            instrument_ids=[1],
            position_notional=1_000_000.0,
            scenario=StressScenario(
                treasury_parallel_bps=25.0,
            ),
        ),
    )

    assert response.total_treasury_pnl < 0.0
    assert response.total_credit_pnl == 0.0
    assert response.total_pnl < 0.0


def test_credit_widening_loses_money() -> None:
    response = calculate_stress(
        prices=[make_price(1)],
        request=StressRequest(
            instrument_ids=[1],
            position_notional=1_000_000.0,
            scenario=StressScenario(
                credit_parallel_bps=50.0,
            ),
        ),
    )

    assert response.total_credit_pnl < 0.0
    assert response.total_treasury_pnl == 0.0
    assert response.total_pnl < 0.0


def test_combined_pnl_equals_components() -> None:
    response = calculate_stress(
        prices=[
            make_price(1, duration=5.0),
            make_price(2, duration=10.0),
        ],
        request=StressRequest(
            instrument_ids=[1, 2],
            position_notional=1_000_000.0,
            scenario=StressScenario(
                treasury_parallel_bps=25.0,
                credit_parallel_bps=50.0,
            ),
        ),
    )

    assert response.total_pnl == pytest.approx(
        response.total_treasury_pnl
        + response.total_credit_pnl
    )
