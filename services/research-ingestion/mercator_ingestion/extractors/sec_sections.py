from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

import trafilatura
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class FilingSection:
    name: str
    order: int
    text: str
    start_character: int
    end_character: int
    content_hash: str
    extraction_method: str


SECTION_PATTERNS: list[
    tuple[str, re.Pattern[str], re.Pattern[str] | None]
] = [
    (
        "business",
        re.compile(
            r"\bitem\s+1[.\s:\-]+business\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bitem\s+1a[.\s:\-]+risk factors\b",
            re.IGNORECASE,
        ),
    ),
    (
        "risk_factors",
        re.compile(
            r"\bitem\s+1a[.\s:\-]+risk factors\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bitem\s+1b[.\s:\-]+",
            re.IGNORECASE,
        ),
    ),
    (
        "management_discussion",
        re.compile(
            r"\bitem\s+7[.\s:\-]+"
            r"management[’'`s\s]+discussion",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bitem\s+7a[.\s:\-]+",
            re.IGNORECASE,
        ),
    ),
    (
        "market_risk",
        re.compile(
            r"\bitem\s+7a[.\s:\-]+"
            r"quantitative and qualitative disclosures",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bitem\s+8[.\s:\-]+",
            re.IGNORECASE,
        ),
    ),
    (
        "financial_statements",
        re.compile(
            r"\bitem\s+8[.\s:\-]+"
            r"financial statements",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bitem\s+9[.\s:\-]+",
            re.IGNORECASE,
        ),
    ),
]


def extract_sec_filing_text(html: str) -> str:
    extracted = trafilatura.extract(
        html,
        include_tables=True,
        include_comments=False,
        include_links=False,
        favor_recall=True,
        deduplicate=True,
    )

    if extracted:
        return normalize_text(extracted)

    soup = BeautifulSoup(html, "lxml")

    for element in soup(
        ["script", "style", "noscript"]
    ):
        element.decompose()

    return normalize_text(
        soup.get_text("\n", strip=True)
    )


def extract_sections(
    normalized_text: str,
) -> list[FilingSection]:
    candidates: list[
        tuple[int, str, re.Pattern[str] | None]
    ] = []

    for (
        name,
        start_pattern,
        end_pattern,
    ) in SECTION_PATTERNS:
        matches = list(
            start_pattern.finditer(normalized_text)
        )

        if not matches:
            continue

        # Filings often contain a table of contents and the
        # actual section heading. The last reasonable match
        # is usually the body section rather than the TOC.
        start = matches[-1].start()

        candidates.append(
            (
                start,
                name,
                end_pattern,
            )
        )

    candidates.sort(key=lambda item: item[0])

    sections: list[FilingSection] = []

    for index, (
        start,
        name,
        end_pattern,
    ) in enumerate(candidates):
        next_known_start = (
            candidates[index + 1][0]
            if index + 1 < len(candidates)
            else len(normalized_text)
        )

        end = next_known_start

        if end_pattern is not None:
            match = end_pattern.search(
                normalized_text,
                start + 1,
            )

            if match is not None:
                end = min(end, match.start())

        section_text = normalized_text[start:end].strip()

        if len(section_text) < 250:
            continue

        sections.append(
            FilingSection(
                name=name,
                order=len(sections),
                text=section_text,
                start_character=start,
                end_character=end,
                content_hash=hashlib.sha256(
                    section_text.encode("utf-8")
                ).hexdigest(),
                extraction_method=(
                    "regex-item-boundaries-v1"
                ),
            )
        )

    return sections


def normalize_text(value: str) -> str:
    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in value.splitlines()
    ]

    return "\n".join(
        line
        for line in lines
        if line
    )
