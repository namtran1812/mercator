from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class InstrumentVersion(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    version_id: int
    instrument_id: int
    instrument_type: str

    cusip: str | None = None
    isin: str | None = None
    ticker: str | None = None

    issuer_name: str
    coupon_rate: Decimal | None = None
    maturity_date: date | None = None
    rating: str | None = None
    sector: str | None = None
    currency: str

    valid_from: datetime
    valid_to: datetime | None = None

    recorded_from: datetime
    recorded_to: datetime | None = None

    source: str
    source_priority: int
    source_event_id: UUID


class InstrumentSearchResult(BaseModel):
    instrument_id: int
    instrument_type: str
    issuer_name: str

    cusip: str | None = None
    isin: str | None = None
    ticker: str | None = None

    rating: str | None = None
    sector: str | None = None


class FixedIncomeEtfDetails(BaseModel):
    instrument_id: int
    fund_name: str
    benchmark_name: str | None = None
    expense_ratio: Decimal | None = None
    shares_outstanding: Decimal | None = None
    nav: Decimal | None = None

    valid_from: datetime
    valid_to: datetime | None = None

    recorded_from: datetime
    recorded_to: datetime | None = None

    source: str
    source_event_id: UUID


class FixedIncomeEtfConstituent(BaseModel):
    etf_instrument_id: int
    constituent_instrument_id: int
    weight: Decimal
    face_value: Decimal | None = None

    valid_from: datetime
    valid_to: datetime | None = None

    recorded_from: datetime
    recorded_to: datetime | None = None

    source: str
    source_event_id: UUID
