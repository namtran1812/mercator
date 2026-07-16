from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class RFQStatus(str, Enum):
    REQUESTED = "REQUESTED"
    QUOTING = "QUOTING"
    QUOTED = "QUOTED"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class QuoteStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class RFQRequest(BaseModel):
    account_id: UUID = UUID(
        "00000000-0000-0000-0000-000000000101"
    )
    instrument_id: int = Field(gt=0)
    side: Side
    quantity: float = Field(gt=0)
    client: str = Field(
        min_length=1,
        max_length=200,
    )


class RFQ(BaseModel):
    id: UUID
    account_id: UUID
    instrument_id: int
    side: Side
    quantity: float
    client: str
    requested_at: datetime
    status: RFQStatus


class DealerQuote(BaseModel):
    id: UUID
    rfq_id: UUID
    dealer: str
    price: float
    spread_bps: float
    latency_ms: int
    inventory_adjustment_bps: float
    size_adjustment_bps: float
    quoted_at: datetime
    expires_at: datetime | None
    quote_status: QuoteStatus


class RFQDetail(BaseModel):
    rfq: RFQ
    quotes: list[DealerQuote]


class ExecuteQuoteRequest(BaseModel):
    quote_id: UUID


class Execution(BaseModel):
    id: UUID
    rfq_id: UUID
    quote_id: UUID
    account_id: UUID
    instrument_id: int
    side: Side
    client: str
    dealer: str
    price: float
    quantity: float
    executed_at: datetime
    execution_status: str


class ExecutionResponse(BaseModel):
    execution: Execution
    rejected_quote_count: int


class Position(BaseModel):
    account_id: UUID
    instrument_id: int
    face_value: float
    average_cost: float
    realized_pnl: float
    updated_at: datetime


class AccountSummary(BaseModel):
    account_id: UUID
    account_name: str
    cash_balance: float
    position_count: int
    total_face_value: float
    positions: list[Position]


class LivePositionRisk(BaseModel):
    account_id: UUID
    instrument_id: int

    face_value: float
    average_cost: float
    current_clean_price: float

    cost_basis: float
    market_value: float

    unrealized_pnl: float
    realized_pnl: float
    total_pnl: float

    yield_to_maturity: float
    g_spread_bps: float
    modified_duration: float
    convexity: float
    dv01: float

    quality_status: str
    curve_version: int
    reference_version: int


class LiveAccountRisk(BaseModel):
    account_id: UUID
    account_name: str
    cash_balance: float

    position_count: int
    total_face_value: float
    total_cost_basis: float
    total_market_value: float

    total_unrealized_pnl: float
    total_realized_pnl: float
    total_pnl: float

    weighted_yield_to_maturity: float
    weighted_g_spread_bps: float
    weighted_modified_duration: float
    weighted_convexity: float
    total_dv01: float

    net_liquidation_value: float

    positions: list[LivePositionRisk]
