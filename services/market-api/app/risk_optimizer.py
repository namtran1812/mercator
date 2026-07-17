from __future__ import annotations

from dataclasses import dataclass

from .models import (
    LatestBondPrice,
    RiskBudgetAllocation,
    RiskBudgetOptimizationRequest,
    RiskBudgetOptimizationResponse,
    RiskDecompositionRequest,
)
from .optimizer import calculate_score
from .risk_decomposition import calculate_risk_decomposition


@dataclass(frozen=True)
class Candidate:
    instrument_id: int
    score: float
    dv01_per_dollar: float
    cs01_per_dollar: float


def optimize_with_risk_budget(
    *,
    prices: list[LatestBondPrice],
    request: RiskBudgetOptimizationRequest,
) -> RiskBudgetOptimizationResponse:
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

    decomposition = calculate_risk_decomposition(
        prices=available_prices,
        request=RiskDecompositionRequest(
            instrument_ids=[
                price.instrument_id
                for price in available_prices
            ],
            position_notional=1_000_000.0,
        ),
    )

    risk_by_id = {
        instrument.instrument_id: instrument
        for instrument in decomposition.instruments
    }

    candidates: list[Candidate] = []

    for price in available_prices:
        risk = risk_by_id.get(price.instrument_id)

        if risk is None:
            continue

        candidates.append(
            Candidate(
                instrument_id=price.instrument_id,
                score=calculate_score(
                    price,
                    request.objective,
                ),
                dv01_per_dollar=(
                    risk.aggregate_dv01
                    / 1_000_000.0
                ),
                cs01_per_dollar=(
                    risk.cs01
                    / 1_000_000.0
                ),
            )
        )

    if not candidates:
        raise ValueError(
            "No instruments had both price and risk data."
        )

    candidates.sort(
        key=lambda item: (
            item.score
            / max(
                item.dv01_per_dollar
                + item.cs01_per_dollar,
                1e-12,
            ),
            item.score,
            -item.instrument_id,
        ),
        reverse=True,
    )

    maximum_position_notional = (
        request.total_notional
        * request.max_position_percent
    )

    remaining_notional = request.total_notional
    remaining_dv01 = request.max_portfolio_dv01
    remaining_cs01 = request.max_portfolio_cs01

    notionals: dict[int, float] = {
        candidate.instrument_id: 0.0
        for candidate in candidates
    }

    while remaining_notional > 0.01:
        made_allocation = False

        for candidate in candidates:
            current_notional = notionals[
                candidate.instrument_id
            ]

            position_capacity = (
                maximum_position_notional
                - current_notional
            )

            if position_capacity <= 0.01:
                continue

            dv01_capacity = (
                remaining_dv01
                / candidate.dv01_per_dollar
                if candidate.dv01_per_dollar > 0.0
                else remaining_notional
            )

            cs01_capacity = (
                remaining_cs01
                / candidate.cs01_per_dollar
                if candidate.cs01_per_dollar > 0.0
                else remaining_notional
            )

            allocation = min(
                remaining_notional,
                position_capacity,
                dv01_capacity,
                cs01_capacity,
            )

            if allocation <= 0.01:
                continue

            notionals[candidate.instrument_id] += allocation
            remaining_notional -= allocation
            remaining_dv01 -= (
                allocation
                * candidate.dv01_per_dollar
            )
            remaining_cs01 -= (
                allocation
                * candidate.cs01_per_dollar
            )

            remaining_dv01 = max(
                remaining_dv01,
                0.0,
            )
            remaining_cs01 = max(
                remaining_cs01,
                0.0,
            )

            made_allocation = True

            if remaining_notional <= 0.01:
                break

        if not made_allocation:
            break

    candidate_by_id = {
        candidate.instrument_id: candidate
        for candidate in candidates
    }

    allocations: list[RiskBudgetAllocation] = []

    invested_notional = 0.0
    portfolio_dv01 = 0.0
    portfolio_cs01 = 0.0

    for candidate in candidates:
        target_notional = notionals[
            candidate.instrument_id
        ]

        if target_notional <= 0.01:
            continue

        dv01 = (
            target_notional
            * candidate.dv01_per_dollar
        )

        cs01 = (
            target_notional
            * candidate.cs01_per_dollar
        )

        invested_notional += target_notional
        portfolio_dv01 += dv01
        portfolio_cs01 += cs01

        allocations.append(
            RiskBudgetAllocation(
                instrument_id=(
                    candidate.instrument_id
                ),
                weight=(
                    target_notional
                    / request.total_notional
                ),
                target_notional=target_notional,
                expected_score=(
                    candidate_by_id[
                        candidate.instrument_id
                    ].score
                ),
                dv01=dv01,
                cs01=cs01,
            )
        )

    allocations.sort(
        key=lambda item: item.target_notional,
        reverse=True,
    )

    cash_notional = max(
        request.total_notional
        - invested_notional,
        0.0,
    )

    return RiskBudgetOptimizationResponse(
        objective=request.objective,
        requested_notional=(
            request.total_notional
        ),
        invested_notional=invested_notional,
        cash_notional=cash_notional,
        invested_percent=(
            invested_notional
            / request.total_notional
        ),
        portfolio_dv01=portfolio_dv01,
        portfolio_cs01=portfolio_cs01,
        max_portfolio_dv01=(
            request.max_portfolio_dv01
        ),
        max_portfolio_cs01=(
            request.max_portfolio_cs01
        ),
        allocations=allocations,
    )
