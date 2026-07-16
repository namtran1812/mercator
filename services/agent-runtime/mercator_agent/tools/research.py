from __future__ import annotations

import os

import httpx

from mercator_agent.state.models import EvidenceItem


RESEARCH_SEARCH_URL = os.getenv(
    "RESEARCH_SEARCH_URL",
    "http://localhost:8003",
)


def search_research(
    *,
    question: str,
    cik: str,
    limit: int,
) -> list[EvidenceItem]:
    response = httpx.post(
        f"{RESEARCH_SEARCH_URL}/search",
        json={
            "query": question,
            "cik": cik,
            "forms": [
                "10-K",
                "10-Q",
                "8-K",
            ],
            "limit": limit,
        },
        timeout=30.0,
    )

    response.raise_for_status()
    payload = response.json()

    return [
        EvidenceItem(
            chunk_id=result["chunk_id"],
            issuer_name=result["issuer_name"],
            form_type=result["form_type"],
            filing_date=result["filing_date"],
            accession_number=(
                result["accession_number"]
            ),
            section_name=result["section_name"],
            chunk_index=result["chunk_index"],
            text=result["chunk_text"],
            filing_url=result["filing_url"],
            citation_label=(
                result["citation_label"]
            ),
            fused_score=result["fused_score"],
        )
        for result in payload["results"]
    ]
