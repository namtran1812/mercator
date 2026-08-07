from __future__ import annotations

from mercator_agent.state.models import (
    AgentState,
)

from mercator_agent.tools.relative_value import (
    calculate_relative_value,
)


def analyze_relative_value_node(
    state: AgentState,
) -> AgentState:
    plan = state.get("plan")

    if (
        plan is not None
        and not plan.needs_relative_value
    ):
        return {
            "relative_value": [],

            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),
                "relative_value": {
                    "status": "skipped",
                    "reason":
                        "planner_disabled",
                },
            },
        }

    prices = state.get(
        "prices",
        [],
    )

    if not prices:
        return {
            "relative_value": [],

            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),
                "relative_value": {
                    "status": "skipped",
                    "reason":
                        "no_prices",
                },
            },
        }

    try:
        results = (
            calculate_relative_value(
                prices
            )
        )

        return {
            "relative_value":
                results,

            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),
                "relative_value": {
                    "status": "completed",
                    "results":
                        len(results),
                },
            },
        }

    except Exception as error:
        return {
            "errors": [
                *state.get(
                    "errors",
                    [],
                ),
                (
                    "Relative-value analysis "
                    f"failed: {error}"
                ),
            ],

            "relative_value": [],

            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),
                "relative_value": {
                    "status": "failed",
                    "error": str(error),
                },
            },
        }
