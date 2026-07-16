from __future__ import annotations

from mercator_agent.state.models import AgentState
from mercator_agent.tools.pricing import (
    latest_prices,
)


def retrieve_prices_node(
    state: AgentState,
) -> AgentState:
    instrument_ids = (
        state["request"].instrument_ids
    )

    try:
        prices = latest_prices(
            instrument_ids
        )

        return {
            "prices": prices,
        }

    except Exception as error:
        return {
            "errors": [
                *state.get("errors", []),
                f"Pricing retrieval failed: {error}",
            ],
            "prices": [],
        }
