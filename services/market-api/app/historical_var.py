from __future__ import annotations

import math
import random
import statistics

from .models import (
    HistoricalVarInstrumentContribution,
    HistoricalVarObservation,
    HistoricalVarRequest,
    HistoricalVarResponse,
    LatestBondPrice,
    RiskDecompositionRequest,
)
from .risk_decomposition import (
    calculate_risk_decomposition,
)


def percentile(
    values: list[float],
    probability: float,
) -> float:
    if not values:
        return 0.0

    ordered = sorted(values)

    if len(ordered) == 1:
        return ordered[0]

    position = probability * (len(ordered) - 1)
    lower_index = math.floor(position)
    upper_index = math.ceil(position)

    if lower_index == upper_index:
        return ordered[lower_index]

    lower_value = ordered[lower_index]
    upper_value = ordered[upper_index]
    fraction = position - lower_index

    return (
        lower_value
        + fraction
        * (upper_value - lower_value)
    )


def generate_historical_shocks(
    *,
    lookback_days: int,
    seed: int,
) -> list[tuple[float, float]]:
    rng = random.Random(seed)

    shocks: list[tuple[float, float]] = []

    previous_rate_shock = 0.0
    previous_credit_shock = 0.0

    for _ in range(lookback_days):
        market_regime = rng.random()

        if market_regime < 0.03:
            rate_volatility = 18.0
            credit_volatility = 28.0
            correlation = 0.55
        elif market_regime < 0.15:
            rate_volatility = 11.0
            credit_volatility = 17.0
            correlation = 0.35
        else:
            rate_volatility = 6.0
            credit_volatility = 9.0
            correlation = 0.20

        common_factor = rng.gauss(0.0, 1.0)
        independent_rate = rng.gauss(0.0, 1.0)
        independent_credit = rng.gauss(0.0, 1.0)

        rate_innovation = rate_volatility * (
            correlation * common_factor
            + math.sqrt(
                max(
                    0.0,
                    1.0 - correlation**2,
                )
            )
            * independent_rate
        )

        credit_innovation = credit_volatility * (
            correlation * common_factor
            + math.sqrt(
                max(
                    0.0,
                    1.0 - correlation**2,
                )
            )
            * independent_credit
        )

        rate_shock = (
            0.12 * previous_rate_shock
            + rate_innovation
        )

        credit_shock = (
            0.18 * previous_credit_shock
            + credit_innovation
        )

        previous_rate_shock = rate_shock
        previous_credit_shock = credit_shock

        shocks.append(
            (
                rate_shock,
                credit_shock,
            )
        )

    return shocks


def calculate_historical_var(
    *,
    prices: list[LatestBondPrice],
    request: HistoricalVarRequest,
) -> HistoricalVarResponse:
    decomposition = calculate_risk_decomposition(
        prices=prices,
        request=RiskDecompositionRequest(
            instrument_ids=request.instrument_ids,
            position_notional=(
                request.position_notional
            ),
        ),
    )

    shocks = generate_historical_shocks(
        lookback_days=request.lookback_days,
        seed=request.seed,
    )

    observations: list[
        HistoricalVarObservation
    ] = []

    instrument_pnl_history: dict[
        int,
        list[float],
    ] = {
        instrument.instrument_id: []
        for instrument
        in decomposition.instruments
    }

    portfolio_pnls: list[float] = []

    for index, (
        treasury_shock_bps,
        credit_shock_bps,
    ) in enumerate(shocks):
        portfolio_pnl = 0.0

        for instrument in decomposition.instruments:
            instrument_pnl = (
                -instrument.aggregate_dv01
                * treasury_shock_bps
                - instrument.cs01
                * credit_shock_bps
            )

            instrument_pnl_history[
                instrument.instrument_id
            ].append(instrument_pnl)

            portfolio_pnl += instrument_pnl

        portfolio_pnls.append(portfolio_pnl)

        observations.append(
            HistoricalVarObservation(
                observation_index=index,
                treasury_shock_bps=(
                    treasury_shock_bps
                ),
                credit_shock_bps=(
                    credit_shock_bps
                ),
                portfolio_pnl=portfolio_pnl,
            )
        )

    loss_quantile_probability = (
        1.0 - request.confidence_level
    )

    pnl_cutoff = percentile(
        portfolio_pnls,
        loss_quantile_probability,
    )

    value_at_risk = max(
        0.0,
        -pnl_cutoff,
    )

    tail_losses = [
        pnl
        for pnl in portfolio_pnls
        if pnl <= pnl_cutoff
    ]

    expected_shortfall = (
        max(
            0.0,
            -statistics.mean(tail_losses),
        )
        if tail_losses
        else value_at_risk
    )

    average_daily_pnl = (
        statistics.mean(portfolio_pnls)
        if portfolio_pnls
        else 0.0
    )

    pnl_volatility = (
        statistics.stdev(portfolio_pnls)
        if len(portfolio_pnls) > 1
        else 0.0
    )

    worst_historical_loss = (
        max(
            0.0,
            -min(portfolio_pnls),
        )
        if portfolio_pnls
        else 0.0
    )

    contributions: list[
        HistoricalVarInstrumentContribution
    ] = []

    portfolio_tail_indices = {
        index
        for index, pnl in enumerate(
            portfolio_pnls
        )
        if pnl <= pnl_cutoff
    }

    for instrument in decomposition.instruments:
        instrument_history = (
            instrument_pnl_history[
                instrument.instrument_id
            ]
        )

        tail_values = [
            pnl
            for index, pnl in enumerate(
                instrument_history
            )
            if index in portfolio_tail_indices
        ]

        contribution = (
            max(
                0.0,
                -statistics.mean(tail_values),
            )
            if tail_values
            else 0.0
        )

        contributions.append(
            HistoricalVarInstrumentContribution(
                instrument_id=(
                    instrument.instrument_id
                ),
                market_value=(
                    instrument.market_value
                ),
                dv01=(
                    instrument.aggregate_dv01
                ),
                cs01=instrument.cs01,
                var_contribution=contribution,
            )
        )

    contributions.sort(
        key=lambda item:
            item.var_contribution,
        reverse=True,
    )

    observations.sort(
        key=lambda item:
            item.portfolio_pnl,
    )

    return HistoricalVarResponse(
        instrument_count=(
            len(decomposition.instruments)
        ),
        observation_count=len(observations),
        confidence_level=(
            request.confidence_level
        ),
        total_market_value=(
            decomposition.total_market_value
        ),
        value_at_risk=value_at_risk,
        expected_shortfall=expected_shortfall,
        worst_historical_loss=(
            worst_historical_loss
        ),
        average_daily_pnl=average_daily_pnl,
        pnl_volatility=pnl_volatility,
        observations=observations[:50],
        instrument_contributions=(
            contributions
        ),
    )
