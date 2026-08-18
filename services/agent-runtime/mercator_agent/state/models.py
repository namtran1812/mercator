from __future__ import annotations

from datetime import date, datetime
from typing import Any, TypedDict
from uuid import UUID

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    question: str = Field(
        min_length=5,
        max_length=1_000,
    )

    issuer: str | None = None
    cik: str | None = None

    instrument_ids: list[int] = Field(
        default_factory=list,
    )

    maximum_evidence: int = Field(
        default=5,
        ge=1,
        le=20,
    )


class AgentPlan(BaseModel):
    intent: str

    issuer: str | None = None

    needs_research: bool = True
    needs_prices: bool = True
    needs_price_attribution: bool = False

    needs_relative_value: bool = False
    needs_risk: bool = False
    needs_stress: bool = False
    needs_hedge: bool = False
    needs_etf_analytics: bool = False


class SecurityResolution(BaseModel):
    query: str

    instrument_ids: list[int]

    instrument_type: str | None = None
    issuer_name: str | None = None

    result_count: int = 0


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
    convexity: float | None = None

    quality_score: float = 1.0
    quality_status: str

    curve_version: int
    reference_version: int | None = None

    event_time: str | None = None
    price_change: float | None = None

    source_event_id: str | None = None
    calculation_trace_id: str | None = None

    dependency_tenor: str | None = None
    dependency_weight: float | None = None

    source: str = "unknown"


class HistoricalPriceObservation(BaseModel):
    instrument_id: int

    event_time: str

    clean_price: float
    dirty_price: float

    yield_to_maturity: float
    g_spread_bps: float
    modified_duration: float
    convexity: float

    curve_version: int
    reference_version: int

    quality_score: float
    quality_status: str

    model_version: str
    calculation_trace_id: str
    source_event_id: str

    source: str = "clickhouse"


class CurveEventObservation(BaseModel):
    event_time: str
    event_id: str

    curve_version: int
    curve_name: str
    tenor: str

    old_rate: float
    new_rate: float

    source: str
    scenario_name: str

    recorded_at: str


class PriceMoveAttribution(BaseModel):
    instrument_id: int

    curve_version: int
    source_event_id: str | None = None

    dependency_tenor: str | None = None

    old_rate: float | None = None
    new_rate: float | None = None
    rate_change_bps: float | None = None

    previous_clean_price: float | None = None
    current_clean_price: float

    observed_price_change: float | None = None
    observed_return: float | None = None

    modified_duration: float
    convexity: float | None = None

    duration_return: float | None = None
    convexity_return: float | None = None
    estimated_curve_return: float | None = None

    estimated_curve_price_change: float | None = None
    residual_price_change: float | None = None

    explanation: str


class InstrumentProfile(BaseModel):
    instrument_id: int
    instrument_type: str

    issuer_name: str

    cusip: str | None = None
    isin: str | None = None
    ticker: str | None = None

    coupon_rate: float | None = None
    maturity_date: date | None = None

    rating: str | None = None
    sector: str | None = None
    currency: str = "USD"

    reference_version: int | None = None


class RelativeValueResult(BaseModel):
    instrument_id: int

    spread_bps: float

    #
    # Retained for API compatibility.
    #
    peer_average_spread_bps: float
    spread_difference_bps: float

    peer_median_spread_bps: float | None = None
    peer_standard_deviation_bps: float | None = None
    spread_z_score: float | None = None

    peer_count: int = 0

    classification: str = "FAIR"
    confidence: str = "LOW"

    sector: str | None = None
    rating: str | None = None
    maturity_date: date | None = None

    peer_instrument_ids: list[int] = Field(
        default_factory=list
    )

    interpretation: str


class KeyRateExposureSnapshot(BaseModel):
    tenor: str
    tenor_years: float
    key_rate_duration: float
    key_rate_dv01: float


class PortfolioRiskSnapshot(BaseModel):
    instrument_count: int

    position_notional_per_instrument: float

    total_market_value: float
    total_dv01: float
    total_cs01: float

    portfolio_key_rate_dv01: list[
        KeyRateExposureSnapshot
    ]


class TreasuryHedgeSnapshot(BaseModel):
    tenor: str
    tenor_years: float
    portfolio_key_rate_dv01: float
    hedge_instrument_dv01_per_million: float
    recommended_notional: float


class CreditHedgeSnapshot(BaseModel):
    portfolio_cs01: float
    hedge_cs01_per_million: float
    recommended_notional: float
    hedge_instrument: str


class HedgeRecommendationSnapshot(BaseModel):
    instrument_count: int

    total_market_value: float
    total_dv01: float
    total_cs01: float

    hedge_ratio: float

    treasury_hedges: list[
        TreasuryHedgeSnapshot
    ]

    credit_hedge: CreditHedgeSnapshot | None

    residual_dv01: float
    residual_cs01: float


class StressTestInstrumentSnapshot(BaseModel):
    instrument_id: int

    market_value: float

    treasury_pnl: float
    credit_pnl: float
    total_pnl: float


class StressTestSnapshot(BaseModel):
    instrument_count: int

    total_market_value: float

    total_treasury_pnl: float
    total_credit_pnl: float
    total_pnl: float

    instruments: list[
        StressTestInstrumentSnapshot
    ]


class EtfAnalyticsSnapshot(BaseModel):
    instrument_id: int

    fund_name: str
    benchmark_name: str | None

    constituent_count: int
    priced_constituent_count: int

    priced_weight: float
    missing_weight: float

    weighted_clean_price: float
    weighted_yield_to_maturity: float
    weighted_g_spread_bps: float
    weighted_modified_duration: float
    weighted_convexity: float

    reference_nav: float | None
    market_price: float | None

    bid: float | None = None
    ask: float | None = None
    mid: float | None = None

    bid_ask_spread: float | None = None
    bid_ask_spread_bps: float | None = None

    premium_discount_percent: float | None

    quote_source: str | None = None
    quote_timestamp: datetime | None = None
    quote_reliability: float | None = None

    expense_ratio: float | None
    shares_outstanding: float | None


class QualityIssue(BaseModel):
    code: str
    severity: str
    message: str
    instrument_id: int | None = None


class QualityAssessment(BaseModel):
    status: str
    score: float = Field(
        ge=0.0,
        le=1.0,
    )

    instrument_ids: list[int] = Field(
        default_factory=list
    )

    issues: list[QualityIssue] = Field(
        default_factory=list
    )


class ClientBrief(BaseModel):
    issuer_name: str
    question: str

    summary: str

    market_observations: list[str]
    evidence_summary: list[str]
    risks: list[str]

    citations: list[str]


class AgentState(
    TypedDict,
    total=False,
):
    request: AgentRequest
    plan: AgentPlan

    issuer: IssuerResolution
    security: SecurityResolution

    evidence: list[
        EvidenceItem
    ]

    prices: list[
        PriceObservation
    ]

    quality: QualityAssessment

    price_attribution: list[
        PriceMoveAttribution
    ]

    relative_value: list[
        RelativeValueResult
    ]

    risk: PortfolioRiskSnapshot
    hedge: HedgeRecommendationSnapshot
    stress: StressTestSnapshot
    etf_analytics: EtfAnalyticsSnapshot

    errors: list[str]

    evidence_valid: bool

    brief: ClientBrief

    diagnostics: dict[
        str,
        Any,
    ]


class AgentQueryResponse(BaseModel):
    brief: ClientBrief | None = None

    plan: AgentPlan | None = None
    security: SecurityResolution | None = None

    prices: list[PriceObservation] = Field(
        default_factory=list
    )

    quality: QualityAssessment | None = None

    price_attribution: list[
        PriceMoveAttribution
    ] = Field(
        default_factory=list
    )

    relative_value: list[RelativeValueResult] = Field(
        default_factory=list
    )

    risk: PortfolioRiskSnapshot | None = None
    hedge: HedgeRecommendationSnapshot | None = None
    stress: StressTestSnapshot | None = None
    etf_analytics: EtfAnalyticsSnapshot | None = None

    evidence: list[EvidenceItem] = Field(
        default_factory=list
    )

    diagnostics: dict[str, Any] = Field(
        default_factory=dict
    )

    errors: list[str] = Field(
        default_factory=list
    )


class ReplayReferenceSnapshot(BaseModel):
    instrument_id: int
    reference_version: int

    issuer_name: str
    instrument_type: str

    coupon_rate: float | None = None
    maturity_date: date | None = None
    rating: str | None = None
    sector: str | None = None
    currency: str = "USD"


class CurveReplayState(BaseModel):
    curve_version: int
    valuation_date: str
    curve_points: list[dict[str, float]] = Field(
        default_factory=list
    )
    curve_events: list[CurveEventObservation] = Field(
        default_factory=list
    )


class ReplaySnapshot(BaseModel):
    instrument_id: int
    requested_as_of: str

    price: HistoricalPriceObservation
    reference: ReplayReferenceSnapshot

    curve_version: int
    curve_events: list[CurveEventObservation] = Field(
        default_factory=list
    )

    calculation_trace_id: str
    source_event_id: str

    replay_status: str = "PROVENANCE_ONLY"

    replayed_clean_price: float | None = None
    replayed_dirty_price: float | None = None

    clean_price_error: float | None = None
    dirty_price_error: float | None = None

    replay_absolute_tolerance: float | None = None

    explanation: str
