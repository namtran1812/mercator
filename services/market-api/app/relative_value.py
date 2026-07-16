from __future__ import annotations

import math
import statistics

from .models import (
    LatestBondPrice,
    RelativeValueOpportunity,
    RelativeValueRequest,
    RelativeValueResponse,
)


def classify_z_score(
    z_score: float,
) -> str:
    if z_score >= 1.5:
        return "CHEAP"

    if z_score <= -1.5:
        return "RICH"

    return "FAIR"


def calculate_relative_value(
    *,
    prices: list[LatestBondPrice],
    request: RelativeValueRequest,
) -> RelativeValueResponse:
    valid_prices = [
        price
        for price in prices
        if (
            price.quality_status == "VALID"
            and price.quality_score >= 0.80
        )
    ]

    opportunities: list[
        RelativeValueOpportunity
    ] = []

    for target in valid_prices:
        peers = [
            candidate
            for candidate in valid_prices
            if (
                candidate.instrument_id
                != target.instrument_id
                and abs(
                    candidate.modified_duration
                    - target.modified_duration
                )
                <= request.duration_bucket_width
            )
        ]

        if (
            len(peers)
            < request.minimum_peer_count
        ):
            continue

        peer_spreads = [
            peer.g_spread_bps
            for peer in peers
        ]

        peer_average = statistics.mean(
            peer_spreads
        )

        peer_standard_deviation = (
            statistics.pstdev(
                peer_spreads
            )
        )

        spread_difference = (
            target.g_spread_bps
            - peer_average
        )

        spread_z_score = (
            spread_difference
            / peer_standard_deviation
            if peer_standard_deviation > 0.0
            else 0.0
        )

        duration_adjusted_spread = (
            target.g_spread_bps
            / max(
                target.modified_duration,
                0.01,
            )
        )

        conviction_score = min(
            100.0,
            abs(spread_z_score)
            * 35.0
            + math.log1p(len(peers))
            * 8.0,
        )

        classification = classify_z_score(
            spread_z_score
        )

        opportunities.append(
            RelativeValueOpportunity(
                instrument_id=(
                    target.instrument_id
                ),
                clean_price=(
                    target.clean_price
                ),
                yield_to_maturity=(
                    target.yield_to_maturity
                ),
                g_spread_bps=(
                    target.g_spread_bps
                ),
                modified_duration=(
                    target.modified_duration
                ),
                peer_count=len(peers),
                peer_average_spread_bps=(
                    peer_average
                ),
                peer_spread_standard_deviation_bps=(
                    peer_standard_deviation
                ),
                spread_difference_bps=(
                    spread_difference
                ),
                spread_z_score=(
                    spread_z_score
                ),
                duration_adjusted_spread=(
                    duration_adjusted_spread
                ),
                classification=classification,
                conviction_score=(
                    conviction_score
                ),
            )
        )

    opportunities.sort(
        key=lambda item: (
            abs(item.spread_z_score),
            item.conviction_score,
        ),
        reverse=True,
    )

    return RelativeValueResponse(
        instrument_count=len(valid_prices),
        opportunity_count=len(
            opportunities
        ),
        average_spread_bps=(
            statistics.mean(
                price.g_spread_bps
                for price in valid_prices
            )
            if valid_prices
            else 0.0
        ),
        average_duration=(
            statistics.mean(
                price.modified_duration
                for price in valid_prices
            )
            if valid_prices
            else 0.0
        ),
        opportunities=opportunities,
    )
