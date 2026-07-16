from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.reconciliation import reconcile_observations
from app.reconciliation_models import ReferenceObservation


def make_observation(
    value: str,
    source: str,
    priority: int,
    trust: float,
) -> ReferenceObservation:
    return ReferenceObservation(
        observation_id=uuid4(),
        instrument_id=1,
        field_name="rating",
        field_value=value,
        source_name=source,
        source_priority=priority,
        trust_score=trust,
        valid_from=datetime.now(timezone.utc),
    )


def test_consensus_beats_single_conflicting_source() -> None:
    observations = [
        make_observation(
            "BBB+",
            "rating-agency-a",
            20,
            0.97,
        ),
        make_observation(
            "BBB+",
            "rating-agency-b",
            25,
            0.95,
        ),
        make_observation(
            "A-",
            "vendor-a",
            40,
            0.90,
        ),
    ]

    result = reconcile_observations(observations)

    assert result.selected_value == "BBB+"
    assert result.selected_source == "rating-agency-a"
    assert 0.68 < result.confidence_score < 0.69


def test_priority_breaks_equal_support_tie() -> None:
    observations = [
        make_observation(
            "A",
            "issuer-filing",
            10,
            0.90,
        ),
        make_observation(
            "A-",
            "vendor-a",
            40,
            0.90,
        ),
    ]

    result = reconcile_observations(observations)

    assert result.selected_value == "A"
    assert result.selected_source == "issuer-filing"
