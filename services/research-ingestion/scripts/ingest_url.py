from __future__ import annotations

import argparse
import asyncio
import hashlib
import os

import httpx
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from mercator_ingestion.extractors.article import extract_article
from mercator_ingestion.models.document import (
    DocumentReference,
    RawDocument,
)
from mercator_ingestion.sources.http_client import PoliteHttpClient
from mercator_ingestion.storage.postgres import ResearchDocumentStore


def fallback_title(html: str, url: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    for selector in (
        'meta[property="og:title"]',
        'meta[name="twitter:title"]',
        "title",
        "h1",
    ):
        element = soup.select_one(selector)

        if element is None:
            continue

        value = element.get("content") or element.get_text(
            " ",
            strip=True,
        )

        if value:
            return str(value).strip()

    return url


async def ingest(url: str) -> None:
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
        try:
            response = await client.get(url)
        except httpx.HTTPStatusError as error:
            if error.response.status_code == 403:
                print(
                    "The source denied automated access with HTTP 403."
                )
                print(
                    "Mercator will store this source as link-and-metadata "
                    "only and will not bypass access controls."
                )
                return

            raise

        reference = DocumentReference(
            source_name="manual-public-research",
            source_document_id=hashlib.sha256(
                url.encode("utf-8")
            ).hexdigest(),
            canonical_url=url,
            title=fallback_title(response.text, url),
            category="Public Market Research",
            metadata={
                "discovery_method": "manual_url",
            },
        )

        document_id = store.upsert_discovered(reference)

        raw = RawDocument(
            reference=reference,
            html=response.text,
            fetched_at=datetime.now(timezone.utc),
        )

        try:
            document = extract_article(raw)
            store.save_extracted(document_id, document)
        except Exception as error:
            store.mark_failure(document_id, str(error))
            raise

        print(f"Ingested: {document.reference.title}")
        print(f"URL:      {document.reference.canonical_url}")
        print(f"Spans:    {len(document.spans)}")
        print(f"SHA-256:  {document.content_hash}")


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "url",
        help="Public article URL to ingest",
    )

    arguments = parser.parse_args()
    asyncio.run(ingest(arguments.url))


if __name__ == "__main__":
    main()
