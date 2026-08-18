from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)

from mercator_agent.state.models import (
    PriceObservation,
    QualityAssessment,
    QualityIssue,
)


def _parse_event_time(
    value: str | None,
) -> datetime | None:
    if not value:
        return None

    normalized = value

    if normalized.endswith("Z"):
        normalized = (
            normalized[:-1]
            + "+00:00"
        )

    try:
        result = datetime.fromisoformat(
            normalized
        )
    except ValueError:
        return None

    if result.tzinfo is None:
        result = result.replace(
            tzinfo=timezone.utc
        )

    return result


def assess_market_quality(
    prices: list[PriceObservation],
    *,
    now: datetime | None = None,
    stale_after_seconds: float = 300.0,
) -> QualityAssessment:
    """
    Aggregate per-price provenance and quality into one
    deterministic analytics policy decision.

    HEALTHY:
        analytics may run normally.

    DEGRADED:
        analytics may run, but consumers should surface
        reduced confidence / provenance warnings.

    BLOCKED:
        analytics whose interpretation depends on these
        observations should not produce directional claims.
    """

    if now is None:
        now = datetime.now(
            timezone.utc
        )

    issues: list[QualityIssue] = []

    if not prices:
        return QualityAssessment(
            status="BLOCKED",
            score=0.0,
            instrument_ids=[],
            issues=[
                QualityIssue(
                    code="NO_PRICES",
                    severity="BLOCKING",
                    message=(
                        "No current evaluated prices "
                        "were available."
                    ),
                )
            ],
        )

    score = 1.0

    for price in prices:
        status = (
            price.quality_status
            .strip()
            .upper()
        )

        if status != "VALID":
            issues.append(
                QualityIssue(
                    code="INVALID_PRICE_STATUS",
                    severity="BLOCKING",
                    instrument_id=
                        price.instrument_id,
                    message=(
                        f"Instrument "
                        f"{price.instrument_id} has "
                        f"pricing quality status "
                        f"{price.quality_status}."
                    ),
                )
            )

        if price.quality_score < 0.50:
            issues.append(
                QualityIssue(
                    code="LOW_PRICE_QUALITY",
                    severity="BLOCKING",
                    instrument_id=
                        price.instrument_id,
                    message=(
                        f"Instrument "
                        f"{price.instrument_id} has "
                        f"pricing quality score "
                        f"{price.quality_score:.2f}."
                    ),
                )
            )

        elif price.quality_score < 0.80:
            issues.append(
                QualityIssue(
                    code="DEGRADED_PRICE_QUALITY",
                    severity="WARNING",
                    instrument_id=
                        price.instrument_id,
                    message=(
                        f"Instrument "
                        f"{price.instrument_id} has "
                        f"pricing quality score "
                        f"{price.quality_score:.2f}."
                    ),
                )
            )

            score = min(
                score,
                price.quality_score,
            )

        event_time = _parse_event_time(
            price.event_time
        )

        if price.event_time and event_time is None:
            issues.append(
                QualityIssue(
                    code="INVALID_EVENT_TIME",
                    severity="WARNING",
                    instrument_id=
                        price.instrument_id,
                    message=(
                        f"Instrument "
                        f"{price.instrument_id} has "
                        "an unparseable price event "
                        "timestamp."
                    ),
                )
            )

            score = min(
                score,
                0.75,
            )

        elif event_time is not None:
            age_seconds = (
                now
                - event_time
            ).total_seconds()

            if age_seconds > stale_after_seconds:
                issues.append(
                    QualityIssue(
                        code="STALE_PRICE",
                        severity="WARNING",
                        instrument_id=
                            price.instrument_id,
                        message=(
                            f"Instrument "
                            f"{price.instrument_id} "
                            f"price is "
                            f"{age_seconds:.0f}s old."
                        ),
                    )
                )

                score = min(
                    score,
                    0.70,
                )

        if price.reference_version is None:
            issues.append(
                QualityIssue(
                    code="MISSING_REFERENCE_VERSION",
                    severity="WARNING",
                    instrument_id=
                        price.instrument_id,
                    message=(
                        f"Instrument "
                        f"{price.instrument_id} price "
                        "does not carry a reference-data "
                        "version."
                    ),
                )
            )

            score = min(
                score,
                0.85,
            )

    has_blocker = any(
        issue.severity == "BLOCKING"
        for issue in issues
    )

    if has_blocker:
        status = "BLOCKED"
        score = min(
            score,
            0.49,
        )

    elif issues:
        status = "DEGRADED"

    else:
        status = "HEALTHY"

    return QualityAssessment(
        status=status,
        score=max(
            0.0,
            min(
                1.0,
                score,
            ),
        ),
        instrument_ids=[
            price.instrument_id
            for price in prices
        ],
        issues=issues,
    )
