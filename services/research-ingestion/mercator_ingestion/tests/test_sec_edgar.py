from __future__ import annotations

from mercator_ingestion.sources.sec_edgar import (
    SecEdgarClient,
)


def test_filing_urls() -> None:
    filing_url, index_url = (
        SecEdgarClient.filing_urls(
            cik="0000320193",
            accession_number="0000320193-24-000123",
            primary_document="aapl-20240928.htm",
        )
    )

    assert filing_url == (
        "https://www.sec.gov/Archives/edgar/data/"
        "320193/000032019324000123/"
        "aapl-20240928.htm"
    )

    assert index_url == (
        "https://www.sec.gov/Archives/edgar/data/"
        "320193/000032019324000123/"
        "0000320193-24-000123-index.html"
    )
