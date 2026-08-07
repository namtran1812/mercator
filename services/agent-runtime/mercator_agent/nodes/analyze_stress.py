from __future__ import annotations

import re

from mercator_agent.state.models import (
    AgentState,
)

from mercator_agent.tools.stress import (
    run_stress_test,
)


def _extract_number(
    question: str,
    patterns: tuple[str, ...],
) -> float | None:
    for pattern in patterns:
        match = re.search(
            pattern,
            question,
            flags=re.IGNORECASE,
        )

        if match:
            return float(
                match.group(1)
            )

    return None


def _stress_scenario_from_question(
    question: str,
) -> dict[str, float]:
    treasury_parallel_bps = (
        _extract_number(
            question,
            (
                r"(\d+(?:\.\d+)?)\s*bp(?:s)?\s+rate",
                r"(\d+(?:\.\d+)?)\s*bp(?:s)?\s+treasury",
                r"rate\s+shock\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*bp",
                r"treasury\s+shock\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*bp",
            ),
        )
        or 0.0
    )

    credit_parallel_bps = (
        _extract_number(
            question,
            (
                r"(\d+(?:\.\d+)?)\s*bp(?:s)?\s+spread",
                r"(\d+(?:\.\d+)?)\s*bp(?:s)?\s+credit",
                r"spread\s+shock\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*bp",
                r"credit\s+shock\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*bp",
            ),
        )
        or 0.0
    )

    treasury_2y_bps = (
        _extract_number(
            question,
            (
                r"2y\s+(?:rate\s+)?shock\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*bp",
                r"(\d+(?:\.\d+)?)\s*bp(?:s)?\s+2y",
            ),
        )
        or 0.0
    )

    treasury_5y_bps = (
        _extract_number(
            question,
            (
                r"5y\s+(?:rate\s+)?shock\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*bp",
                r"(\d+(?:\.\d+)?)\s*bp(?:s)?\s+5y",
            ),
        )
        or 0.0
    )

    treasury_10y_bps = (
        _extract_number(
            question,
            (
                r"10y\s+(?:rate\s+)?shock\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*bp",
                r"(\d+(?:\.\d+)?)\s*bp(?:s)?\s+10y",
            ),
        )
        or 0.0
    )

    treasury_30y_bps = (
        _extract_number(
            question,
            (
                r"30y\s+(?:rate\s+)?shock\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*bp",
                r"(\d+(?:\.\d+)?)\s*bp(?:s)?\s+30y",
            ),
        )
        or 0.0
    )

    return {
        "treasury_parallel_bps":
            treasury_parallel_bps,

        "treasury_2y_bps":
            treasury_2y_bps,

        "treasury_5y_bps":
            treasury_5y_bps,

        "treasury_10y_bps":
            treasury_10y_bps,

        "treasury_30y_bps":
            treasury_30y_bps,

        "credit_parallel_bps":
            credit_parallel_bps,
    }


def analyze_stress_node(
    state: AgentState,
) -> AgentState:
    plan = state.get(
        "plan"
    )

    if (
        plan is not None
        and not plan.needs_stress
    ):
        return {
            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),
                "stress": {
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
                "stress": {
                    "status":
                        "skipped",
                    "reason":
                        "no_instrument_ids",
                },
            },
        }

    scenario = (
        _stress_scenario_from_question(
            state[
                "request"
            ].question
        )
    )

    #
    # If planner requested stress but no explicit shock
    # could be extracted, use a simple +100bp Treasury
    # parallel shock as the default scenario.
    #
    if not any(
        value != 0.0
        for value in scenario.values()
    ):
        scenario[
            "treasury_parallel_bps"
        ] = 100.0

    try:
        stress = run_stress_test(
            instrument_ids,

            position_notional=
                1_000_000.0,

            **scenario,
        )

        return {
            "stress":
                stress,

            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),
                "stress": {
                    "status":
                        "completed",

                    "instrument_count":
                        stress.instrument_count,

                    "scenario":
                        scenario,

                    "total_market_value":
                        stress.total_market_value,

                    "total_treasury_pnl":
                        stress.total_treasury_pnl,

                    "total_credit_pnl":
                        stress.total_credit_pnl,

                    "total_pnl":
                        stress.total_pnl,
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
                    "Stress analysis failed: "
                    f"{error}"
                ),
            ],

            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),
                "stress": {
                    "status":
                        "failed",
                    "scenario":
                        scenario,
                    "error":
                        str(error),
                },
            },
        }
