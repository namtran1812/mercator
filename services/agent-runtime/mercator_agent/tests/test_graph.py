from __future__ import annotations

from unittest.mock import patch

from mercator_agent.graph import graph
from mercator_agent.state.models import (
    EvidenceItem,
    IssuerResolution,
    PriceObservation,
)


def test_graph_builds_brief() -> None:
    issuer = IssuerResolution(
        cik="0000320193",
        issuer_name="Apple Inc.",
        tickers=["AAPL"],
    )

    evidence = [
        EvidenceItem(
            chunk_id=(
                "00000000-0000-0000-0000-000000000001"
            ),
            issuer_name="Apple Inc.",
            form_type="10-K",
            filing_date="2025-09-27",
            accession_number="example",
            section_name="risk_factors",
            chunk_index=0,
            text=(
                "The company discusses liquidity, debt, "
                "interest rate risk, and cybersecurity."
            ),
            filing_url=(
                "https://www.sec.gov/example"
            ),
            citation_label=(
                "Apple Inc. 10-K 2025-09-27 "
                "§risk_factors chunk 0"
            ),
            fused_score=0.03,
        )
    ]

    prices = [
        PriceObservation(
            instrument_id=1,
            clean_price=99.0,
            dirty_price=100.0,
            yield_to_maturity=0.05,
            g_spread_bps=100.0,
            modified_duration=4.0,
            quality_score=0.95,
            quality_status="VALID",
            curve_version=2,
            reference_version=1,
        ),
        PriceObservation(
            instrument_id=2,
            clean_price=98.0,
            dirty_price=99.0,
            yield_to_maturity=0.06,
            g_spread_bps=180.0,
            modified_duration=5.0,
            quality_score=0.95,
            quality_status="VALID",
            curve_version=2,
            reference_version=1,
        ),
    ]

    with (
        patch(
            "mercator_agent.nodes.resolve_issuer."
            "resolve_issuer",
            return_value=issuer,
        ),
        patch(
            "mercator_agent.nodes.retrieve_research."
            "search_research",
            return_value=evidence,
        ),
        patch(
            "mercator_agent.nodes.retrieve_prices."
            "latest_prices",
            return_value=prices,
        ),
    ):
        result = graph.invoke(
            {
                "request": {
                    "question": (
                        "Assess the issuer's credit risk"
                    ),
                    "issuer": "Apple",
                    "instrument_ids": [1, 2],
                    "maximum_evidence": 5,
                },
                "errors": [],
            }
        )

    assert result["brief"].issuer_name == "Apple Inc."
    assert result["brief"].citations
    assert result["evidence_valid"] is True


def test_request_dictionary_is_normalized() -> None:
    from mercator_agent.nodes.normalize_request import (
        normalize_request_node,
    )
    from mercator_agent.state.models import AgentRequest

    result = normalize_request_node(
        {
            "request": {
                "question": "Assess issuer liquidity risk",
                "issuer": "Apple",
                "instrument_ids": [1, 2],
                "maximum_evidence": 5,
            }
        }
    )

    assert isinstance(
        result["request"],
        AgentRequest,
    )

    assert result["request"].issuer == "Apple"
    assert result["request"].instrument_ids == [1, 2]
