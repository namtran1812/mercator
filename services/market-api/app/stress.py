from __future__ import annotations

from .models import (
    LatestBondPrice,
    RiskDecompositionRequest,
    StressRequest,
    StressResponse,
    StressResult,
)
from .risk_decomposition import (
    calculate_risk_decomposition,
)


def interpolate_treasury_shock_bps(
    tenor_years: float,
    *,
    treasury_2y_bps: float,
    treasury_5y_bps: float,
    treasury_10y_bps: float,
    treasury_30y_bps: float,
) -> float:
    curve = [
        (2.0, treasury_2y_bps),
        (5.0, treasury_5y_bps),
        (10.0, treasury_10y_bps),
        (30.0, treasury_30y_bps),
    ]

    if tenor_years <= curve[0][0]:
        return curve[0][1]

    if tenor_years >= curve[-1][0]:
        return curve[-1][1]

    for index in range(1, len(curve)):
        upper_years, upper_shock = curve[index]
        lower_years, lower_shock = curve[index - 1]

        if tenor_years <= upper_years:
            fraction = (
                tenor_years - lower_years
            ) / (
                upper_years - lower_years
            )

            return (
                lower_shock
                + fraction
                * (upper_shock - lower_shock)
            )

    raise RuntimeError(
        "Unable to interpolate Treasury shock"
    )


def calculate_stress(
    *,
    prices: list[LatestBondPrice],
    request: StressRequest,
) -> StressResponse:
    decomposition = calculate_risk_decomposition(
        prices=prices,
        request=RiskDecompositionRequest(
            instrument_ids=request.instrument_ids,
            position_notional=(
                request.position_notional
            ),
        ),
    )

    results: list[StressResult] = []

    total_market_value = 0.0
    total_treasury_pnl = 0.0
    total_credit_pnl = 0.0
    total_pnl = 0.0

    for instrument in decomposition.instruments:
        treasury_pnl = 0.0

        for exposure in instrument.key_rate_exposures:
            shaped_shock_bps = (
                interpolate_treasury_shock_bps(
                    exposure.tenor_years,
                    treasury_2y_bps=(
                        request.scenario.treasury_2y_bps
                    ),
                    treasury_5y_bps=(
                        request.scenario.treasury_5y_bps
                    ),
                    treasury_10y_bps=(
                        request.scenario.treasury_10y_bps
                    ),
                    treasury_30y_bps=(
                        request.scenario.treasury_30y_bps
                    ),
                )
            )

            total_shock_bps = (
                request.scenario.treasury_parallel_bps
                + shaped_shock_bps
            )

            treasury_pnl += (
                -exposure.key_rate_dv01
                * total_shock_bps
            )

        credit_pnl = (
            -instrument.cs01
            * request.scenario.credit_parallel_bps
        )

        instrument_total_pnl = (
            treasury_pnl
            + credit_pnl
        )

        results.append(
            StressResult(
                instrument_id=(
                    instrument.instrument_id
                ),
                market_value=(
                    instrument.market_value
                ),
                treasury_pnl=treasury_pnl,
                credit_pnl=credit_pnl,
                total_pnl=instrument_total_pnl,
            )
        )

        total_market_value += (
            instrument.market_value
        )
        total_treasury_pnl += treasury_pnl
        total_credit_pnl += credit_pnl
        total_pnl += instrument_total_pnl

    results.sort(
        key=lambda item: item.total_pnl
    )

    return StressResponse(
        instrument_count=len(results),
        total_market_value=total_market_value,
        total_treasury_pnl=(
            total_treasury_pnl
        ),
        total_credit_pnl=total_credit_pnl,
        total_pnl=total_pnl,
        instruments=results,
    )
