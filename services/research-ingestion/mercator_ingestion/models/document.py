from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class DocumentReference(BaseModel):
    source_name: str
    source_document_id: str
    canonical_url: HttpUrl
    title: str

    author: str | None = None
    series: str | None = None
    category: str | None = None
    published_at: datetime | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)


class RawDocument(BaseModel):
    reference: DocumentReference
    html: str
    fetched_at: datetime


class DocumentSpan(BaseModel):
    span_index: int
    section_heading: str | None = None
    span_text: str
    start_character: int
    end_character: int
    content_hash: str


class ResearchDocument(BaseModel):
    reference: DocumentReference

    summary: str | None = None
    normalized_text: str
    content_hash: str

    fetched_at: datetime
    spans: list[DocumentSpan]

    metadata: dict[str, Any] = Field(default_factory=dict)
