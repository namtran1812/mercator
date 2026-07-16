from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query
from psycopg import Connection

from .database import connection_dependency
from .models import InstrumentSearchResult, InstrumentVersion
from .reconciliation import reconcile_observations
from .reconciliation_models import (
    ReconciliationResult,
    ReferenceObservation,
)
from .repository import (
    get_current_instrument,
    get_instrument_as_of,
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
