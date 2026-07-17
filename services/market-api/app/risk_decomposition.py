from __future__ import annotations

from collections import defaultdict

from .models import (
    InstrumentRiskDecomposition,
    KeyRateExposure,
    LatestBondPrice,
    RiskDecompositionRequest,
    RiskDecompositionResponse,
)


KEY_RATE_TENORS = [
    ("2Y", 2.0),
    ("3Y", 3.0),
    ("5Y", 5.0),
    ("7Y", 7.0),
    ("10Y", 10.0),
    ("20Y", 20.0),
    ("30Y", 30.0),
]


def maturity_proxy_from_duration(
    modified_duration: float,
) -> float:
    return max(
        0.25,
        min(
            30.0,
            modified_duration * 1.35,
        ),
    )


def key_rate_weights(
    maturity_years: float,
) -> list[tuple[str, float, float]]:
    if maturity_years <= KEY_RATE_TENORS[0][1]:
        tenor, years = KEY_RATE_TENORS[0]
        return [(tenor, years, 1.0)]

    if maturity_years >= KEY_RATE_TENORS[-1][1]:
        tenor, years = KEY_RATE_TENORS[-1]
        return [(tenor, years, 1.0)]

    for index in range(1, len(KEY_RATE_TENORS)):
        upper_tenor, upper_years = (
            KEY_RATE_TENORS[index]
        )
        lower_tenor, lower_years = (
            KEY_RATE_TENORS[index - 1]
        )

        if maturity_years <= upper_years:
            upper_weight = (
                maturity_years - lower_years
            ) / (
                upper_years - lower_years
            )

            lower_weight = 1.0 - upper_weight

            return [
                (
                    lower_tenor,
                    lower_years,
                    lower_weight,
                ),
                (
                    upper_tenor,
                    upper_years,
                    upper_weight,
                ),
            ]

    raise RuntimeError(
        "Unable to calculate key-rate weights"
    )


def calculate_risk_decomposition(
    *,
    prices: list[LatestBondPrice],
    request: RiskDecompositionRequest,
) -> RiskDecompositionResponse:
    valid_prices = [
        price
        for price in prices
        if (
            price.quality_status == "VALID"
            and price.quality_score >= 0.80
        )
    ]

    instruments: list[
        InstrumentRiskDecomposition
    ] = []

    portfolio_key_rates: dict[
        tuple[str, float],
        dict[str, float],
    ] = defaultdict(
        lambda: {
            "duration": 0.0,
            "dv01": 0.0,
        }
    )

    total_market_value = 0.0
    total_dv01 = 0.0
    total_cs01 = 0.0

    for price in valid_prices:
        market_value = (
            request.position_notional
            * price.clean_price
            / 100.0
        )

        aggregate_dv01 = (
            market_value
            * price.modified_duration
            * 0.0001
        )

        # Parallel 1 bp credit-spread move.
        cs01 = aggregate_dv01

        maturity_years = (
            maturity_proxy_from_duration(
                price.modified_duration
            )
        )

        exposures: list[
            KeyRateExposure
        ] = []

        for (
            tenor,
            tenor_years,
            weight,
        ) in key_rate_weights(
            maturity_years
        ):
            key_rate_duration = (
                price.modified_duration
                * weight
            )

            key_rate_dv01 = (
                aggregate_dv01
                * weight
            )

            exposures.append(
                KeyRateExposure(
                    tenor=tenor,
                    tenor_years=tenor_years,
                    key_rate_duration=(
                        key_rate_duration
                    ),
                    key_rate_dv01=(
                        key_rate_dv01
                    ),
                )
            )

            key = (
                tenor,
                tenor_years,
            )

            portfolio_key_rates[
                key
            ]["duration"] += (
                key_rate_duration
            )

            portfolio_key_rates[
                key
            ]["dv01"] += (
                key_rate_dv01
            )

        instruments.append(
            InstrumentRiskDecomposition(
                instrument_id=(
                    price.instrument_id
                ),
                clean_price=(
                    price.clean_price
                ),
                modified_duration=(
                    price.modified_duration
                ),
                g_spread_bps=(
                    price.g_spread_bps
                ),
                position_notional=(
                    request.position_notional
                ),
                market_value=market_value,
                aggregate_dv01=aggregate_dv01,
                cs01=cs01,
                key_rate_exposures=exposures,
            )
        )

        total_market_value += market_value
        total_dv01 += aggregate_dv01
        total_cs01 += cs01

    portfolio_exposures = [
        KeyRateExposure(
            tenor=tenor,
            tenor_years=tenor_years,
            key_rate_duration=values[
                "duration"
            ],
            key_rate_dv01=values[
                "dv01"
            ],
        )
        for (
            tenor,
            tenor_years,
        ), values in sorted(
            portfolio_key_rates.items(),
            key=lambda item: item[0][1],
        )
    ]

    return RiskDecompositionResponse(
        instrument_count=len(instruments),
        position_notional_per_instrument=(
            request.position_notional
        ),
        total_market_value=(
            total_market_value
        ),
        total_dv01=total_dv01,
        total_cs01=total_cs01,
        portfolio_key_rate_dv01=(
            portfolio_exposures
        ),
        instruments=instruments,
    )
