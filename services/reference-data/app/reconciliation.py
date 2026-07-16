from __future__ import annotations

from collections import defaultdict

from .reconciliation_models import (
    ReconciliationResult,
    ReferenceObservation,
)


def reconcile_observations(
    observations: list[ReferenceObservation],
) -> ReconciliationResult:
    if not observations:
        raise ValueError("observations cannot be empty")

    instrument_ids = {
        observation.instrument_id
        for observation in observations
    }
    field_names = {
        observation.field_name
        for observation in observations
    }

    if len(instrument_ids) != 1:
        raise ValueError("all observations must target one instrument")

    if len(field_names) != 1:
        raise ValueError("all observations must target one field")

    grouped: dict[str, list[ReferenceObservation]] = defaultdict(list)

    for observation in observations:
        grouped[observation.field_value].append(observation)

    scored_values: list[
        tuple[
            float,
            int,
            str,
            list[ReferenceObservation],
        ]
    ] = []

    for value, matching in grouped.items():
        weighted_support = sum(
            observation.trust_score
            for observation in matching
        )

        best_priority = min(
            observation.source_priority
            for observation in matching
        )

        scored_values.append(
            (
                weighted_support,
                -best_priority,
                value,
                matching,
            )
        )

    scored_values.sort(reverse=True)

    selected_support, _, selected_value, selected_group = (
        scored_values[0]
    )

    total_support = sum(
        observation.trust_score
        for observation in observations
    )

    confidence = (
        selected_support / total_support
        if total_support > 0.0
        else 0.0
    )

    selected_source = min(
        selected_group,
        key=lambda observation: observation.source_priority,
    ).source_name

    return ReconciliationResult(
        instrument_id=observations[0].instrument_id,
        field_name=observations[0].field_name,
        selected_value=selected_value,
        selected_source=selected_source,
        confidence_score=confidence,
        contributing_observations=[
            observation.observation_id
            for observation in selected_group
        ],
    )
