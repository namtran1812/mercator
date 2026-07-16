from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import trafilatura
from bs4 import BeautifulSoup

from mercator_ingestion.models.document import (
    DocumentReference,
    DocumentSpan,
    RawDocument,
    ResearchDocument,
)
from mercator_ingestion.sources.citadel_market_insights import (
    parse_publication_date,
)


@dataclass(frozen=True)
class ExtractedMetadata:
    title: str | None
    author: str | None
    published_at: datetime | None
    series: str | None
    description: str | None


def extract_article(
    raw: RawDocument,
    *,
    maximum_span_characters: int = 1_500,
) -> ResearchDocument:
    metadata = _extract_metadata(raw.html)

    extracted_text = trafilatura.extract(
        raw.html,
        include_comments=False,
        include_tables=True,
        include_links=False,
        favor_precision=True,
        deduplicate=True,
    )

    if not extracted_text:
        raise ValueError(
            f"Unable to extract article text from "
            f"{raw.reference.canonical_url}"
        )

    normalized_text = _normalize_text(extracted_text)

    content_hash = hashlib.sha256(
        normalized_text.encode("utf-8")
    ).hexdigest()

    reference = raw.reference.model_copy(
        update={
            "title": metadata.title or raw.reference.title,
            "author": metadata.author or raw.reference.author,
            "series": metadata.series or raw.reference.series,
            "published_at": (
                metadata.published_at
                or raw.reference.published_at
            ),
        }
    )

    spans = _create_spans(
        normalized_text,
        maximum_span_characters,
    )

    return ResearchDocument(
        reference=reference,
        summary=metadata.description,
        normalized_text=normalized_text,
        content_hash=content_hash,
        fetched_at=raw.fetched_at,
        spans=spans,
        metadata={
            **raw.reference.metadata,
            "extractor": "trafilatura",
            "span_count": len(spans),
        },
    )


def _extract_metadata(html: str) -> ExtractedMetadata:
    soup = BeautifulSoup(html, "lxml")

    json_ld = _read_json_ld(soup)

    title = (
        _meta_content(soup, "property", "og:title")
        or _meta_content(soup, "name", "twitter:title")
        or _json_ld_value(json_ld, "headline")
    )

    description = (
        _meta_content(
            soup,
            "property",
            "og:description",
        )
        or _meta_content(
            soup,
            "name",
            "description",
        )
        or _json_ld_value(
            json_ld,
            "description",
        )
    )

    author = _extract_author(json_ld, soup)

    published_value = (
        _meta_content(
            soup,
            "property",
            "article:published_time",
        )
        or _json_ld_value(
            json_ld,
            "datePublished",
        )
    )

    series = _extract_series(soup)

    return ExtractedMetadata(
        title=_normalize_optional(title),
        author=_normalize_optional(author),
        published_at=parse_publication_date(
            published_value
        ),
        series=_normalize_optional(series),
        description=_normalize_optional(description),
    )


def _read_json_ld(
    soup: BeautifulSoup,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for script in soup.select(
        'script[type="application/ld+json"]'
    ):
        if not script.string:
            continue

        try:
            value = json.loads(script.string)
        except json.JSONDecodeError:
            continue

        if isinstance(value, dict):
            results.append(value)
        elif isinstance(value, list):
            results.extend(
                item
                for item in value
                if isinstance(item, dict)
            )

    return results


def _json_ld_value(
    documents: list[dict[str, Any]],
    key: str,
) -> str | None:
    for document in documents:
        value = document.get(key)

        if isinstance(value, str):
            return value

        graph = document.get("@graph")

        if isinstance(graph, list):
            for item in graph:
                if not isinstance(item, dict):
                    continue

                nested = item.get(key)

                if isinstance(nested, str):
                    return nested

    return None


def _extract_author(
    documents: list[dict[str, Any]],
    soup: BeautifulSoup,
) -> str | None:
    for document in documents:
        author = document.get("author")

        if isinstance(author, dict):
            name = author.get("name")

            if isinstance(name, str):
                return name

        if isinstance(author, list):
            names = [
                entry.get("name")
                for entry in author
                if isinstance(entry, dict)
                and isinstance(entry.get("name"), str)
            ]

            if names:
                return ", ".join(names)

    author_meta = soup.find(
        "meta",
        attrs={"name": "author"},
    )

    if author_meta:
        value = author_meta.get("content")

        if isinstance(value, str):
            return value

    return None


def _extract_series(
    soup: BeautifulSoup,
) -> str | None:
    page_text = soup.get_text(" ", strip=True)

    match = re.search(
        r"Series:\s*([A-Za-z0-9 &’'\-]+)",
        page_text,
        flags=re.IGNORECASE,
    )

    return match.group(1).strip() if match else None


def _meta_content(
    soup: BeautifulSoup,
    attribute: str,
    value: str,
) -> str | None:
    tag = soup.find(
        "meta",
        attrs={attribute: value},
    )

    if not tag:
        return None

    content = tag.get("content")
    return content if isinstance(content, str) else None


def _normalize_optional(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    normalized = re.sub(r"\s+", " ", value).strip()
    return normalized or None


def _normalize_text(value: str) -> str:
    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in value.splitlines()
    ]

    return "\n".join(
        line
        for line in lines
        if line
    )


def _create_spans(
    text: str,
    maximum_characters: int,
) -> list[DocumentSpan]:
    paragraphs = text.splitlines()

    spans: list[DocumentSpan] = []
    current_parts: list[str] = []
    current_length = 0
    current_start = 0
    cursor = 0

    def flush() -> None:
        nonlocal current_parts
        nonlocal current_length
        nonlocal current_start

        if not current_parts:
            return

        span_text = "\n".join(current_parts)

        spans.append(
            DocumentSpan(
                span_index=len(spans),
                span_text=span_text,
                start_character=current_start,
                end_character=current_start + len(span_text),
                content_hash=hashlib.sha256(
                    span_text.encode("utf-8")
                ).hexdigest(),
            )
        )

        current_parts = []
        current_length = 0

    for paragraph in paragraphs:
        added_length = len(paragraph)

        if current_parts:
            added_length += 1

        if (
            current_parts
            and current_length + added_length
            > maximum_characters
        ):
            flush()
            current_start = cursor

        if not current_parts:
            current_start = cursor

        current_parts.append(paragraph)
        current_length += added_length
        cursor += len(paragraph) + 1

    flush()
    return spans
