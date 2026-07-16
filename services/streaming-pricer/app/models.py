from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CurveUpdate(BaseModel):
    event_id: str
    event_time: datetime
    curve_version: int
    tenor: str
    old_rate: float
    new_rate: float


class StreamingPrice(BaseModel):
    instrument_id: int

    clean_price: float
    dirty_price: float
    yield_to_maturity: float
    g_spread_bps: float
    modified_duration: float
    convexity: float

    curve_version: int
    quality_status: str
    event_time: datetime

    price_change: float
    source_event_id: str


class CurveSimulationConfig(BaseModel):
    interval_seconds: float = Field(
        default=2.0,
        gt=0.0,
    )
    volatility_bps: float = Field(
        default=2.0,
        gt=0.0,
    )
