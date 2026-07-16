from __future__ import annotations

from .models import (
    LatestBondPrice,
    ScenarioRequest,
    ScenarioResponse,
    ScenarioResult,
)


def calculate_scenario(
    prices: list[LatestBondPrice],
    request: ScenarioRequest,
) -> ScenarioResponse:
    total_shock_decimal = (
        request.treasury_shock_bps
        + request.credit_spread_shock_bps
    ) / 10_000.0

    results: list[ScenarioResult] = []

    for price in prices:
        first_order_change = (
            -price.modified_duration
            * total_shock_decimal
        )

        second_order_change = (
            0.5
            * price.convexity
            * total_shock_decimal
            * total_shock_decimal
        )

        price_change_percent_decimal = (
            first_order_change
            + second_order_change
        )

        shocked_clean_price = (
            price.clean_price
            * (1.0 + price_change_percent_decimal)
        )

        price_change = (
            shocked_clean_price
            - price.clean_price
        )

        estimated_pnl = (
            price_change
            / 100.0
            * request.position_face_value
        )

        results.append(
            ScenarioResult(
                instrument_id=price.instrument_id,
                base_clean_price=price.clean_price,
                shocked_clean_price=shocked_clean_price,
                price_change=price_change,
                price_change_percent=(
                    price_change_percent_decimal * 100.0
                ),
                base_yield=price.yield_to_maturity,
                shocked_yield=(
                    price.yield_to_maturity
                    + total_shock_decimal
                ),
                base_spread_bps=price.g_spread_bps,
                shocked_spread_bps=(
                    price.g_spread_bps
                    + request.credit_spread_shock_bps
                ),
                modified_duration=(
                    price.modified_duration
                ),
                convexity=price.convexity,
                estimated_pnl=estimated_pnl,
            )
        )

    results.sort(
        key=lambda result: result.estimated_pnl,
        reverse=True,
    )

    return ScenarioResponse(
        treasury_shock_bps=(
            request.treasury_shock_bps
        ),
        credit_spread_shock_bps=(
            request.credit_spread_shock_bps
        ),
        position_face_value=(
            request.position_face_value
        ),
        instrument_count=len(results),
        total_estimated_pnl=sum(
            result.estimated_pnl
            for result in results
        ),
        results=results,
    )
