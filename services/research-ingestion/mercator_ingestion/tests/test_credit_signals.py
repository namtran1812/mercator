from __future__ import annotations

from mercator_ingestion.extractors.credit_signals import (
    extract_credit_signals,
)
from mercator_ingestion.extractors.filing_chunks import (
    create_filing_chunks,
)


def test_chunking_creates_overlap() -> None:
    text = " ".join(
        [
            "The company has sufficient liquidity.",
            "Debt increased during the quarter.",
            "Management expects higher interest rates.",
            "The company may need to refinance maturing debt.",
            "Cybersecurity incidents may disrupt operations.",
        ]
        * 20
    )

    chunks = create_filing_chunks(
        text,
        section_name="risk_factors",
        maximum_characters=500,
        overlap_sentences=2,
    )

    assert len(chunks) > 1
    assert all(
        chunk.token_estimate > 0
        for chunk in chunks
    )


def test_credit_signal_extraction() -> None:
    text = (
        "The company may face refinancing risk as "
        "maturing debt becomes due. Higher interest rates "
        "could increase interest expense. A cybersecurity "
        "incident could disrupt operations."
    )

    signals = extract_credit_signals(text)

    values = {
        signal.signal_value
        for signal in signals
    }

    assert "refinancing_risk" in values
    assert "rate_sensitivity" in values
    assert "cybersecurity_risk" in values
