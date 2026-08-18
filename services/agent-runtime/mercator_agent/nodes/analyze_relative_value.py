from __future__ import annotations

from mercator_agent.state.models import (
    AgentState,
)

from mercator_agent.tools.relative_value import (
    calculate_relative_value,
)

from mercator_agent.tools.reference_data import (
    find_peer_profiles,
    get_instrument_profiles,
)

from mercator_agent.tools.pricing import (
    latest_prices,
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
        target_ids = [
            price.instrument_id
            for price in prices
        ]

        target_profiles = (
            get_instrument_profiles(
                target_ids
            )
        )

        profile_by_id = {
            profile.instrument_id:
                profile
            for profile
            in target_profiles
        }

        #
        # Expand beyond only the securities explicitly
        # mentioned in the user request.
        #
        for target_profile in target_profiles:
            for peer_profile in (
                find_peer_profiles(
                    target_profile,
                    limit=50,
                )
            ):
                profile_by_id.setdefault(
                    peer_profile.instrument_id,
                    peer_profile,
                )

        additional_ids = [
            instrument_id
            for instrument_id
            in profile_by_id
            if instrument_id
            not in target_ids
        ]

        peer_prices = (
            latest_prices(
                additional_ids
            )
            if additional_ids
            else []
        )

        results = (
            calculate_relative_value(
                [
                    *prices,
                    *peer_prices,
                ],

                profiles=list(
                    profile_by_id.values()
                ),

                target_instrument_ids=
                    target_ids,
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

                    "targets":
                        len(target_ids),

                    "peer_candidates":
                        len(additional_ids),
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
