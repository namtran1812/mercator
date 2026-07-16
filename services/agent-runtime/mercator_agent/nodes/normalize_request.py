from __future__ import annotations

from mercator_agent.state.models import (
    AgentRequest,
    AgentState,
)


def normalize_request_node(
    state: AgentState,
) -> AgentState:
    request = AgentRequest.model_validate(
        state["request"]
    )

    return {
        "request": request,
    }
