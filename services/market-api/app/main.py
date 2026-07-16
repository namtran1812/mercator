from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    LatestBondPrice,
    MarketSummary,
    PriceHistoryPoint,
    PortfolioRiskRequest,
    PortfolioRiskResponse,
    ReplayScenario,
    ReplayScenario,
    ScenarioRequest,
    ScenarioResponse,
)
from .repository import MarketRepository
from .portfolio import calculate_portfolio_risk
from .scenario import calculate_scenario


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


@app.get(
    "/prices/{instrument_id}/history",
    response_model=list[PriceHistoryPoint],
)
def price_history(
    instrument_id: int,
    limit: int = Query(
        default=100,
        ge=1,
        le=5_000,
    ),
) -> list[PriceHistoryPoint]:
    return repository.price_history(
        instrument_id=instrument_id,
        limit=limit,
    )


@app.post(
    "/scenarios/run",
    response_model=ScenarioResponse,
)
def run_scenario(
    request: ScenarioRequest,
) -> ScenarioResponse:
    prices = repository.latest_prices_by_ids(
        request.instrument_ids
    )

    return calculate_scenario(
        prices,
        request,
    )


@app.post(
    "/portfolio/risk",
    response_model=PortfolioRiskResponse,
)
def portfolio_risk(
    request: PortfolioRiskRequest,
) -> PortfolioRiskResponse:
    instrument_ids = [
        position.instrument_id
        for position in request.positions
    ]

    prices = repository.latest_prices_by_ids(
        instrument_ids
    )

    return calculate_portfolio_risk(
        prices,
        request,
    )


@app.get(
    "/replay/scenarios",
    response_model=list[ReplayScenario],
)
def replay_scenarios() -> list[ReplayScenario]:
    return repository.replay_scenarios()


@app.get(
    "/replay/scenarios",
    response_model=list[ReplayScenario],
)
def replay_scenarios() -> list[ReplayScenario]:
    return repository.replay_scenarios()
