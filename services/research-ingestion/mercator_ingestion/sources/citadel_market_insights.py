from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from mercator_ingestion.models.document import (
    DocumentReference,
    RawDocument,
)
from mercator_ingestion.sources.http_client import PoliteHttpClient


class CitadelMarketInsightsSource:
    SOURCE_NAME = "citadel-securities-market-insights"

    BASE_URL = "https://www.citadelsecurities.com"
    ARCHIVE_URL = (
        "https://www.citadelsecurities.com/"
        "news-and-insights/category/market-insights/"
    )

    def __init__(
        self,
        client: PoliteHttpClient,
    ) -> None:
        self._client = client

    async def discover(
        self,
        maximum_pages: int | None = None,
    ) -> list[DocumentReference]:
        references_by_url: dict[str, DocumentReference] = {}

        page_number = 1

        while maximum_pages is None or page_number <= maximum_pages:
            page_url = (
                self.ARCHIVE_URL
                if page_number == 1
                else urljoin(
                    self.ARCHIVE_URL,
                    f"page/{page_number}/",
                )
            )

            response = await self._client.get(page_url)
            discovered = self._parse_archive_page(response.text)

            if not discovered:
                break

            new_documents = 0

            for reference in discovered:
                canonical_url = str(reference.canonical_url)

                if canonical_url not in references_by_url:
                    references_by_url[canonical_url] = reference
                    new_documents += 1

            if new_documents == 0:
                break

            page_number += 1

        return list(references_by_url.values())

    async def fetch(
        self,
        reference: DocumentReference,
    ) -> RawDocument:
        response = await self._client.get(
            str(reference.canonical_url)
        )

        return RawDocument(
            reference=reference,
            html=response.text,
            fetched_at=datetime.now(timezone.utc),
        )

    def _parse_archive_page(
        self,
        html: str,
    ) -> list[DocumentReference]:
        soup = BeautifulSoup(html, "lxml")

        references: list[DocumentReference] = []
        seen_urls: set[str] = set()

        for anchor in soup.select("a[href]"):
            href = anchor.get("href")

            if not href:
                continue

            absolute_url = urljoin(self.BASE_URL, href)
            parsed = urlparse(absolute_url)

            if parsed.netloc != "www.citadelsecurities.com":
                continue

            if "/news-and-insights/" not in parsed.path:
                continue

            if "/category/" in parsed.path:
                continue

            if "/page/" in parsed.path:
                continue

            title = self._extract_anchor_title(anchor)

            if not title:
                continue

            normalized_url = absolute_url.split("#", maxsplit=1)[0]

            if normalized_url in seen_urls:
                continue

            seen_urls.add(normalized_url)

            source_document_id = hashlib.sha256(
                normalized_url.encode("utf-8")
            ).hexdigest()

            references.append(
                DocumentReference(
                    source_name=self.SOURCE_NAME,
                    source_document_id=source_document_id,
                    canonical_url=normalized_url,
                    title=title,
                    category="Market Insights",
                    metadata={
                        "archive_discovery": True,
                    },
                )
            )

        return references

    @staticmethod
    def _extract_anchor_title(anchor: object) -> str | None:
        get_text = getattr(anchor, "get_text", None)

        if get_text is None:
            return None

        title = re.sub(
            r"\s+",
            " ",
            get_text(" ", strip=True),
        ).strip()

        ignored = {
            "",
            "Read More",
            "View Article",
            "Market Insights",
            "News & Insights",
        }

        if title in ignored:
            parent = getattr(anchor, "parent", None)

            if parent is not None:
                heading = parent.find(
                    ["h1", "h2", "h3", "h4"]
                )

                if heading is not None:
                    title = re.sub(
                        r"\s+",
                        " ",
                        heading.get_text(" ", strip=True),
                    ).strip()

        if not title or title in ignored:
            return None

        return title[:500]


def parse_publication_date(
    value: str | None,
) -> datetime | None:
    if not value:
        return None

    try:
        parsed = date_parser.parse(value)
    except (ValueError, OverflowError):
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed
