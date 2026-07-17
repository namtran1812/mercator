from __future__ import annotations

from .models import (
    CreditHedgeRecommendation,
    HedgeRecommendationRequest,
    HedgeRecommendationResponse,
    LatestBondPrice,
    RiskDecompositionRequest,
    TreasuryHedgeRecommendation,
)
from .risk_decomposition import (
    calculate_risk_decomposition,
)


TREASURY_HEDGE_DV01_PER_MILLION = {
    "2Y": 190.0,
    "3Y": 275.0,
    "5Y": 440.0,
    "7Y": 610.0,
    "10Y": 820.0,
    "20Y": 1_350.0,
    "30Y": 1_720.0,
}

CREDIT_HEDGE_CS01_PER_MILLION = 850.0


def calculate_hedge_recommendations(
    *,
    prices: list[LatestBondPrice],
    request: HedgeRecommendationRequest,
) -> HedgeRecommendationResponse:
    decomposition = calculate_risk_decomposition(
        prices=prices,
        request=RiskDecompositionRequest(
            instrument_ids=request.instrument_ids,
            position_notional=(
                request.position_notional
            ),
        ),
    )

    treasury_hedges: list[
        TreasuryHedgeRecommendation
    ] = []

    hedged_dv01 = 0.0

    for exposure in (
        decomposition.portfolio_key_rate_dv01
    ):
        hedge_dv01_per_million = (
            TREASURY_HEDGE_DV01_PER_MILLION.get(
                exposure.tenor
            )
        )

        if (
            hedge_dv01_per_million is None
            or abs(exposure.key_rate_dv01) < 1e-9
        ):
            continue

        target_dv01 = (
            exposure.key_rate_dv01
            * request.hedge_ratio
        )

        recommended_notional = (
            -target_dv01
            / hedge_dv01_per_million
            * 1_000_000.0
        )

        hedged_dv01 += target_dv01

        treasury_hedges.append(
            TreasuryHedgeRecommendation(
                tenor=exposure.tenor,
                tenor_years=(
                    exposure.tenor_years
                ),
                portfolio_key_rate_dv01=(
                    exposure.key_rate_dv01
                ),
                hedge_instrument_dv01_per_million=(
                    hedge_dv01_per_million
                ),
                recommended_notional=(
                    recommended_notional
                ),
            )
        )

    credit_hedge = None
    hedged_cs01 = 0.0

    if request.include_credit_hedge:
        target_cs01 = (
            decomposition.total_cs01
            * request.hedge_ratio
        )

        recommended_notional = (
            -target_cs01
            / CREDIT_HEDGE_CS01_PER_MILLION
            * 1_000_000.0
        )

        hedged_cs01 = target_cs01

        credit_hedge = CreditHedgeRecommendation(
            portfolio_cs01=(
                decomposition.total_cs01
            ),
            hedge_cs01_per_million=(
                CREDIT_HEDGE_CS01_PER_MILLION
            ),
            recommended_notional=(
                recommended_notional
            ),
            hedge_instrument=(
                "CDX Investment Grade Index"
            ),
        )

    residual_dv01 = (
        decomposition.total_dv01
        - hedged_dv01
    )

    residual_cs01 = (
        decomposition.total_cs01
        - hedged_cs01
    )

    treasury_hedges.sort(
        key=lambda hedge:
            abs(hedge.recommended_notional),
        reverse=True,
    )

    return HedgeRecommendationResponse(
        instrument_count=(
            decomposition.instrument_count
        ),
        total_market_value=(
            decomposition.total_market_value
        ),
        total_dv01=decomposition.total_dv01,
        total_cs01=decomposition.total_cs01,
        hedge_ratio=request.hedge_ratio,
        treasury_hedges=treasury_hedges,
        credit_hedge=credit_hedge,
        residual_dv01=residual_dv01,
        residual_cs01=residual_cs01,
    )
