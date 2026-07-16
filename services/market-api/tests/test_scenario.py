from __future__ import annotations

from datetime import datetime, timezone

from app.models import (
    LatestBondPrice,
    ScenarioRequest,
)
from app.scenario import calculate_scenario


def make_price(
    instrument_id: int,
    duration: float,
    convexity: float,
) -> LatestBondPrice:
    return LatestBondPrice(
        instrument_id=instrument_id,
        clean_price=100.0,
        dirty_price=101.0,
        yield_to_maturity=0.05,
        g_spread_bps=150.0,
        modified_duration=duration,
        convexity=convexity,
        quality_score=0.95,
        quality_status="VALID",
        curve_version=2,
        reference_version=1,
        event_time=datetime.now(timezone.utc),
    )


def test_positive_rate_shock_reduces_price() -> None:
    response = calculate_scenario(
        [
            make_price(
                instrument_id=1,
                duration=5.0,
                convexity=25.0,
            )
        ],
        ScenarioRequest(
            instrument_ids=[1],
            treasury_shock_bps=100.0,
            position_face_value=1_000_000.0,
        ),
    )

    result = response.results[0]

    assert result.shocked_clean_price < 100.0
    assert result.estimated_pnl < 0.0


def test_higher_duration_has_larger_loss() -> None:
    response = calculate_scenario(
        [
            make_price(1, 3.0, 10.0),
            make_price(2, 7.0, 40.0),
        ],
        ScenarioRequest(
            instrument_ids=[1, 2],
            treasury_shock_bps=50.0,
        ),
    )

    by_id = {
        result.instrument_id: result
        for result in response.results
    }

    assert (
        by_id[2].estimated_pnl
        < by_id[1].estimated_pnl
    )
