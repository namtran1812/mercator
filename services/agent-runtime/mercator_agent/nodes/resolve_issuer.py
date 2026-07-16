from __future__ import annotations

from mercator_agent.state.models import AgentState
from mercator_agent.tools.issuer_resolution import (
    resolve_issuer,
)


def resolve_issuer_node(
    state: AgentState,
) -> AgentState:
    request = state["request"]

    try:
        issuer = resolve_issuer(
            issuer=request.issuer,
            cik=request.cik,
        )

        return {
            "issuer": issuer,
        }

    except Exception as error:
        return {
            "errors": [
                *state.get("errors", []),
                f"Issuer resolution failed: {error}",
            ],
        }
