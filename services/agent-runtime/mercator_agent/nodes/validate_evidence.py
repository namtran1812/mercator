from __future__ import annotations

from mercator_agent.state.models import AgentState


def validate_evidence_node(
    state: AgentState,
) -> AgentState:
    evidence = state.get("evidence", [])

    valid = bool(evidence)

    for item in evidence:
        if not item.text.strip():
            valid = False

        if not item.filing_url.startswith(
            "https://www.sec.gov/"
        ):
            valid = False

        if not item.citation_label.strip():
            valid = False

    return {
        "evidence_valid": valid,
    }
