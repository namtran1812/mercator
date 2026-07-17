from __future__ import annotations

from .models import (
    LatestBondPrice,
    ScenarioAnalysisRequest,
    ScenarioAnalysisResponse,
    ScenarioInstrumentResult,
)

DOWNGRADE_SPREAD_BPS_PER_NOTCH = 15.0


def analyze_scenario(
    *,
    prices: list[LatestBondPrice],
    request: ScenarioAnalysisRequest,
) -> ScenarioAnalysisResponse:
    requested_ids = set(request.instrument_ids)

    available_prices = [
        price
        for price in prices
        if price.instrument_id in requested_ids
    ]

    if not available_prices:
        raise ValueError(
            "No pricing data found for requested instruments."
        )

    results: list[ScenarioInstrumentResult] = []

    treasury_total = 0.0
    spread_total = 0.0
    liquidity_total = 0.0
    downgrade_total = 0.0

    for price in available_prices:
        duration = max(
            float(price.modified_duration),
            0.0,
        )

        convexity = max(
            float(price.convexity),
            0.0,
        )

        treasury_shift_decimal = (
            request.treasury_shift_bps
            / 10_000.0
        )

        spread_shift_decimal = (
            request.spread_shift_bps
            / 10_000.0
        )

        treasury_pnl = (
            request.position_notional
            * (
                -duration
                * treasury_shift_decimal
                + 0.5
                * convexity
                * treasury_shift_decimal
                * treasury_shift_decimal
            )
        )

        spread_pnl = (
            -duration
            * request.position_notional
            * spread_shift_decimal
        )

        liquidity_pnl = (
            -request.position_notional
            * request.liquidity_haircut_percent
            / 100.0
        )

        downgrade_shift_decimal = (
            DOWNGRADE_SPREAD_BPS_PER_NOTCH
            * request.downgrade_notches
            / 10_000.0
        )

        downgrade_pnl = (
            -duration
            * request.position_notional
            * downgrade_shift_decimal
        )

        pnl = (
            treasury_pnl
            + spread_pnl
            + liquidity_pnl
            + downgrade_pnl
        )

        treasury_total += treasury_pnl
        spread_total += spread_pnl
        liquidity_total += liquidity_pnl
        downgrade_total += downgrade_pnl

        results.append(
            ScenarioInstrumentResult(
                instrument_id=price.instrument_id,
                pnl=pnl,
                treasury_pnl=treasury_pnl,
                spread_pnl=spread_pnl,
                liquidity_pnl=liquidity_pnl,
                downgrade_pnl=downgrade_pnl,
            )
        )

    results.sort(
        key=lambda item: item.pnl
    )

    return ScenarioAnalysisResponse(
        total_pnl=(
            treasury_total
            + spread_total
            + liquidity_total
            + downgrade_total
        ),
        treasury_pnl=treasury_total,
        spread_pnl=spread_total,
        liquidity_pnl=liquidity_total,
        downgrade_pnl=downgrade_total,
        instruments=results,
    )
