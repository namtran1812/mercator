from __future__ import annotations

from mercator_agent.state.models import (
    AgentState,
)

from mercator_agent.tools.research import (
    search_research,
)


def retrieve_research_node(
    state: AgentState,
) -> AgentState:
    plan = state.get("plan")

    if (
        plan is not None
        and not plan.needs_research
    ):
        return {
            "evidence": [],

            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),
                "research": {
                    "status": "skipped",
                    "reason":
                        "planner_disabled",
                },
            },
        }

    issuer = state.get(
        "issuer"
    )

    if issuer is None:
        return {
            "evidence": [],

            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),
                "research": {
                    "status": "skipped",
                    "reason":
                        "issuer_unresolved",
                },
            },
        }

    request = state["request"]

    try:
        evidence = search_research(
            question=
                request.question,

            cik=
                issuer.cik,

            limit=
                request.maximum_evidence,
        )

        return {
            "evidence": evidence,

            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),
                "research": {
                    "status": "completed",
                    "results":
                        len(evidence),
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
                    "Research retrieval failed: "
                    f"{error}"
                ),
            ],

            "evidence": [],

            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),
                "research": {
                    "status": "failed",
                    "error": str(error),
                },
            },
        }
