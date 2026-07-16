from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .kafka import (
    KafkaPublisher,
    RFQ_REQUESTED_TOPIC,
    TRADE_EXECUTED_TOPIC,
)
from .models import (
    AccountSummary,
    LiveAccountRisk,
    DealerAnalytics,
    DealerQuote,
    Position,
    ExecuteQuoteRequest,
    Execution,
    ExecutionResponse,
    RFQ,
    RFQDetail,
    RFQRequest,
    RfqAnalyticsSummary,
)
from .repository import RFQRepository
from .metrics import (
    RFQS_CREATED,
    TRADES_EXECUTED,
    metrics_middleware,
    metrics_response,
)
from .ledger import apply_execution_to_ledger
from .live_risk import calculate_live_account_risk


app = FastAPI(
    title="Mercator RFQ API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

repository = RFQRepository()
publisher = KafkaPublisher()


app.middleware("http")(
    metrics_middleware
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/rfqs",
    response_model=RFQ,
    status_code=201,
)
def create_rfq(
    request: RFQRequest,
) -> RFQ:
    rfq_id = uuid4()
    requested_at = datetime.now(
        timezone.utc
    )

    row = repository.create_rfq(
        rfq_id=rfq_id,
        account_id=request.account_id,
        instrument_id=request.instrument_id,
        side=request.side.value,
        quantity=request.quantity,
        client=request.client,
        requested_at=requested_at,
    )

    RFQS_CREATED.labels(
        side=request.side.value
    ).inc()

    publisher.publish(
        topic=RFQ_REQUESTED_TOPIC,
        key=str(rfq_id),
        payload={
            "event_type": "RFQ_REQUESTED",
            "rfq_id": str(rfq_id),
            "account_id": str(request.account_id),
            "instrument_id":
                request.instrument_id,
            "side": request.side.value,
            "quantity": request.quantity,
            "client": request.client,
            "requested_at":
                requested_at.isoformat(),
        },
    )

    return RFQ.model_validate(row)


@app.get(
    "/rfqs/{rfq_id}",
    response_model=RFQDetail,
)
def get_rfq(
    rfq_id: UUID,
) -> RFQDetail:
    row = repository.get_rfq(rfq_id)

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="RFQ not found",
        )

    quote_rows = repository.list_quotes(
        rfq_id
    )

    return RFQDetail(
        rfq=RFQ.model_validate(row),
        quotes=[
            DealerQuote.model_validate(
                quote
            )
            for quote in quote_rows
        ],
    )


@app.post(
    "/rfqs/{rfq_id}/execute",
    response_model=ExecutionResponse,
)
def execute_quote(
    rfq_id: UUID,
    request: ExecuteQuoteRequest,
) -> ExecutionResponse:
    execution_id = uuid4()
    executed_at = datetime.now(
        timezone.utc
    )

    try:
        (
            execution_row,
            rejected_quote_count,
        ) = repository.execute_quote(
            rfq_id=rfq_id,
            quote_id=request.quote_id,
            execution_id=execution_id,
            executed_at=executed_at,
        )
    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    execution = Execution.model_validate(
        execution_row
    )

    apply_execution_to_ledger(
        execution_id=execution.id
    )

    TRADES_EXECUTED.labels(
        side=execution.side.value,
        dealer=execution.dealer,
    ).inc()

    publisher.publish(
        topic=TRADE_EXECUTED_TOPIC,
        key=str(rfq_id),
        payload={
            "event_type": "TRADE_EXECUTED",
            "execution_id": str(
                execution.id
            ),
            "rfq_id": str(
                execution.rfq_id
            ),
            "quote_id": str(
                execution.quote_id
            ),
            "instrument_id":
                execution.instrument_id,
            "side": execution.side.value,
            "client": execution.client,
            "dealer": execution.dealer,
            "price": execution.price,
            "quantity": execution.quantity,
            "executed_at":
                execution.executed_at.isoformat(),
        },
    )

    return ExecutionResponse(
        execution=execution,
        rejected_quote_count=(
            rejected_quote_count
        ),
    )


@app.get(
    "/accounts/{account_id}",
    response_model=AccountSummary,
)
def account_summary(
    account_id: UUID,
) -> AccountSummary:
    try:
        (
            account,
            position_rows,
        ) = repository.account_summary(
            account_id
        )
    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    positions = [
        Position.model_validate(row)
        for row in position_rows
    ]

    return AccountSummary(
        account_id=account["account_id"],
        account_name=account["account_name"],
        cash_balance=account["cash_balance"],
        position_count=len(positions),
        total_face_value=sum(
            position.face_value
            for position in positions
        ),
        positions=positions,
    )


@app.get(
    "/accounts/{account_id}/risk",
    response_model=LiveAccountRisk,
)
def live_account_risk(
    account_id: UUID,
) -> LiveAccountRisk:
    try:
        account, positions = (
            repository.account_summary(
                account_id
            )
        )
    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    return calculate_live_account_risk(
        account=account,
        position_rows=positions,
    )


@app.get(
    "/analytics/summary",
    response_model=RfqAnalyticsSummary,
)
def analytics_summary() -> RfqAnalyticsSummary:
    summary, dealer_rows = (
        repository.analytics_summary()
    )

    rfq_count = int(
        summary["rfq_count"]
    )

    executed_rfq_count = int(
        summary["executed_rfq_count"]
    )

    dealers = []

    for row in dealer_rows:
        quote_count = int(
            row["quote_count"]
        )

        execution_count = int(
            row["execution_count"]
        )

        dealers.append(
            DealerAnalytics(
                dealer=row["dealer"],
                quote_count=quote_count,
                execution_count=execution_count,
                hit_ratio=(
                    execution_count
                    / quote_count
                    if quote_count > 0
                    else 0.0
                ),
                average_latency_ms=float(
                    row["average_latency_ms"]
                ),
                average_spread_bps=float(
                    row["average_spread_bps"]
                ),
                average_price=float(
                    row["average_price"]
                ),
            )
        )

    return RfqAnalyticsSummary(
        rfq_count=rfq_count,
        quoted_rfq_count=int(
            summary["quoted_rfq_count"]
        ),
        executed_rfq_count=(
            executed_rfq_count
        ),
        execution_rate=(
            executed_rfq_count / rfq_count
            if rfq_count > 0
            else 0.0
        ),
        average_quotes_per_rfq=float(
            summary["average_quotes_per_rfq"]
        ),
        average_dealer_latency_ms=float(
            summary[
                "average_dealer_latency_ms"
            ]
        ),
        p95_dealer_latency_ms=float(
            summary[
                "p95_dealer_latency_ms"
            ]
        ),
        average_execution_latency_ms=float(
            summary[
                "average_execution_latency_ms"
            ]
        ),
        total_notional=float(
            summary["total_notional"]
        ),
        executed_notional=float(
            summary["executed_notional"]
        ),
        dealers=dealers,
    )


@app.get("/metrics")
def metrics():
    return metrics_response()
