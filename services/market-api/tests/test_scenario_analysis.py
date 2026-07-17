from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.models import (
    LatestBondPrice,
    ScenarioAnalysisRequest,
)
from app.scenario_analysis import analyze_scenario


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
        curve_version=1,
        reference_version=1,
        event_time=datetime.now(
            timezone.utc
        ),
    )


def test_parallel_rate_increase_generates_loss() -> None:
    response = analyze_scenario(
        prices=[
            make_price(1, 5.0, 30.0),
        ],
        request=ScenarioAnalysisRequest(
            instrument_ids=[1],
            position_notional=1_000_000.0,
            treasury_shift_bps=50.0,
        ),
    )

    assert response.total_pnl < 0.0
    assert response.treasury_pnl < 0.0


def test_spread_tightening_generates_gain() -> None:
    response = analyze_scenario(
        prices=[
            make_price(1, 5.0, 30.0),
        ],
        request=ScenarioAnalysisRequest(
            instrument_ids=[1],
            position_notional=1_000_000.0,
            spread_shift_bps=-25.0,
        ),
    )

    assert response.spread_pnl > 0.0
    assert response.total_pnl > 0.0


def test_liquidity_haircut_is_applied_per_position() -> None:
    response = analyze_scenario(
        prices=[
            make_price(1, 5.0, 30.0),
            make_price(2, 7.0, 40.0),
        ],
        request=ScenarioAnalysisRequest(
            instrument_ids=[1, 2],
            position_notional=1_000_000.0,
            liquidity_haircut_percent=2.0,
        ),
    )

    assert response.liquidity_pnl == pytest.approx(
        -40_000.0
    )


def test_downgrade_generates_loss() -> None:
    response = analyze_scenario(
        prices=[
            make_price(1, 5.0, 30.0),
        ],
        request=ScenarioAnalysisRequest(
            instrument_ids=[1],
            position_notional=1_000_000.0,
            downgrade_notches=2,
        ),
    )

    assert response.downgrade_pnl < 0.0


def test_component_totals_reconcile() -> None:
    response = analyze_scenario(
        prices=[
            make_price(1, 5.0, 30.0),
            make_price(2, 7.0, 40.0),
        ],
        request=ScenarioAnalysisRequest(
            instrument_ids=[1, 2],
            position_notional=1_000_000.0,
            treasury_shift_bps=50.0,
            spread_shift_bps=25.0,
            liquidity_haircut_percent=1.0,
            downgrade_notches=1,
        ),
    )

    expected_total = (
        response.treasury_pnl
        + response.spread_pnl
        + response.liquidity_pnl
        + response.downgrade_pnl
    )

    assert response.total_pnl == pytest.approx(
        expected_total
    )

    assert sum(
        item.pnl
        for item in response.instruments
    ) == pytest.approx(
        response.total_pnl
    )


def test_missing_prices_raise_value_error() -> None:
    with pytest.raises(
        ValueError,
        match="No pricing data",
    ):
        analyze_scenario(
            prices=[],
            request=ScenarioAnalysisRequest(
                instrument_ids=[99],
                position_notional=1_000_000.0,
            ),
        )
