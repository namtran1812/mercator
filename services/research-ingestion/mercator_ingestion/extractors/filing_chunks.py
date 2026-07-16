from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class FilingChunk:
    chunk_index: int
    section_name: str | None
    text: str
    start_character: int
    end_character: int
    content_hash: str
    token_estimate: int


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def split_sentences(text: str) -> list[str]:
    return [
        sentence.strip()
        for sentence in re.split(
            r"(?<=[.!?])\s+(?=[A-Z0-9])",
            text,
        )
        if sentence.strip()
    ]


def create_filing_chunks(
    text: str,
    *,
    section_name: str | None,
    start_index: int = 0,
    maximum_characters: int = 1_800,
    overlap_sentences: int = 2,
) -> list[FilingChunk]:
    if maximum_characters < 300:
        raise ValueError(
            "maximum_characters must be at least 300"
        )

    sentences = split_sentences(text)

    if not sentences:
        return []

    chunks: list[FilingChunk] = []
    cursor = 0
    position = 0

    while position < len(sentences):
        selected: list[str] = []
        selected_length = 0
        end_position = position

        while end_position < len(sentences):
            sentence = sentences[end_position]
            added_length = len(sentence)

            if selected:
                added_length += 1

            if (
                selected
                and selected_length + added_length
                > maximum_characters
            ):
                break

            selected.append(sentence)
            selected_length += added_length
            end_position += 1

        chunk_text = " ".join(selected)

        start_character = text.find(
            selected[0],
            cursor,
        )

        if start_character < 0:
            start_character = cursor

        end_character = (
            start_character + len(chunk_text)
        )

        chunks.append(
            FilingChunk(
                chunk_index=start_index + len(chunks),
                section_name=section_name,
                text=chunk_text,
                start_character=start_character,
                end_character=end_character,
                content_hash=hashlib.sha256(
                    chunk_text.encode("utf-8")
                ).hexdigest(),
                token_estimate=estimate_tokens(
                    chunk_text
                ),
            )
        )

        cursor = end_character

        if end_position >= len(sentences):
            break

        position = max(
            position + 1,
            end_position - overlap_sentences,
        )

    return chunks
