from __future__ import annotations

from mercator_agent.state.models import AgentState
from mercator_agent.tools.relative_value import (
    calculate_relative_value,
)


def analyze_relative_value_node(
    state: AgentState,
) -> AgentState:
    results = calculate_relative_value(
        state.get("prices", [])
    )

    return {
        "relative_value": results,
    }
