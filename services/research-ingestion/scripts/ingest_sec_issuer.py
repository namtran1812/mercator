from __future__ import annotations

import argparse
import asyncio
import os

from mercator_ingestion.sources.sec_edgar import (
    SecEdgarClient,
    SecEdgarConfig,
)
from mercator_ingestion.storage.sec_postgres import (
    SecFilingStore,
)


async def ingest(
    cik: str,
    forms: set[str],
) -> None:
    user_agent = os.getenv("SEC_USER_AGENT")

    if not user_agent:
        raise RuntimeError(
            "SEC_USER_AGENT is required. Example: "
            "'Mercator Research your-email@example.com'"
        )

    store = SecFilingStore()

    async with SecEdgarClient(
        SecEdgarConfig(
            user_agent=user_agent,
            minimum_delay_seconds=0.2,
        )
    ) as client:
        submissions = await client.get_submissions(cik)

    store.upsert_issuer(submissions)

    inserted = store.upsert_recent_filings(
        submissions,
        allowed_forms=forms,
    )

    print(
        f"Issuer:  {submissions['name']}"
    )
    print(
        f"CIK:     {str(submissions['cik']).zfill(10)}"
    )
    print(
        f"Tickers: {', '.join(submissions.get('tickers', []))}"
    )
    print(
        f"Stored:  {inserted:,} recent filings"
    )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--cik",
        required=True,
        help="SEC CIK, with or without leading zeroes",
    )

    parser.add_argument(
        "--forms",
        nargs="+",
        default=["10-K", "10-Q", "8-K"],
    )

    arguments = parser.parse_args()

    asyncio.run(
        ingest(
            cik=arguments.cik,
            forms=set(arguments.forms),
        )
    )


if __name__ == "__main__":
    main()
