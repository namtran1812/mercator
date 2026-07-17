from __future__ import annotations

from datetime import datetime, timezone

from app.carry_roll import (
    calculate_carry_roll,
    interpolate_curve_rate,
)
from app.models import (
    CarryRollRequest,
    LatestBondPrice,
)


def make_price(
    instrument_id: int,
    yield_to_maturity: float,
    spread: float,
    duration: float,
) -> LatestBondPrice:
    return LatestBondPrice(
        instrument_id=instrument_id,
        clean_price=100.0,
        dirty_price=101.0,
        yield_to_maturity=yield_to_maturity,
        g_spread_bps=spread,
        modified_duration=duration,
        convexity=25.0,
        quality_score=0.95,
        quality_status="VALID",
        curve_version=2,
        reference_version=1,
        event_time=datetime.now(
            timezone.utc
        ),
    )


def test_curve_interpolation() -> None:
    rate = interpolate_curve_rate(4.0)

    assert 0.0410 < rate < 0.0430


def test_high_yield_wide_spread_has_positive_carry() -> None:
    response = calculate_carry_roll(
        prices=[
            make_price(1, 0.080, 250.0, 5.0),
            make_price(2, 0.055, 120.0, 5.1),
            make_price(3, 0.056, 125.0, 4.9),
            make_price(4, 0.054, 115.0, 5.2),
        ],
        request=CarryRollRequest(
            instrument_ids=[1, 2, 3, 4],
            horizon_months=3,
            annual_financing_rate=0.045,
            expected_spread_normalization_fraction=0.25,
        ),
    )

    by_id = {
        item.instrument_id: item
        for item in response.opportunities
    }

    assert (
        by_id[1].coupon_carry_return_percent
        > 0.0
    )

    assert (
        by_id[1].expected_spread_change_bps
        < 0.0
    )

    assert (
        by_id[1].expected_total_return_percent
        > by_id[2].expected_total_return_percent
    )


def test_higher_financing_rate_reduces_return() -> None:
    prices = [
        make_price(1, 0.060, 150.0, 5.0),
        make_price(2, 0.060, 150.0, 5.1),
    ]

    low_financing = calculate_carry_roll(
        prices=prices,
        request=CarryRollRequest(
            instrument_ids=[1, 2],
            annual_financing_rate=0.02,
        ),
    )

    high_financing = calculate_carry_roll(
        prices=prices,
        request=CarryRollRequest(
            instrument_ids=[1, 2],
            annual_financing_rate=0.08,
        ),
    )

    assert (
        low_financing.opportunities[
            0
        ].expected_total_return_percent
        >
        high_financing.opportunities[
            0
        ].expected_total_return_percent
    )
