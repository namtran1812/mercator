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
    RelativeValueRequest,
    RelativeValueResponse,
    CarryRollRequest,
    CarryRollResponse,
    RiskDecompositionRequest,
    RiskDecompositionResponse,
    StressRequest,
    StressResponse,
    HistoricalVarRequest,
    HistoricalVarResponse,
    HedgeRecommendationRequest,
    HedgeRecommendationResponse,
    PortfolioOptimizationRequest,
    PortfolioOptimizationResponse,
    RiskBudgetOptimizationRequest,
    RiskBudgetOptimizationResponse,
    ScenarioAnalysisRequest,
    ScenarioAnalysisResponse,
    ReplayScenario,
    RelativeValueRequest,
    RelativeValueResponse,
    CarryRollRequest,
    CarryRollResponse,
    ScenarioRequest,
    ScenarioResponse,
)
from .repository import MarketRepository
from .portfolio import calculate_portfolio_risk
from .scenario import calculate_scenario
from .relative_value import calculate_relative_value
from .carry_roll import calculate_carry_roll
from .risk_decomposition import calculate_risk_decomposition
from .stress import calculate_stress
from .historical_var import calculate_historical_var
from .hedging import calculate_hedge_recommendations
from .optimizer import optimize_portfolio
from .risk_optimizer import optimize_with_risk_budget
from .scenario_analysis import analyze_scenario


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


@app.post(
    "/relative-value/rank",
    response_model=RelativeValueResponse,
)
def rank_relative_value(
    request: RelativeValueRequest,
) -> RelativeValueResponse:
    prices = repository.latest_prices_by_ids(
        request.instrument_ids
    )

    return calculate_relative_value(
        prices=prices,
        request=request,
    )


@app.post(
    "/carry-roll/rank",
    response_model=CarryRollResponse,
)
def rank_carry_roll(
    request: CarryRollRequest,
) -> CarryRollResponse:
    prices = repository.latest_prices_by_ids(
        request.instrument_ids
    )

    return calculate_carry_roll(
        prices=prices,
        request=request,
    )


@app.post(
    "/risk/decomposition",
    response_model=RiskDecompositionResponse,
)
def risk_decomposition(
    request: RiskDecompositionRequest,
) -> RiskDecompositionResponse:
    prices = repository.latest_prices_by_ids(
        request.instrument_ids
    )

    return calculate_risk_decomposition(
        prices=prices,
        request=request,
    )


@app.post(
    "/stress/run",
    response_model=StressResponse,
)
def run_stress(
    request: StressRequest,
) -> StressResponse:
    prices = repository.latest_prices_by_ids(
        request.instrument_ids
    )

    return calculate_stress(
        prices=prices,
        request=request,
    )


@app.post(
    "/risk/historical-var",
    response_model=HistoricalVarResponse,
)
def historical_var(
    request: HistoricalVarRequest,
) -> HistoricalVarResponse:
    prices = repository.latest_prices_by_ids(
        request.instrument_ids
    )

    return calculate_historical_var(
        prices=prices,
        request=request,
    )


@app.post(
    "/risk/hedge-recommendations",
    response_model=HedgeRecommendationResponse,
)
def hedge_recommendations(
    request: HedgeRecommendationRequest,
) -> HedgeRecommendationResponse:
    prices = repository.latest_prices_by_ids(
        request.instrument_ids
    )

    return calculate_hedge_recommendations(
        prices=prices,
        request=request,
    )


@app.post(
    "/portfolio/optimize",
    response_model=PortfolioOptimizationResponse,
)
def optimize(
    request: PortfolioOptimizationRequest,
):

    prices = repository.latest_prices_by_ids(
        request.instrument_ids
    )

    return optimize_portfolio(
        prices=prices,
        request=request,
    )


@app.post(
    "/portfolio/optimize-risk",
    response_model=RiskBudgetOptimizationResponse,
)
def optimize_risk_budget(
    request: RiskBudgetOptimizationRequest,
) -> RiskBudgetOptimizationResponse:
    prices = repository.latest_prices_by_ids(
        request.instrument_ids
    )

    return optimize_with_risk_budget(
        prices=prices,
        request=request,
    )


@app.post(
    "/risk/scenario-analysis",
    response_model=ScenarioAnalysisResponse,
)
def scenario_analysis(
    request: ScenarioAnalysisRequest,
) -> ScenarioAnalysisResponse:
    prices = repository.latest_prices_by_ids(
        request.instrument_ids
    )

    try:
        return analyze_scenario(
            prices=prices,
            request=request,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
