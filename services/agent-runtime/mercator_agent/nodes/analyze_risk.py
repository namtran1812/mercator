from __future__ import annotations

from mercator_agent.state.models import (
    AgentState,
)

from mercator_agent.tools.risk import (
    get_risk_decomposition,
)


def analyze_risk_node(
    state: AgentState,
) -> AgentState:
    plan = state.get("plan")

    if (
        plan is not None
        and not plan.needs_risk
    ):
        return {
            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),

                "risk": {
                    "status":
                        "skipped",

                    "reason":
                        "planner_disabled",
                },
            },
        }

    request = state["request"]

    instrument_ids = list(
        request.instrument_ids
    )

    if not instrument_ids:
        security = state.get(
            "security"
        )

        if security is not None:
            if isinstance(
                security,
                dict,
            ):
                instrument_ids = list(
                    security.get(
                        "instrument_ids",
                        [],
                    )
                )
            else:
                instrument_ids = list(
                    security.instrument_ids
                )

    if not instrument_ids:
        return {
            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),

                "risk": {
                    "status":
                        "skipped",

                    "reason":
                        "no_instrument_ids",
                },
            },
        }

    try:
        risk = get_risk_decomposition(
            instrument_ids,
            position_notional=
                1_000_000.0,
        )

        return {
            "risk":
                risk,

            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),

                "risk": {
                    "status":
                        "completed",

                    "instrument_count":
                        risk.instrument_count,

                    "total_dv01":
                        risk.total_dv01,

                    "total_cs01":
                        risk.total_cs01,
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
                    "Risk analysis failed: "
                    f"{error}"
                ),
            ],

            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),

                "risk": {
                    "status":
                        "failed",

                    "error":
                        str(error),
                },
            },
        }
