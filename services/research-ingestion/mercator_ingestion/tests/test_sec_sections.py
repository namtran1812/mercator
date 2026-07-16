from __future__ import annotations

from mercator_ingestion.extractors.sec_sections import (
    extract_sections,
    normalize_text,
)


def test_extract_item_sections() -> None:
    text = normalize_text(
        """
        ITEM 1. BUSINESS
        This business section describes the company,
        its markets, products, customers, and operations.
        The company operates across several major markets.
        Additional business discussion continues here for
        enough characters to qualify as a valid section.

        ITEM 1A. RISK FACTORS
        The company faces credit risk, market risk,
        supply-chain risk, regulatory risk, litigation,
        cybersecurity threats, and macroeconomic uncertainty.
        These risks could materially affect future results
        and the company's ability to meet obligations.

        ITEM 1B. UNRESOLVED STAFF COMMENTS
        None.

        ITEM 7. MANAGEMENT'S DISCUSSION
        Management discusses revenue, operating income,
        liquidity, capital resources, cash flows, debt,
        and expected future financing requirements.
        Additional discussion continues here so the section
        is sufficiently long for extraction.

        ITEM 7A. QUANTITATIVE AND QUALITATIVE DISCLOSURES
        Interest-rate and foreign-exchange exposures are
        discussed in this section with sensitivity analysis.

        ITEM 8. FINANCIAL STATEMENTS
        Financial statements begin here.
        """
    )

    sections = extract_sections(text)

    names = {
        section.name
        for section in sections
    }

    assert "risk_factors" in names
    assert "management_discussion" in names
