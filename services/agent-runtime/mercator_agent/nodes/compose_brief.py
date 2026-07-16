from __future__ import annotations

import re

from mercator_agent.state.models import (
    AgentState,
    ClientBrief,
)


RISK_TERMS = {
    "liquidity",
    "debt",
    "refinancing",
    "interest rate",
    "cybersecurity",
    "regulatory",
    "supply chain",
}


def shorten(
    value: str,
    maximum: int = 280,
) -> str:
    normalized = re.sub(
        r"\s+",
        " ",
        value,
    ).strip()

    if len(normalized) <= maximum:
        return normalized

    return normalized[: maximum - 1].rstrip() + "…"


def compose_brief_node(
    state: AgentState,
) -> AgentState:
    issuer = state.get("issuer")

    if issuer is None:
        return {
            "errors": [
                *state.get("errors", []),
                "Brief could not be composed "
                "without an issuer.",
            ],
        }

    request = state["request"]
    evidence = state.get("evidence", [])
    relative_value = state.get(
        "relative_value",
        [],
    )

    market_observations = [
        (
            f"Instrument {result.instrument_id}: "
            f"{result.spread_bps:.2f} bp G-spread, "
            f"{result.spread_difference_bps:+.2f} bp "
            f"versus selected peers; "
            f"{result.interpretation}."
        )
        for result in relative_value
    ]

    evidence_summary = [
        (
            f"{item.citation_label}: "
            f"{shorten(item.text)}"
        )
        for item in evidence
    ]

    risks: list[str] = []

    for item in evidence:
        lowered = item.text.lower()

        matched = [
            term
            for term in RISK_TERMS
            if term in lowered
        ]

        if matched:
            risks.append(
                (
                    f"{item.citation_label}: "
                    f"mentions "
                    f"{', '.join(sorted(matched))}."
                )
            )

    summary_parts = [
        (
            f"Mercator reviewed "
            f"{len(evidence)} filing evidence "
            f"passage(s) for {issuer.issuer_name}."
        )
    ]

    if relative_value:
        widest = relative_value[0]

        summary_parts.append(
            (
                f"Instrument {widest.instrument_id} "
                f"has the widest selected-peer "
                f"spread differential at "
                f"{widest.spread_difference_bps:+.2f} bp."
            )
        )

    if not state.get("evidence_valid", False):
        summary_parts.append(
            "The available filing evidence did not "
            "pass every validation check."
        )

    citations = [
        (
            f"{item.citation_label} — "
            f"{item.filing_url}"
        )
        for item in evidence
    ]

    return {
        "brief": ClientBrief(
            issuer_name=issuer.issuer_name,
            question=request.question,
            summary=" ".join(summary_parts),
            market_observations=(
                market_observations
            ),
            evidence_summary=evidence_summary,
            risks=risks[:10],
            citations=citations,
        ),
    }
