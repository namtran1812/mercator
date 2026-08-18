from __future__ import annotations

from mercator_agent.state.models import (
    AgentState,
)

from mercator_agent.tools.pricing import (
    explain_price_move,
)


def attribute_price_move_node(
    state: AgentState,
) -> AgentState:
    """
    Run deterministic price-move attribution only when
    explicitly requested by the planner.
    """

    plan = state.get(
        "plan"
    )

    if (
        plan is not None
        and not plan.needs_price_attribution
    ):
        return {
            "price_attribution": [],

            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),

                "price_attribution": {
                    "status": "skipped",
                    "reason":
                        "planner_disabled",
                },
            },
        }

    quality = state.get(
        "quality"
    )

    if (
        quality is not None
        and quality.status == "BLOCKED"
    ):
        return {
            "price_attribution": [],

            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),

                "price_attribution": {
                    "status": "blocked",
                    "reason":
                        "data_quality_blocked",
                    "quality_score":
                        quality.score,
                },
            },
        }

    #
    # Prefer exactly the securities whose current price
    # snapshot was retrieved by the previous graph node.
    #
    prices = state.get(
        "prices",
        [],
    )

    instrument_ids = [
        price.instrument_id
        for price in prices
    ]

    if not instrument_ids:
        instrument_ids = list(
            state[
                "request"
            ].instrument_ids
        )

    if not instrument_ids:
        security = state.get(
            "security"
        )

        if security is not None:
            instrument_ids = list(
                security.instrument_ids
            )

    if not instrument_ids:
        return {
            "price_attribution": [],

            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),

                "price_attribution": {
                    "status": "skipped",
                    "reason":
                        "no_instrument_ids",
                },
            },
        }

    attributions = []
    failures: list[str] = []

    #
    # Keep interactive agent responses bounded.
    #
    for instrument_id in instrument_ids[:5]:
        try:
            attributions.append(
                explain_price_move(
                    instrument_id
                )
            )

        except Exception as error:
            failures.append(
                (
                    f"Instrument {instrument_id}: "
                    f"{error}"
                )
            )

    result: AgentState = {
        "price_attribution":
            attributions,

        "diagnostics": {
            **state.get(
                "diagnostics",
                {},
            ),

            "price_attribution": {
                "status":
                    (
                        "completed"
                        if attributions
                        else "failed"
                    ),

                "requested":
                    min(
                        len(instrument_ids),
                        5,
                    ),

                "returned":
                    len(attributions),

                "failures":
                    len(failures),
            },
        },
    }

    if failures:
        result["errors"] = [
            *state.get(
                "errors",
                [],
            ),
            *[
                (
                    "Price attribution failed: "
                    + failure
                )
                for failure
                in failures
            ],
        ]

    return result
