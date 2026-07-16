from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class LatestBondPrice(BaseModel):
    instrument_id: int

    clean_price: float
    dirty_price: float
    yield_to_maturity: float
    g_spread_bps: float
    modified_duration: float
    convexity: float

    quality_score: float
    quality_status: str

    curve_version: int
    reference_version: int

    event_time: datetime


class MarketSummary(BaseModel):
    instrument_count: int
    average_clean_price: float
    average_yield_to_maturity: float
    average_g_spread_bps: float
    widest_instrument_id: int | None
    widest_g_spread_bps: float | None
