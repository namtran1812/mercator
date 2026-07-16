from __future__ import annotations

from .models import (
    LatestBondPrice,
    PortfolioRiskRequest,
    PortfolioRiskResponse,
    PositionRisk,
)


def calculate_portfolio_risk(
    prices: list[LatestBondPrice],
    request: PortfolioRiskRequest,
) -> PortfolioRiskResponse:
    prices_by_id = {
        price.instrument_id: price
        for price in prices
    }

    requested_face_values = {
        position.instrument_id:
            position.face_value
        for position in request.positions
    }

    preliminary: list[
        tuple[
            LatestBondPrice,
            float,
            float,
            float,
            float,
        ]
    ] = []

    for instrument_id, face_value in (
        requested_face_values.items()
    ):
        price = prices_by_id.get(instrument_id)

        if price is None:
            continue

        market_value = (
            price.clean_price
            / 100.0
            * face_value
        )

        dv01 = (
            price.modified_duration
            * market_value
            / 10_000.0
        )

        convexity_contribution = (
            price.convexity
            * market_value
            / 100_000_000.0
        )

        preliminary.append(
            (
                price,
                face_value,
                market_value,
                dv01,
                convexity_contribution,
            )
        )

    total_market_value = sum(
        item[2]
        for item in preliminary
    )

    total_face_value = sum(
        item[1]
        for item in preliminary
    )

    positions: list[PositionRisk] = []

    for (
        price,
        face_value,
        market_value,
        dv01,
        convexity_contribution,
    ) in preliminary:
        weight = (
            market_value / total_market_value
            if total_market_value > 0.0
            else 0.0
        )

        positions.append(
            PositionRisk(
                instrument_id=price.instrument_id,
                face_value=face_value,
                clean_price=price.clean_price,
                market_value=market_value,
                yield_to_maturity=(
                    price.yield_to_maturity
                ),
                g_spread_bps=(
                    price.g_spread_bps
                ),
                modified_duration=(
                    price.modified_duration
                ),
                convexity=price.convexity,
                dv01=dv01,
                convexity_contribution=(
                    convexity_contribution
                ),
                market_value_weight=weight,
            )
        )

    positions.sort(
        key=lambda position:
            position.market_value,
        reverse=True,
    )

    def weighted_average(
        attribute: str,
    ) -> float:
        return sum(
            getattr(position, attribute)
            * position.market_value_weight
            for position in positions
        )

    return PortfolioRiskResponse(
        position_count=len(positions),
        total_face_value=total_face_value,
        total_market_value=total_market_value,
        weighted_yield_to_maturity=(
            weighted_average(
                "yield_to_maturity"
            )
        ),
        weighted_g_spread_bps=(
            weighted_average(
                "g_spread_bps"
            )
        ),
        weighted_modified_duration=(
            weighted_average(
                "modified_duration"
            )
        ),
        weighted_convexity=(
            weighted_average(
                "convexity"
            )
        ),
        total_dv01=sum(
            position.dv01
            for position in positions
        ),
        total_convexity_contribution=sum(
            position.convexity_contribution
            for position in positions
        ),
        positions=positions,
    )
