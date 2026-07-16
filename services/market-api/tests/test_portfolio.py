from __future__ import annotations

from datetime import datetime, timezone

from app.models import (
    LatestBondPrice,
    PortfolioPosition,
    PortfolioRiskRequest,
)
from app.portfolio import (
    calculate_portfolio_risk,
)


def make_price(
    instrument_id: int,
    clean_price: float,
    duration: float,
    convexity: float,
    spread: float,
) -> LatestBondPrice:
    return LatestBondPrice(
        instrument_id=instrument_id,
        clean_price=clean_price,
        dirty_price=clean_price + 1.0,
        yield_to_maturity=0.05,
        g_spread_bps=spread,
        modified_duration=duration,
        convexity=convexity,
        quality_score=0.95,
        quality_status="VALID",
        curve_version=2,
        reference_version=1,
        event_time=datetime.now(
            timezone.utc
        ),
    )


def test_portfolio_market_value_and_dv01() -> None:
    response = calculate_portfolio_risk(
        prices=[
            make_price(
                1,
                100.0,
                5.0,
                25.0,
                150.0,
            ),
            make_price(
                2,
                90.0,
                3.0,
                15.0,
                200.0,
            ),
        ],
        request=PortfolioRiskRequest(
            positions=[
                PortfolioPosition(
                    instrument_id=1,
                    face_value=1_000_000,
                ),
                PortfolioPosition(
                    instrument_id=2,
                    face_value=2_000_000,
                ),
            ]
        ),
    )

    assert response.position_count == 2
    assert response.total_face_value == 3_000_000
    assert response.total_market_value == 2_800_000
    assert response.total_dv01 > 0.0


def test_weights_sum_to_one() -> None:
    response = calculate_portfolio_risk(
        prices=[
            make_price(
                1,
                100.0,
                5.0,
                25.0,
                150.0,
            ),
            make_price(
                2,
                100.0,
                3.0,
                15.0,
                200.0,
            ),
        ],
        request=PortfolioRiskRequest(
            positions=[
                PortfolioPosition(
                    instrument_id=1,
                    face_value=1_000_000,
                ),
                PortfolioPosition(
                    instrument_id=2,
                    face_value=1_000_000,
                ),
            ]
        ),
    )

    total_weight = sum(
        position.market_value_weight
        for position in response.positions
    )

    assert abs(total_weight - 1.0) < 1e-12
