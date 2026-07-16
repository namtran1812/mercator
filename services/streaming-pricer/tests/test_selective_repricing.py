from __future__ import annotations

from datetime import datetime, timezone

from app.consumer import apply_curve_update
from app.models import CurveUpdate


def test_dependency_weight_reduces_price_impact() -> None:
    base = {
        "instrument_id": 1,
        "clean_price": 100.0,
        "dirty_price": 101.0,
        "yield_to_maturity": 0.05,
        "g_spread_bps": 150.0,
        "modified_duration": 5.0,
        "convexity": 25.0,
        "quality_status": "VALID",
    }

    event = CurveUpdate(
        event_id="test-event",
        event_time=datetime.now(
            timezone.utc
        ),
        curve_version=3,
        tenor="5Y",
        old_rate=0.04,
        new_rate=0.05,
    )

    full_weight = apply_curve_update(
        base,
        event,
        1.0,
    )

    half_weight = apply_curve_update(
        base,
        event,
        0.5,
    )

    assert full_weight.clean_price < (
        half_weight.clean_price
    )

    assert abs(
        half_weight.price_change
    ) < abs(
        full_weight.price_change
    )


def test_positive_rate_change_reduces_price() -> None:
    base = {
        "instrument_id": 1,
        "clean_price": 100.0,
        "dirty_price": 101.0,
        "yield_to_maturity": 0.05,
        "g_spread_bps": 150.0,
        "modified_duration": 5.0,
        "convexity": 25.0,
        "quality_status": "VALID",
    }

    event = CurveUpdate(
        event_id="test-event",
        event_time=datetime.now(
            timezone.utc
        ),
        curve_version=3,
        tenor="5Y",
        old_rate=0.04,
        new_rate=0.045,
    )

    result = apply_curve_update(
        base,
        event,
        1.0,
    )

    assert result.clean_price < 100.0
    assert result.price_change < 0.0
