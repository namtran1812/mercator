from __future__ import annotations

from datetime import date
from typing import Any, TypedDict
from uuid import UUID

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    question: str = Field(min_length=5, max_length=1_000)
    issuer: str | None = None
    cik: str | None = None
    instrument_ids: list[int] = Field(default_factory=list)
    maximum_evidence: int = Field(default=5, ge=1, le=20)


class IssuerResolution(BaseModel):
    cik: str
    issuer_name: str
    tickers: list[str]


class EvidenceItem(BaseModel):
    chunk_id: UUID
    issuer_name: str
    form_type: str
    filing_date: date
    accession_number: str
    section_name: str | None
    chunk_index: int
    text: str
    filing_url: str
    citation_label: str
    fused_score: float


class PriceObservation(BaseModel):
    instrument_id: int
    clean_price: float
    dirty_price: float
    yield_to_maturity: float
    g_spread_bps: float
    modified_duration: float
    quality_score: float
    quality_status: str
    curve_version: int
    reference_version: int


class RelativeValueResult(BaseModel):
    instrument_id: int
    spread_bps: float
    peer_average_spread_bps: float
    spread_difference_bps: float
    interpretation: str


class ClientBrief(BaseModel):
    issuer_name: str
    question: str
    summary: str
    market_observations: list[str]
    evidence_summary: list[str]
    risks: list[str]
    citations: list[str]


class AgentState(TypedDict, total=False):
    request: AgentRequest

    issuer: IssuerResolution
    evidence: list[EvidenceItem]
    prices: list[PriceObservation]
    relative_value: list[RelativeValueResult]

    errors: list[str]
    evidence_valid: bool

    brief: ClientBrief

    diagnostics: dict[str, Any]
