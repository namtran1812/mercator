from __future__ import annotations

from mercator_agent.state.models import (
    AgentState,
)

from mercator_agent.tools.issuer_resolution import (
    resolve_issuer,
)


def resolve_issuer_node(
    state: AgentState,
) -> AgentState:
    request = state["request"]
    plan = state.get("plan")

    #
    # Explicit issuer/CIK input should always be
    # canonicalized for downstream market analysis and
    # brief generation, even when SEC research itself is
    # not requested.
    #
    # For planner-inferred issuers, avoid the additional
    # SEC issuer lookup unless research needs it.
    #
    if (
        plan is not None
        and not plan.needs_research
        and request.issuer is None
        and request.cik is None
    ):
        return {
            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),
                "issuer_resolution": {
                    "status": "skipped",
                    "reason":
                        "research_not_requested",
                },
            },
        }

    #
    # Explicit request data has highest priority.
    # Planner extraction is the fallback.
    #
    issuer_name = (
        request.issuer
        or (
            plan.issuer
            if plan is not None
            else None
        )
    )

    cik = request.cik

    if (
        issuer_name is None
        and cik is None
    ):
        return {
            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),
                "issuer_resolution": {
                    "status": "skipped",
                    "reason":
                        "no_issuer_or_cik",
                },
            },
        }

    try:
        issuer = resolve_issuer(
            issuer=issuer_name,
            cik=cik,
        )

        return {
            "issuer": issuer,

            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),
                "issuer_resolution": {
                    "status": "resolved",
                    "issuer":
                        issuer.issuer_name,
                    "cik":
                        issuer.cik,
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
                    "Issuer resolution failed: "
                    f"{error}"
                ),
            ],

            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),
                "issuer_resolution": {
                    "status": "failed",
                    "error": str(error),
                },
            },
        }
