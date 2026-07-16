from __future__ import annotations

import argparse
import asyncio
import os

from mercator_ingestion.extractors.article import (
    extract_article,
)
from mercator_ingestion.sources.citadel_market_insights import (
    CitadelMarketInsightsSource,
)
from mercator_ingestion.sources.http_client import (
    PoliteHttpClient,
)
from mercator_ingestion.storage.postgres import (
    ResearchDocumentStore,
)


async def run(
    maximum_pages: int,
    maximum_documents: int,
) -> None:
    user_agent = os.getenv(
        "MERCATOR_RESEARCH_USER_AGENT",
        (
            "MercatorResearchBot/0.1 "
            "(educational portfolio project; "
            "contact: namtran1812@users.noreply.github.com)"
        ),
    )

    store = ResearchDocumentStore()

    async with PoliteHttpClient(
        user_agent=user_agent,
        minimum_delay_seconds=2.0,
    ) as client:
        source = CitadelMarketInsightsSource(client)

        references = await source.discover(
            maximum_pages=maximum_pages
        )

        references = references[:maximum_documents]

        print(
            f"Discovered {len(references):,} "
            "candidate documents."
        )

        extracted = 0
        failed = 0

        for index, reference in enumerate(
            references,
            start=1,
        ):
            print(
                f"[{index}/{len(references)}] "
                f"{reference.title}"
            )

            document_id = store.upsert_discovered(
                reference
            )

            try:
                raw = await source.fetch(reference)
                document = extract_article(raw)
                store.save_extracted(
                    document_id,
                    document,
                )
                extracted += 1
            except Exception as error:
                store.mark_failure(
                    document_id,
                    str(error),
                )
                failed += 1
                print(f"  FAILED: {error}")

        print(f"Extracted: {extracted:,}")
        print(f"Failed:    {failed:,}")


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--maximum-pages",
        type=int,
        default=2,
    )

    parser.add_argument(
        "--maximum-documents",
        type=int,
        default=20,
    )

    arguments = parser.parse_args()

    asyncio.run(
        run(
            maximum_pages=arguments.maximum_pages,
            maximum_documents=arguments.maximum_documents,
        )
    )


if __name__ == "__main__":
    main()
