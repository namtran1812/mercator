from __future__ import annotations

from mercator_agent.state.models import AgentState
from mercator_agent.tools.research import (
    search_research,
)


def retrieve_research_node(
    state: AgentState,
) -> AgentState:
    issuer = state.get("issuer")

    if issuer is None:
        return {
            "errors": [
                *state.get("errors", []),
                "Research retrieval skipped because "
                "issuer resolution failed.",
            ],
        }

    request = state["request"]

    try:
        evidence = search_research(
            question=request.question,
            cik=issuer.cik,
            limit=request.maximum_evidence,
        )

        return {
            "evidence": evidence,
        }

    except Exception as error:
        return {
            "errors": [
                *state.get("errors", []),
                f"Research retrieval failed: {error}",
            ],
            "evidence": [],
        }
