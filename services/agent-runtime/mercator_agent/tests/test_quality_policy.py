from __future__ import annotations

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from mercator_agent.state.models import (
    PriceObservation,
)

from mercator_agent.tools.quality import (
    assess_market_quality,
)


def make_price(
    *,
    quality_status: str = "VALID",
    quality_score: float = 1.0,
    reference_version: int | None = 1,
    age_seconds: int = 0,
) -> PriceObservation:
    event_time = (
        datetime.now(
            timezone.utc
        )
        - timedelta(
            seconds=age_seconds
        )
    )

    return PriceObservation(
        instrument_id=1,
        clean_price=100.0,
        dirty_price=100.5,
        yield_to_maturity=0.05,
        g_spread_bps=100.0,
        modified_duration=4.0,
        convexity=20.0,
        quality_score=quality_score,
        quality_status=quality_status,
        curve_version=2,
        reference_version=
            reference_version,
        event_time=
            event_time.isoformat(),
        source="test",
    )


def test_healthy_quality() -> None:
    result = assess_market_quality(
        [
            make_price()
        ]
    )

    assert result.status == "HEALTHY"
    assert result.score == 1.0
    assert result.issues == []


def test_stale_price_is_degraded() -> None:
    result = assess_market_quality(
        [
            make_price(
                age_seconds=600,
            )
        ]
    )

    assert result.status == "DEGRADED"

    assert any(
        issue.code == "STALE_PRICE"
        for issue in result.issues
    )


def test_missing_reference_version_is_degraded() -> None:
    result = assess_market_quality(
        [
            make_price(
                reference_version=None,
            )
        ]
    )

    assert result.status == "DEGRADED"

    assert any(
        issue.code
        == "MISSING_REFERENCE_VERSION"
        for issue in result.issues
    )


def test_invalid_price_blocks() -> None:
    result = assess_market_quality(
        [
            make_price(
                quality_status="STALE",
            )
        ]
    )

    assert result.status == "BLOCKED"

    assert any(
        issue.severity == "BLOCKING"
        for issue in result.issues
    )


def test_very_low_quality_blocks() -> None:
    result = assess_market_quality(
        [
            make_price(
                quality_score=0.25,
            )
        ]
    )

    assert result.status == "BLOCKED"
