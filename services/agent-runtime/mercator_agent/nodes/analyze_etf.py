from __future__ import annotations

from mercator_agent.state.models import (
    AgentState,
)

from mercator_agent.tools.etf_analytics import (
    get_etf_analytics,
)


def analyze_etf_node(
    state: AgentState,
) -> AgentState:
    plan = state.get(
        "plan"
    )

    if (
        plan is not None
        and not plan.needs_etf_analytics
    ):
        return {
            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),

                "etf_analytics": {
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

                "etf_analytics": {
                    "status":
                        "skipped",

                    "reason":
                        "no_instrument_ids",
                },
            },
        }

    #
    # Current agent request model supports multiple IDs,
    # while the ETF endpoint is instrument-specific.
    #
    # Start with the first resolved ETF.
    #
    instrument_id = int(
        instrument_ids[0]
    )

    try:
        analytics = get_etf_analytics(
            instrument_id
        )

        return {
            "etf_analytics":
                analytics,

            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),

                "etf_analytics": {
                    "status":
                        "completed",

                    "instrument_id":
                        analytics.instrument_id,

                    "fund_name":
                        analytics.fund_name,

                    "priced_weight":
                        analytics.priced_weight,

                    "premium_discount_percent":
                        analytics.premium_discount_percent,
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
                    "ETF analytics failed: "
                    f"{error}"
                ),
            ],

            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),

                "etf_analytics": {
                    "status":
                        "failed",

                    "instrument_id":
                        instrument_id,

                    "error":
                        str(error),
                },
            },
        }
