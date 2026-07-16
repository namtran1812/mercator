from __future__ import annotations

import statistics

from mercator_agent.state.models import (
    PriceObservation,
    RelativeValueResult,
)


def calculate_relative_value(
    prices: list[PriceObservation],
) -> list[RelativeValueResult]:
    valid_prices = [
        price
        for price in prices
        if (
            price.quality_status == "VALID"
            and price.quality_score >= 0.80
        )
    ]

    if len(valid_prices) < 2:
        return []

    average_spread = statistics.mean(
        price.g_spread_bps
        for price in valid_prices
    )

    results: list[RelativeValueResult] = []

    for price in valid_prices:
        difference = (
            price.g_spread_bps -
            average_spread
        )

        if difference >= 25.0:
            interpretation = (
                "trades materially wider than the "
                "selected peer average"
            )
        elif difference <= -25.0:
            interpretation = (
                "trades materially tighter than the "
                "selected peer average"
            )
        else:
            interpretation = (
                "trades near the selected peer average"
            )

        results.append(
            RelativeValueResult(
                instrument_id=price.instrument_id,
                spread_bps=price.g_spread_bps,
                peer_average_spread_bps=(
                    average_spread
                ),
                spread_difference_bps=difference,
                interpretation=interpretation,
            )
        )

    return sorted(
        results,
        key=lambda result: (
            result.spread_difference_bps
        ),
        reverse=True,
    )
