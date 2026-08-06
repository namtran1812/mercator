from __future__ import annotations

from .models import (
    LatestBondPrice,
    PortfolioAllocation,
    PortfolioOptimizationRequest,
    PortfolioOptimizationResponse,
)


def calculate_score(
    price: LatestBondPrice,
    objective: str,
) -> float:
    if objective == "carry":
        return max(
            float(price.yield_to_maturity),
            0.0,
        )

    if objective == "spread":
        return max(
            float(price.g_spread_bps),
            0.0,
        )

    return max(
        (
            float(price.yield_to_maturity)
            * float(price.g_spread_bps)
            / max(
                float(price.modified_duration),
                0.5,
            )
        ),
        0.0,
    )


def optimize_portfolio(
    *,
    prices: list[LatestBondPrice],
    request: PortfolioOptimizationRequest,
) -> PortfolioOptimizationResponse:
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

    required_minimum_instruments = int(
        1.0 / request.max_position_percent
    )

    if (
        request.max_position_percent
        * len(available_prices)
        < 1.0 - 1e-12
    ):
        raise ValueError(
            "Maximum position percentage is too small "
            f"for {len(available_prices)} available instruments. "
            f"At least {required_minimum_instruments} instruments "
            "are required."
        )

    scored = [
        (
            calculate_score(
                price,
                request.objective,
            ),
            price,
        )
        for price in available_prices
    ]

    scored.sort(
        key=lambda item: (
            item[0],
            -item[1].instrument_id,
        ),
        reverse=True,
    )

    scores = {
        price.instrument_id: score
        for score, price in scored
    }

    weights = {
        price.instrument_id: 0.0
        for _, price in scored
    }

    active_ids = {
        price.instrument_id
        for _, price in scored
    }

    remaining_weight = 1.0

    while active_ids and remaining_weight > 1e-12:
        active_score_total = sum(
            scores[instrument_id]
            for instrument_id in active_ids
        )

        if active_score_total <= 1e-12:
            proposed = {
                instrument_id: (
                    remaining_weight
                    / len(active_ids)
                )
                for instrument_id in active_ids
            }
        else:
            proposed = {
                instrument_id: (
                    remaining_weight
                    * scores[instrument_id]
                    / active_score_total
                )
                for instrument_id in active_ids
            }

        capped_ids = {
            instrument_id
            for instrument_id, proposed_weight
            in proposed.items()
            if (
                weights[instrument_id]
                + proposed_weight
                > request.max_position_percent
                + 1e-12
            )
        }

        if not capped_ids:
            for instrument_id, proposed_weight in proposed.items():
                weights[instrument_id] += proposed_weight

            remaining_weight = 0.0
            break

        for instrument_id in capped_ids:
            available_capacity = (
                request.max_position_percent
                - weights[instrument_id]
            )

            allocation = max(
                available_capacity,
                0.0,
            )

            weights[instrument_id] += allocation
            remaining_weight -= allocation
            active_ids.remove(instrument_id)

    total_weight = sum(weights.values())

    if total_weight <= 0.0:
        raise ValueError(
            "Optimizer produced no valid allocations."
        )

    if abs(total_weight - 1.0) > 1e-9:
        residual = 1.0 - total_weight

        for _, price in scored:
            instrument_id = price.instrument_id
            capacity = (
                request.max_position_percent
                - weights[instrument_id]
            )

            allocation = min(
                max(capacity, 0.0),
                residual,
            )

            weights[instrument_id] += allocation
            residual -= allocation

            if residual <= 1e-12:
                break

    allocations = [
        PortfolioAllocation(
            instrument_id=price.instrument_id,
            weight=weights[price.instrument_id],
            target_notional=(
                weights[price.instrument_id]
                * request.total_notional
            ),
            expected_score=score,
        )
        for score, price in scored
        if weights[price.instrument_id] > 1e-12
    ]

    return PortfolioOptimizationResponse(
        objective=request.objective,
        total_notional=request.total_notional,
        allocations=allocations,
    )
