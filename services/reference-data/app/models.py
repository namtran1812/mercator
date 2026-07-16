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
