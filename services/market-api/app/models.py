from __future__ import annotations
from typing import Literal

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


class RelativeValueRequest(BaseModel):
    instrument_ids: list[int] = Field(
        min_length=2,
        max_length=10_000,
    )

    duration_bucket_width: float = Field(
        default=1.5,
        gt=0.0,
        le=10.0,
    )

    minimum_peer_count: int = Field(
        default=3,
        ge=2,
        le=100,
    )


class RelativeValueOpportunity(BaseModel):
    instrument_id: int

    clean_price: float
    yield_to_maturity: float
    g_spread_bps: float
    modified_duration: float

    peer_count: int
    peer_average_spread_bps: float
    peer_spread_standard_deviation_bps: float

    spread_difference_bps: float
    spread_z_score: float
    duration_adjusted_spread: float

    classification: str
    conviction_score: float


class RelativeValueResponse(BaseModel):
    instrument_count: int
    opportunity_count: int

    average_spread_bps: float
    average_duration: float

    opportunities: list[RelativeValueOpportunity]


class CarryRollRequest(BaseModel):
    instrument_ids: list[int] = Field(
        min_length=2,
        max_length=10_000,
    )

    horizon_months: int = Field(
        default=3,
        ge=1,
        le=24,
    )

    annual_financing_rate: float = Field(
        default=0.045,
        ge=-0.05,
        le=0.25,
    )

    expected_spread_normalization_fraction: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
    )


class CarryRollOpportunity(BaseModel):
    instrument_id: int

    clean_price: float
    yield_to_maturity: float
    g_spread_bps: float
    modified_duration: float
    convexity: float

    horizon_months: int

    coupon_carry_return_percent: float
    financing_cost_return_percent: float
    treasury_roll_down_bps: float
    treasury_roll_return_percent: float

    peer_average_spread_bps: float
    expected_spread_change_bps: float
    spread_normalization_return_percent: float

    expected_total_return_percent: float
    expected_pnl_per_million: float

    classification: str
    conviction_score: float


class CarryRollResponse(BaseModel):
    instrument_count: int
    horizon_months: int
    average_expected_return_percent: float
    opportunities: list[CarryRollOpportunity]


class RiskDecompositionRequest(BaseModel):
    instrument_ids: list[int] = Field(
        min_length=1,
        max_length=10_000,
    )

    position_notional: float = Field(
        default=1_000_000.0,
        gt=0.0,
        le=1_000_000_000.0,
    )


class KeyRateExposure(BaseModel):
    tenor: str
    tenor_years: float
    key_rate_duration: float
    key_rate_dv01: float


class InstrumentRiskDecomposition(BaseModel):
    instrument_id: int
    clean_price: float
    modified_duration: float
    g_spread_bps: float

    position_notional: float
    market_value: float

    aggregate_dv01: float
    cs01: float

    key_rate_exposures: list[KeyRateExposure]


class RiskDecompositionResponse(BaseModel):
    instrument_count: int
    position_notional_per_instrument: float

    total_market_value: float
    total_dv01: float
    total_cs01: float

    portfolio_key_rate_dv01: list[KeyRateExposure]
    instruments: list[InstrumentRiskDecomposition]



class StressScenario(BaseModel):
    treasury_parallel_bps: float = Field(
        default=0.0,
        ge=-1000.0,
        le=1000.0,
    )
    treasury_2y_bps: float = Field(
        default=0.0,
        ge=-1000.0,
        le=1000.0,
    )
    treasury_5y_bps: float = Field(
        default=0.0,
        ge=-1000.0,
        le=1000.0,
    )
    treasury_10y_bps: float = Field(
        default=0.0,
        ge=-1000.0,
        le=1000.0,
    )
    treasury_30y_bps: float = Field(
        default=0.0,
        ge=-1000.0,
        le=1000.0,
    )
    credit_parallel_bps: float = Field(
        default=0.0,
        ge=-2000.0,
        le=2000.0,
    )


class StressRequest(BaseModel):
    instrument_ids: list[int] = Field(
        min_length=1,
        max_length=10_000,
    )
    position_notional: float = Field(
        default=1_000_000.0,
        gt=0.0,
        le=1_000_000_000.0,
    )
    scenario: StressScenario


class StressResult(BaseModel):
    instrument_id: int
    market_value: float
    treasury_pnl: float
    credit_pnl: float
    total_pnl: float


class StressResponse(BaseModel):
    instrument_count: int
    total_market_value: float
    total_treasury_pnl: float
    total_credit_pnl: float
    total_pnl: float
    instruments: list[StressResult]



class HistoricalVarRequest(BaseModel):
    instrument_ids: list[int] = Field(
        min_length=1,
        max_length=10_000,
    )
    position_notional: float = Field(
        default=1_000_000.0,
        gt=0.0,
        le=1_000_000_000.0,
    )
    confidence_level: float = Field(
        default=0.99,
        ge=0.90,
        le=0.999,
    )
    lookback_days: int = Field(
        default=250,
        ge=30,
        le=5_000,
    )
    seed: int = Field(
        default=42,
        ge=0,
        le=2_147_483_647,
    )


class HistoricalVarObservation(BaseModel):
    observation_index: int
    treasury_shock_bps: float
    credit_shock_bps: float
    portfolio_pnl: float


class HistoricalVarInstrumentContribution(BaseModel):
    instrument_id: int
    market_value: float
    dv01: float
    cs01: float
    var_contribution: float


class HistoricalVarResponse(BaseModel):
    instrument_count: int
    observation_count: int
    confidence_level: float
    total_market_value: float
    value_at_risk: float
    expected_shortfall: float
    worst_historical_loss: float
    average_daily_pnl: float
    pnl_volatility: float
    observations: list[HistoricalVarObservation]
    instrument_contributions: list[
        HistoricalVarInstrumentContribution
    ]



class HedgeRecommendationRequest(BaseModel):
    instrument_ids: list[int] = Field(
        min_length=1,
        max_length=10_000,
    )
    position_notional: float = Field(
        default=1_000_000.0,
        gt=0.0,
        le=1_000_000_000.0,
    )
    hedge_ratio: float = Field(
        default=1.0,
        ge=0.0,
        le=1.5,
    )
    include_credit_hedge: bool = True


class TreasuryHedgeRecommendation(BaseModel):
    tenor: str
    tenor_years: float
    portfolio_key_rate_dv01: float
    hedge_instrument_dv01_per_million: float
    recommended_notional: float


class CreditHedgeRecommendation(BaseModel):
    portfolio_cs01: float
    hedge_cs01_per_million: float
    recommended_notional: float
    hedge_instrument: str


class HedgeRecommendationResponse(BaseModel):
    instrument_count: int
    total_market_value: float
    total_dv01: float
    total_cs01: float
    hedge_ratio: float
    treasury_hedges: list[
        TreasuryHedgeRecommendation
    ]
    credit_hedge: CreditHedgeRecommendation | None
    residual_dv01: float
    residual_cs01: float


class PortfolioOptimizationRequest(BaseModel):
    instrument_ids: list[int] = Field(
        min_length=2,
        max_length=10000,
    )

    total_notional: float = Field(
        default=10000000,
        gt=0,
    )

    max_position_percent: float = Field(
        default=0.20,
        gt=0,
        le=1,
    )

    objective: Literal[
        "carry",
        "spread",
        "risk_adjusted"
    ] = "risk_adjusted"


class PortfolioAllocation(BaseModel):
    instrument_id: int
    weight: float
    target_notional: float
    expected_score: float


class PortfolioOptimizationResponse(BaseModel):
    objective: str
    total_notional: float
    allocations: list[
        PortfolioAllocation
    ]



class RiskBudgetOptimizationRequest(BaseModel):
    instrument_ids: list[int] = Field(
        min_length=2,
        max_length=10_000,
    )
    total_notional: float = Field(
        default=10_000_000.0,
        gt=0.0,
        le=10_000_000_000.0,
    )
    max_position_percent: float = Field(
        default=0.20,
        gt=0.0,
        le=1.0,
    )
    max_portfolio_dv01: float = Field(
        default=100_000.0,
        gt=0.0,
    )
    max_portfolio_cs01: float = Field(
        default=100_000.0,
        gt=0.0,
    )
    objective: Literal[
        "carry",
        "spread",
        "risk_adjusted",
    ] = "risk_adjusted"


class RiskBudgetAllocation(BaseModel):
    instrument_id: int
    weight: float
    target_notional: float
    expected_score: float
    dv01: float
    cs01: float


class RiskBudgetOptimizationResponse(BaseModel):
    objective: str
    requested_notional: float
    invested_notional: float
    cash_notional: float
    invested_percent: float
    portfolio_dv01: float
    portfolio_cs01: float
    max_portfolio_dv01: float
    max_portfolio_cs01: float
    allocations: list[RiskBudgetAllocation]


class ScenarioAnalysisRequest(BaseModel):
    instrument_ids: list[int]
    position_notional: float = Field(gt=0)

    treasury_shift_bps: float = 0.0
    spread_shift_bps: float = 0.0

    liquidity_haircut_percent: float = Field(
        default=0.0,
        ge=0,
        le=100,
    )

    downgrade_notches: int = Field(
        default=0,
        ge=0,
        le=5,
    )


class ScenarioInstrumentResult(BaseModel):
    instrument_id: int

    pnl: float

    treasury_pnl: float

    spread_pnl: float

    liquidity_pnl: float

    downgrade_pnl: float


class ScenarioAnalysisResponse(BaseModel):
    total_pnl: float

    treasury_pnl: float

    spread_pnl: float

    liquidity_pnl: float

    downgrade_pnl: float

    instruments: list[ScenarioInstrumentResult]
