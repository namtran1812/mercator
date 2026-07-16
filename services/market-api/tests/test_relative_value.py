from __future__ import annotations

from datetime import datetime, timezone

from app.models import (
    LatestBondPrice,
    RelativeValueRequest,
)
from app.relative_value import (
    calculate_relative_value,
)


def make_price(
    instrument_id: int,
    spread: float,
    duration: float,
) -> LatestBondPrice:
    return LatestBondPrice(
        instrument_id=instrument_id,
        clean_price=100.0,
        dirty_price=101.0,
        yield_to_maturity=0.05,
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


def test_wide_spread_is_classified_cheap() -> None:
    prices = [
        make_price(1, 100.0, 5.0),
        make_price(2, 105.0, 5.1),
        make_price(3, 110.0, 4.9),
        make_price(4, 115.0, 5.2),
        make_price(5, 220.0, 5.0),
    ]

    response = calculate_relative_value(
        prices=prices,
        request=RelativeValueRequest(
            instrument_ids=[
                1,
                2,
                3,
                4,
                5,
            ],
            duration_bucket_width=1.0,
            minimum_peer_count=3,
        ),
    )

    by_id = {
        item.instrument_id: item
        for item in response.opportunities
    }

    assert by_id[5].classification == "CHEAP"
    assert by_id[5].spread_z_score > 1.5


def test_tight_spread_is_classified_rich() -> None:
    prices = [
        make_price(1, 20.0, 5.0),
        make_price(2, 100.0, 5.1),
        make_price(3, 110.0, 4.9),
        make_price(4, 115.0, 5.2),
        make_price(5, 120.0, 5.0),
    ]

    response = calculate_relative_value(
        prices=prices,
        request=RelativeValueRequest(
            instrument_ids=[
                1,
                2,
                3,
                4,
                5,
            ],
            duration_bucket_width=1.0,
            minimum_peer_count=3,
        ),
    )

    by_id = {
        item.instrument_id: item
        for item in response.opportunities
    }

    assert by_id[1].classification == "RICH"
    assert by_id[1].spread_z_score < -1.5
