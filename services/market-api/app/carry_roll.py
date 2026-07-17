from __future__ import annotations

import math
import statistics

from .models import (
    CarryRollOpportunity,
    CarryRollRequest,
    CarryRollResponse,
    LatestBondPrice,
)


TREASURY_CURVE = [
    (0.25, 0.0430),
    (0.50, 0.0420),
    (1.00, 0.0410),
    (2.00, 0.0400),
    (3.00, 0.0410),
    (5.00, 0.0430),
    (7.00, 0.0450),
    (10.00, 0.0460),
    (30.00, 0.0470),
]


def interpolate_curve_rate(
    maturity_years: float,
) -> float:
    if maturity_years <= TREASURY_CURVE[0][0]:
        return TREASURY_CURVE[0][1]

    if maturity_years >= TREASURY_CURVE[-1][0]:
        return TREASURY_CURVE[-1][1]

    for index in range(1, len(TREASURY_CURVE)):
        upper_years, upper_rate = (
            TREASURY_CURVE[index]
        )
        lower_years, lower_rate = (
            TREASURY_CURVE[index - 1]
        )

        if maturity_years <= upper_years:
            fraction = (
                maturity_years - lower_years
            ) / (
                upper_years - lower_years
            )

            return (
                lower_rate
                + fraction
                * (upper_rate - lower_rate)
            )

    raise RuntimeError(
        "Could not interpolate Treasury curve"
    )


def maturity_proxy_from_duration(
    modified_duration: float,
) -> float:
    # Approximation suitable for the synthetic universe.
    return max(
        0.25,
        min(
            30.0,
            modified_duration * 1.35,
        ),
    )


def classification(
    expected_return_percent: float,
) -> str:
    if expected_return_percent >= 2.0:
        return "ATTRACTIVE"

    if expected_return_percent <= 0.0:
        return "UNATTRACTIVE"

    return "NEUTRAL"


def calculate_carry_roll(
    *,
    prices: list[LatestBondPrice],
    request: CarryRollRequest,
) -> CarryRollResponse:
    valid_prices = [
        price
        for price in prices
        if (
            price.quality_status == "VALID"
            and price.quality_score >= 0.80
        )
    ]

    horizon_years = (
        request.horizon_months / 12.0
    )

    opportunities: list[
        CarryRollOpportunity
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
                <= 1.5
            )
        ]

        peer_average_spread = (
            statistics.mean(
                peer.g_spread_bps
                for peer in peers
            )
            if peers
            else target.g_spread_bps
        )

        maturity_years = (
            maturity_proxy_from_duration(
                target.modified_duration
            )
        )

        rolled_maturity_years = max(
            0.25,
            maturity_years - horizon_years,
        )

        current_treasury_rate = (
            interpolate_curve_rate(
                maturity_years
            )
        )

        rolled_treasury_rate = (
            interpolate_curve_rate(
                rolled_maturity_years
            )
        )

        treasury_roll_down = (
            rolled_treasury_rate
            - current_treasury_rate
        )

        treasury_roll_down_bps = (
            treasury_roll_down
            * 10_000.0
        )

        coupon_carry_return = (
            target.yield_to_maturity
            * horizon_years
        )

        financing_cost_return = (
            request.annual_financing_rate
            * horizon_years
        )

        treasury_roll_return = (
            -target.modified_duration
            * treasury_roll_down
        )

        spread_gap_bps = (
            target.g_spread_bps
            - peer_average_spread
        )

        expected_spread_change_bps = (
            -spread_gap_bps
            * request.expected_spread_normalization_fraction
        )

        expected_spread_change_decimal = (
            expected_spread_change_bps
            / 10_000.0
        )

        spread_normalization_return = (
            -target.modified_duration
            * expected_spread_change_decimal
        )

        total_return = (
            coupon_carry_return
            - financing_cost_return
            + treasury_roll_return
            + spread_normalization_return
        )

        expected_return_percent = (
            total_return * 100.0
        )

        expected_pnl_per_million = (
            total_return * 1_000_000.0
        )

        conviction_score = min(
            100.0,
            max(
                0.0,
                abs(expected_return_percent)
                * 20.0
                + math.log1p(len(peers))
                * 8.0,
            ),
        )

        opportunities.append(
            CarryRollOpportunity(
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
                convexity=target.convexity,
                horizon_months=(
                    request.horizon_months
                ),
                coupon_carry_return_percent=(
                    coupon_carry_return
                    * 100.0
                ),
                financing_cost_return_percent=(
                    financing_cost_return
                    * 100.0
                ),
                treasury_roll_down_bps=(
                    treasury_roll_down_bps
                ),
                treasury_roll_return_percent=(
                    treasury_roll_return
                    * 100.0
                ),
                peer_average_spread_bps=(
                    peer_average_spread
                ),
                expected_spread_change_bps=(
                    expected_spread_change_bps
                ),
                spread_normalization_return_percent=(
                    spread_normalization_return
                    * 100.0
                ),
                expected_total_return_percent=(
                    expected_return_percent
                ),
                expected_pnl_per_million=(
                    expected_pnl_per_million
                ),
                classification=classification(
                    expected_return_percent
                ),
                conviction_score=(
                    conviction_score
                ),
            )
        )

    opportunities.sort(
        key=lambda item:
            item.expected_total_return_percent,
        reverse=True,
    )

    average_expected_return = (
        statistics.mean(
            item.expected_total_return_percent
            for item in opportunities
        )
        if opportunities
        else 0.0
    )

    return CarryRollResponse(
        instrument_count=len(valid_prices),
        horizon_months=(
            request.horizon_months
        ),
        average_expected_return_percent=(
            average_expected_return
        ),
        opportunities=opportunities,
    )
