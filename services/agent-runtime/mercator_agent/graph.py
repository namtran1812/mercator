from __future__ import annotations

from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from mercator_agent.nodes.analyze_relative_value import (
    analyze_relative_value_node,
)
from mercator_agent.nodes.compose_brief import (
    compose_brief_node,
)
from mercator_agent.nodes.normalize_request import (
    normalize_request_node,
)
from mercator_agent.nodes.resolve_issuer import (
    resolve_issuer_node,
)
from mercator_agent.nodes.retrieve_prices import (
    retrieve_prices_node,
)
from mercator_agent.nodes.retrieve_research import (
    retrieve_research_node,
)
from mercator_agent.nodes.validate_evidence import (
    validate_evidence_node,
)
from mercator_agent.state.models import AgentState


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node(
        "normalize_request",
        normalize_request_node,
    )

    builder.add_node(
        "resolve_issuer",
        resolve_issuer_node,
    )

    builder.add_node(
        "retrieve_research",
        retrieve_research_node,
    )

    builder.add_node(
        "retrieve_prices",
        retrieve_prices_node,
    )

    builder.add_node(
        "analyze_relative_value",
        analyze_relative_value_node,
    )

    builder.add_node(
        "validate_evidence",
        validate_evidence_node,
    )

    builder.add_node(
        "compose_brief",
        compose_brief_node,
    )

    builder.add_edge(
        START,
        "normalize_request",
    )

    builder.add_edge(
        "normalize_request",
        "resolve_issuer",
    )

    builder.add_edge(
        "resolve_issuer",
        "retrieve_research",
    )

    builder.add_edge(
        "retrieve_research",
        "retrieve_prices",
    )

    builder.add_edge(
        "retrieve_prices",
        "analyze_relative_value",
    )

    builder.add_edge(
        "analyze_relative_value",
        "validate_evidence",
    )

    builder.add_edge(
        "validate_evidence",
        "compose_brief",
    )

    builder.add_edge(
        "compose_brief",
        END,
    )

    return builder.compile()


graph = build_graph()
