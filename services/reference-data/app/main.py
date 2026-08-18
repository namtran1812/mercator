from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from psycopg import Connection

from .database import connection_dependency
from .models import (
    FixedIncomeEtfConstituent,
    FixedIncomeEtfDetails,
    InstrumentSearchResult,
    InstrumentVersion,
)
from .reconciliation import reconcile_observations
from .reconciliation_models import (
    ReconciliationResult,
    ReferenceObservation,
)
from .repository import (
    get_current_instrument,
    get_instrument_as_of,
    find_peer_instruments,
    get_current_etf,
    get_current_etf_constituents,
    list_versions,
    search_instruments,
    get_active_reference_observations,
    persist_reconciliation,
)

app = FastAPI(
    title="Mercator Reference Data Service",
    version="0.1.0",
    description=(
        "Bi-temporal security-master API for corporate bonds "
        "and fixed-income ETFs."
    ),
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8005",
        "http://localhost:8005",
    ],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)



@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/instruments/search",
    response_model=list[InstrumentSearchResult],
)
def search(
    q: str = Query(min_length=1, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    connection: Connection = Depends(connection_dependency),
) -> list[InstrumentSearchResult]:
    return search_instruments(
        connection=connection,
        query_text=q,
        limit=limit,
    )


@app.get(
    "/instruments/peers",
    response_model=list[InstrumentVersion],
)
def peer_instruments(
    instrument_type: str,
    currency: str = "USD",
    sector: str | None = None,
    maturity_start: datetime | None = None,
    maturity_end: datetime | None = None,
    exclude_instrument_id: int = 0,
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    connection: Connection = Depends(
        connection_dependency
    ),
) -> list[InstrumentVersion]:
    return find_peer_instruments(
        connection=connection,
        instrument_type=instrument_type,
        currency=currency,
        sector=sector,
        maturity_start=maturity_start,
        maturity_end=maturity_end,
        exclude_instrument_id=
            exclude_instrument_id,
        limit=limit,
    )


@app.get(
    "/instruments/{instrument_id}",
    response_model=InstrumentVersion,
)
def current_instrument(
    instrument_id: int,
    connection: Connection = Depends(connection_dependency),
) -> InstrumentVersion:
    instrument = get_current_instrument(
        connection=connection,
        instrument_id=instrument_id,
    )

    if instrument is None:
        raise HTTPException(
            status_code=404,
            detail="Instrument not found",
        )

    return instrument


@app.get(
    "/instruments/{instrument_id}/as-of",
    response_model=InstrumentVersion,
)
def instrument_as_of(
    instrument_id: int,
    valid_at: datetime,
    known_at: datetime | None = None,
    connection: Connection = Depends(connection_dependency),
) -> InstrumentVersion:
    resolved_known_at = known_at or datetime.now(timezone.utc)

    instrument = get_instrument_as_of(
        connection=connection,
        instrument_id=instrument_id,
        valid_at=valid_at,
        known_at=resolved_known_at,
    )

    if instrument is None:
        raise HTTPException(
            status_code=404,
            detail="No instrument version exists for the requested times",
        )

    return instrument


@app.get(
    "/instruments/{instrument_id}/versions",
    response_model=list[InstrumentVersion],
)
def versions(
    instrument_id: int,
    connection: Connection = Depends(connection_dependency),
) -> list[InstrumentVersion]:
    results = list_versions(
        connection=connection,
        instrument_id=instrument_id,
    )

    if not results:
        raise HTTPException(
            status_code=404,
            detail="Instrument not found",
        )

    return results


@app.post(
    "/instruments/{instrument_id}/reconcile/{field_name}",
    response_model=ReconciliationResult,
)
def reconcile_field(
    instrument_id: int,
    field_name: str,
    connection: Connection = Depends(connection_dependency),
) -> ReconciliationResult:
    rows = get_active_reference_observations(
        connection=connection,
        instrument_id=instrument_id,
        field_name=field_name,
    )

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="No active observations found",
        )

    observations = [
        ReferenceObservation.model_validate(row)
        for row in rows
    ]

    result = reconcile_observations(observations)
    persist_reconciliation(connection, result)

    return result


@app.get(
    "/etfs/{instrument_id}",
    response_model=FixedIncomeEtfDetails,
)
def current_etf(
    instrument_id: int,
    connection: Connection = Depends(
        connection_dependency
    ),
) -> FixedIncomeEtfDetails:
    instrument = get_current_instrument(
        connection=connection,
        instrument_id=instrument_id,
    )

    if (
        instrument is None
        or instrument.instrument_type
        != "FIXED_INCOME_ETF"
    ):
        raise HTTPException(
            status_code=404,
            detail="Fixed-income ETF not found",
        )

    etf = get_current_etf(
        connection=connection,
        instrument_id=instrument_id,
    )

    if etf is None:
        raise HTTPException(
            status_code=404,
            detail="ETF analytics metadata not found",
        )

    return etf


@app.get(
    "/etfs/{instrument_id}/constituents",
    response_model=list[
        FixedIncomeEtfConstituent
    ],
)
def current_etf_constituents(
    instrument_id: int,
    connection: Connection = Depends(
        connection_dependency
    ),
) -> list[FixedIncomeEtfConstituent]:
    instrument = get_current_instrument(
        connection=connection,
        instrument_id=instrument_id,
    )

    if (
        instrument is None
        or instrument.instrument_type
        != "FIXED_INCOME_ETF"
    ):
        raise HTTPException(
            status_code=404,
            detail="Fixed-income ETF not found",
        )

    constituents = (
        get_current_etf_constituents(
            connection=connection,
            instrument_id=instrument_id,
        )
    )

    if not constituents:
        raise HTTPException(
            status_code=404,
            detail="ETF constituents not found",
        )

    return constituents
