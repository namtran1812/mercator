from __future__ import annotations

from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from mercator_agent.nodes.attribute_price_move import (
    attribute_price_move_node,
)

from mercator_agent.nodes.analyze_relative_value import (
    analyze_relative_value_node,
)

from mercator_agent.nodes.analyze_risk import (
    analyze_risk_node,
)

from mercator_agent.nodes.analyze_hedge import (
    analyze_hedge_node,
)

from mercator_agent.nodes.analyze_stress import (
    analyze_stress_node,
)

from mercator_agent.nodes.analyze_etf import (
    analyze_etf_node,
)

from mercator_agent.nodes.compose_brief import (
    compose_brief_node,
)

from mercator_agent.nodes.normalize_request import (
    normalize_request_node,
)

from mercator_agent.nodes.plan_query import (
    plan_query_node,
)

from mercator_agent.nodes.resolve_issuer import (
    resolve_issuer_node,
)

from mercator_agent.nodes.resolve_security import (
    resolve_security_node,
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

from mercator_agent.state.models import (
    AgentState,
)


def build_graph():
    builder = StateGraph(
        AgentState
    )

    builder.add_node(
        "normalize_request",
        normalize_request_node,
    )

    builder.add_node(
        "plan_query",
        plan_query_node,
    )

    builder.add_node(
        "resolve_issuer",
        resolve_issuer_node,
    )

    builder.add_node(
        "resolve_security",
        resolve_security_node,
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
        "attribute_price_move",
        attribute_price_move_node,
    )

    builder.add_node(
        "analyze_relative_value",
        analyze_relative_value_node,
    )

    builder.add_node(
        "analyze_risk",
        analyze_risk_node,
    )

    builder.add_node(
        "analyze_hedge",
        analyze_hedge_node,
    )

    builder.add_node(
        "analyze_stress",
        analyze_stress_node,
    )

    builder.add_node(
        "analyze_etf",
        analyze_etf_node,
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
        "plan_query",
    )

    builder.add_edge(
        "plan_query",
        "resolve_issuer",
    )

    builder.add_edge(
        "resolve_issuer",
        "resolve_security",
    )

    builder.add_edge(
        "resolve_security",
        "retrieve_research",
    )

    builder.add_edge(
        "retrieve_research",
        "retrieve_prices",
    )

    builder.add_edge(
        "retrieve_prices",
        "attribute_price_move",
    )

    builder.add_edge(
        "attribute_price_move",
        "analyze_relative_value",
    )

    builder.add_edge(
        "analyze_relative_value",
        "analyze_risk",
    )

    builder.add_edge(
        "analyze_risk",
        "analyze_hedge",
    )

    builder.add_edge(
        "analyze_hedge",
        "analyze_stress",
    )

    builder.add_edge(
        "analyze_stress",
        "analyze_etf",
    )

    builder.add_edge(
        "analyze_etf",
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
