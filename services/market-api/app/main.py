from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from .models import LatestBondPrice, MarketSummary
from .repository import MarketRepository


app = FastAPI(
    title="Mercator Market API",
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

repository = MarketRepository()


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
    }


@app.get(
    "/prices/latest",
    response_model=list[LatestBondPrice],
)
def latest_prices(
    limit: int = Query(
        default=100,
        ge=1,
        le=10_000,
    ),
    minimum_quality_score: float = Query(
        default=0.8,
        ge=0.0,
        le=1.0,
    ),
) -> list[LatestBondPrice]:
    return repository.latest_prices(
        limit=limit,
        minimum_quality_score=(
            minimum_quality_score
        ),
    )


@app.get(
    "/market/summary",
    response_model=MarketSummary,
)
def market_summary() -> MarketSummary:
    return repository.market_summary()
