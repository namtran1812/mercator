from __future__ import annotations

import argparse
import asyncio
import hashlib
import os

from mercator_ingestion.extractors.sec_sections import (
    extract_sec_filing_text,
    extract_sections,
)
from mercator_ingestion.sources.sec_edgar import (
    SecEdgarClient,
    SecEdgarConfig,
)
from mercator_ingestion.storage.sec_postgres import (
    SecDocumentStore,
)


async def ingest(
    *,
    cik: str,
    forms: set[str],
    limit: int,
) -> None:
    user_agent = os.getenv("SEC_USER_AGENT")

    if not user_agent:
        raise RuntimeError(
            "SEC_USER_AGENT is required"
        )

    store = SecDocumentStore()

    filings = store.pending_filings(
        cik=cik,
        forms=forms,
        limit=limit,
    )

    print(f"Selected {len(filings)} filing(s).")

    async with SecEdgarClient(
        SecEdgarConfig(
            user_agent=user_agent,
            minimum_delay_seconds=0.2,
        )
    ) as client:
        for index, filing in enumerate(
            filings,
            start=1,
        ):
            filing_id = filing["filing_id"]
            filing_url = str(filing["filing_url"])

            print(
                f"[{index}/{len(filings)}] "
                f"{filing['form_type']} "
                f"{filing['filing_date']}"
            )

            try:
                html = await client.get_filing_document(
                    filing_url
                )

                normalized_text = (
                    extract_sec_filing_text(html)
                )

                if len(normalized_text) < 1_000:
                    raise ValueError(
                        "Extracted filing text is unexpectedly short"
                    )

                content_hash = hashlib.sha256(
                    normalized_text.encode("utf-8")
                ).hexdigest()

                sections = extract_sections(
                    normalized_text
                )

                store.save_document(
                    filing_id=filing_id,
                    normalized_text=normalized_text,
                    content_hash=content_hash,
                    sections=sections,
                )

                print(
                    f"  Characters: {len(normalized_text):,}"
                )
                print(
                    f"  Sections:   {len(sections)}"
                )

            except Exception as error:
                store.mark_failure(
                    filing_id=filing_id,
                    error=str(error),
                )
                print(f"  FAILED: {error}")


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--cik",
        required=True,
    )

    parser.add_argument(
        "--forms",
        nargs="+",
        default=["10-K", "10-Q"],
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=2,
    )

    arguments = parser.parse_args()

    asyncio.run(
        ingest(
            cik=arguments.cik,
            forms=set(arguments.forms),
            limit=arguments.limit,
        )
    )


if __name__ == "__main__":
    main()
