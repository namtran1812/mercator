from __future__ import annotations

from unittest.mock import patch

from mercator_agent.graph import graph
from mercator_agent.nodes.plan_query import (
    build_fast_plan,
)
from mercator_agent.state.models import (
    PriceMoveAttribution,
    PriceObservation,
)


def test_price_move_question_routes_deterministically() -> None:
    plan = build_fast_plan(
        "Why did instrument 2902 move?"
    )

    assert plan is not None
    assert plan.intent == "price_attribution"

    assert (
        plan.needs_price_attribution
        is True
    )

    assert plan.needs_prices is True
    assert plan.needs_research is True


def test_credit_quality_question_is_not_price_attribution() -> None:
    plan = build_fast_plan(
        "Explain why Apple's credit quality changed"
    )

    if plan is not None:
        assert (
            plan.needs_price_attribution
            is False
        )


def test_graph_builds_price_move_attribution() -> None:
    price = PriceObservation(
        instrument_id=2902,

        clean_price=98.0,
        dirty_price=98.5,

        yield_to_maturity=0.05,
        g_spread_bps=140.0,
        modified_duration=5.0,
        convexity=40.0,

        quality_status="VALID",

        curve_version=162,
        reference_version=7,

        price_change=-1.0,

        source_event_id=(
            "11111111-2222-5333-8444-555555555555"
        ),

        dependency_tenor="10Y",
        source="redis",
    )

    attribution = PriceMoveAttribution(
        instrument_id=2902,

        curve_version=162,

        source_event_id=(
            "11111111-2222-5333-8444-555555555555"
        ),

        dependency_tenor="10Y",

        old_rate=0.0400,
        new_rate=0.0420,
        rate_change_bps=20.0,

        previous_clean_price=99.0,
        current_clean_price=98.0,

        observed_price_change=-1.0,
        observed_return=(-1.0 / 99.0),

        modified_duration=5.0,
        convexity=40.0,

        duration_return=-0.01,
        convexity_return=0.00008,

        estimated_curve_return=-0.00992,

        estimated_curve_price_change=-0.98208,
        residual_price_change=-0.01792,

        explanation=(
            "The 10Y curve rate rose by 20.00 bp. "
            "The duration/convexity approximation "
            "explains most of the observed move; "
            "the remaining residual is left unexplained."
        ),
    )

    with (
        patch(
            "mercator_agent.nodes.retrieve_prices."
            "latest_prices",
            return_value=[price],
        ),
        patch(
            "mercator_agent.nodes.attribute_price_move."
            "explain_price_move",
            return_value=attribution,
        ),
    ):
        result = graph.invoke(
            {
                "request": {
                    "question":
                        "Why did instrument 2902 move?",

                    "instrument_ids":
                        [2902],

                    "maximum_evidence":
                        5,
                },

                "errors": [],
            }
        )

    assert (
        result["plan"]
        .needs_price_attribution
        is True
    )

    assert len(
        result["price_attribution"]
    ) == 1

    assert (
        result["price_attribution"][0]
        .rate_change_bps
        == 20.0
    )

    assert any(
        "10Y curve rate rose"
        in observation
        for observation
        in result["brief"]
        .market_observations
    )

    assert (
        "deterministic price-move attribution"
        in result["brief"]
        .summary.lower()
    )
