from __future__ import annotations

from mercator_agent.state.models import (
    AgentState,
)

from mercator_agent.tools.hedge import (
    get_hedge_recommendations,
)


def analyze_hedge_node(
    state: AgentState,
) -> AgentState:
    plan = state.get(
        "plan"
    )

    if (
        plan is not None
        and not plan.needs_hedge
    ):
        return {
            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),

                "hedge": {
                    "status":
                        "skipped",

                    "reason":
                        "planner_disabled",
                },
            },
        }

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

                "hedge": {
                    "status":
                        "skipped",

                    "reason":
                        "no_instrument_ids",
                },
            },
        }

    try:
        hedge = get_hedge_recommendations(
            instrument_ids,
            position_notional=
                1_000_000.0,

            hedge_ratio=
                1.0,

            include_credit_hedge=
                True,
        )

        return {
            "hedge":
                hedge,

            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),

                "hedge": {
                    "status":
                        "completed",

                    "instrument_count":
                        hedge.instrument_count,

                    "treasury_hedges":
                        len(
                            hedge.treasury_hedges
                        ),

                    "credit_hedge":
                        hedge.credit_hedge
                        is not None,

                    "residual_dv01":
                        hedge.residual_dv01,

                    "residual_cs01":
                        hedge.residual_cs01,
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
                    "Hedge analysis failed: "
                    f"{error}"
                ),
            ],

            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),

                "hedge": {
                    "status":
                        "failed",

                    "error":
                        str(error),
                },
            },
        }
