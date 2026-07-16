from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    chunk_id: UUID
    cik: str
    issuer_name: str
    form_type: str
    filing_date: date
    accession_number: str

    section_name: str | None
    chunk_index: int
    chunk_text: str

    filing_url: str
    index_url: str

    lexical_rank: float = 0.0
    semantic_score: float = 0.0
    fused_score: float = 0.0

    citation_label: str


class SearchResponse(BaseModel):
    query: str
    mode: str
    result_count: int
    results: list[SearchResult]


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    cik: str | None = None
    forms: list[str] | None = None
    limit: int = Field(default=10, ge=1, le=50)
