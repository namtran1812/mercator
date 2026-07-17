from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.hedging import (
    calculate_hedge_recommendations,
)
from app.models import (
    HedgeRecommendationRequest,
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


def test_full_hedge_reduces_residuals_to_zero() -> None:
    response = calculate_hedge_recommendations(
        prices=[
            make_price(1, 5.0),
            make_price(2, 10.0),
        ],
        request=HedgeRecommendationRequest(
            instrument_ids=[1, 2],
            position_notional=1_000_000.0,
            hedge_ratio=1.0,
            include_credit_hedge=True,
        ),
    )

    assert response.residual_dv01 == (
        pytest.approx(0.0)
    )

    assert response.residual_cs01 == (
        pytest.approx(0.0)
    )


def test_half_hedge_leaves_half_risk() -> None:
    response = calculate_hedge_recommendations(
        prices=[
            make_price(1, 5.0),
            make_price(2, 10.0),
        ],
        request=HedgeRecommendationRequest(
            instrument_ids=[1, 2],
            position_notional=1_000_000.0,
            hedge_ratio=0.5,
            include_credit_hedge=True,
        ),
    )

    assert response.residual_dv01 == (
        pytest.approx(
            response.total_dv01 * 0.5
        )
    )

    assert response.residual_cs01 == (
        pytest.approx(
            response.total_cs01 * 0.5
        )
    )


def test_long_portfolio_produces_short_hedges() -> None:
    response = calculate_hedge_recommendations(
        prices=[
            make_price(1, 5.0),
        ],
        request=HedgeRecommendationRequest(
            instrument_ids=[1],
            position_notional=1_000_000.0,
            hedge_ratio=1.0,
            include_credit_hedge=True,
        ),
    )

    assert response.treasury_hedges

    assert all(
        hedge.recommended_notional < 0.0
        for hedge in response.treasury_hedges
    )

    assert response.credit_hedge is not None

    assert (
        response.credit_hedge.recommended_notional
        < 0.0
    )


def test_credit_hedge_can_be_disabled() -> None:
    response = calculate_hedge_recommendations(
        prices=[
            make_price(1, 7.0),
        ],
        request=HedgeRecommendationRequest(
            instrument_ids=[1],
            include_credit_hedge=False,
        ),
    )

    assert response.credit_hedge is None

    assert response.residual_cs01 == (
        pytest.approx(response.total_cs01)
    )
