from __future__ import annotations

from mercator_agent.state.models import (
    PriceObservation,
)
from mercator_agent.tools.relative_value import (
    calculate_relative_value,
)


def make_price(
    instrument_id: int,
    spread: float,
) -> PriceObservation:
    return PriceObservation(
        instrument_id=instrument_id,
        clean_price=100.0,
        dirty_price=101.0,
        yield_to_maturity=0.05,
        g_spread_bps=spread,
        modified_duration=4.0,
        quality_score=0.95,
        quality_status="VALID",
        curve_version=2,
        reference_version=1,
    )


def test_relative_value_ranking() -> None:
    results = calculate_relative_value(
        [
            make_price(1, 100.0),
            make_price(2, 150.0),
            make_price(3, 200.0),
        ]
    )

    assert len(results) == 3
    assert results[0].instrument_id == 3
    assert results[0].spread_difference_bps == 50.0
    assert results[-1].instrument_id == 1
