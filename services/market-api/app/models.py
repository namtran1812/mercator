from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


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


class PriceHistoryPoint(BaseModel):
    event_time: datetime
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
    model_version: str
    calculation_trace_id: str
    source_event_id: str


class MarketSummary(BaseModel):
    instrument_count: int
    average_clean_price: float
    average_yield_to_maturity: float
    average_g_spread_bps: float
    widest_instrument_id: int | None
    widest_g_spread_bps: float | None


class ScenarioRequest(BaseModel):
    instrument_ids: list[int] = Field(
        min_length=1,
        max_length=1_000,
    )

    treasury_shock_bps: float = Field(
        default=0.0,
        ge=-500.0,
        le=500.0,
    )

    credit_spread_shock_bps: float = Field(
        default=0.0,
        ge=-1_000.0,
        le=1_000.0,
    )

    position_face_value: float = Field(
        default=1_000_000.0,
        gt=0.0,
        le=1_000_000_000.0,
    )


class ScenarioResult(BaseModel):
    instrument_id: int

    base_clean_price: float
    shocked_clean_price: float
    price_change: float
    price_change_percent: float

    base_yield: float
    shocked_yield: float

    base_spread_bps: float
    shocked_spread_bps: float

    modified_duration: float
    convexity: float

    estimated_pnl: float


class ScenarioResponse(BaseModel):
    treasury_shock_bps: float
    credit_spread_shock_bps: float
    position_face_value: float

    instrument_count: int
    total_estimated_pnl: float

    results: list[ScenarioResult]


class PortfolioPosition(BaseModel):
    instrument_id: int
    face_value: float = Field(
        gt=0.0,
        le=1_000_000_000.0,
    )


class PortfolioRiskRequest(BaseModel):
    positions: list[PortfolioPosition] = Field(
        min_length=1,
        max_length=10_000,
    )


class PositionRisk(BaseModel):
    instrument_id: int
    face_value: float

    clean_price: float
    market_value: float

    yield_to_maturity: float
    g_spread_bps: float
    modified_duration: float
    convexity: float

    dv01: float
    convexity_contribution: float

    market_value_weight: float


class PortfolioRiskResponse(BaseModel):
    position_count: int
    total_face_value: float
    total_market_value: float

    weighted_yield_to_maturity: float
    weighted_g_spread_bps: float
    weighted_modified_duration: float
    weighted_convexity: float

    total_dv01: float
    total_convexity_contribution: float

    positions: list[PositionRisk]


class ReplayScenario(BaseModel):
    scenario_name: str
    event_count: int
    first_event_time: datetime
    last_event_time: datetime


class ReplayRequest(BaseModel):
    scenario_name: str
    speed: float = Field(
        default=10.0,
        gt=0.0,
        le=1_000.0,
    )


class ReplayScenario(BaseModel):
    scenario_name: str
    event_count: int
    first_event_time: datetime
    last_event_time: datetime


class ReplayRequest(BaseModel):
    scenario_name: str
    speed: float = Field(
        default=10.0,
        gt=0.0,
        le=1_000.0,
    )
