from __future__ import annotations

import os
from typing import Any
from uuid import UUID

import clickhouse_connect

from .models import (
    LiveAccountRisk,
    LivePositionRisk,
)


def create_clickhouse_client():
    return clickhouse_connect.get_client(
        host=os.getenv(
            "CLICKHOUSE_HOST",
            "localhost",
        ),
        port=int(
            os.getenv(
                "CLICKHOUSE_PORT",
                "8123",
            )
        ),
        username=os.getenv(
            "CLICKHOUSE_USERNAME",
            "mercator",
        ),
        password=os.getenv(
            "CLICKHOUSE_PASSWORD",
            "mercator",
        ),
        database=os.getenv(
            "CLICKHOUSE_DATABASE",
            "mercator",
        ),
    )


def load_latest_prices(
    instrument_ids: list[int],
) -> dict[int, dict[str, Any]]:
    if not instrument_ids:
        return {}

    client = create_clickhouse_client()

    result = client.query(
        """
        SELECT
            instrument_id,
            argMax(clean_price, event_time)
                AS clean_price,
            argMax(yield_to_maturity, event_time)
                AS yield_to_maturity,
            argMax(g_spread_bps, event_time)
                AS g_spread_bps,
            argMax(modified_duration, event_time)
                AS modified_duration,
            argMax(convexity, event_time)
                AS convexity,
            argMax(quality_status, event_time)
                AS quality_status,
            argMax(curve_version, event_time)
                AS curve_version,
            argMax(reference_version, event_time)
                AS reference_version
        FROM evaluated_prices
        WHERE instrument_id IN
            {instrument_ids:Array(UInt64)}
        GROUP BY instrument_id
        """,
        parameters={
            "instrument_ids": instrument_ids,
        },
    )

    return {
        int(row[0]): {
            "clean_price": float(row[1]),
            "yield_to_maturity": float(row[2]),
            "g_spread_bps": float(row[3]),
            "modified_duration": float(row[4]),
            "convexity": float(row[5]),
            "quality_status": str(row[6]),
            "curve_version": int(row[7]),
            "reference_version": int(row[8]),
        }
        for row in result.result_rows
    }


def calculate_live_account_risk(
    *,
    account: dict[str, Any],
    position_rows: list[dict[str, Any]],
) -> LiveAccountRisk:
    instrument_ids = [
        int(row["instrument_id"])
        for row in position_rows
    ]

    prices = load_latest_prices(
        instrument_ids
    )

    positions: list[LivePositionRisk] = []

    for row in position_rows:
        instrument_id = int(
            row["instrument_id"]
        )

        price = prices.get(instrument_id)

        if price is None:
            continue

        face_value = float(
            row["face_value"]
        )

        average_cost = float(
            row["average_cost"]
        )

        realized_pnl = float(
            row["realized_pnl"]
        )

        current_clean_price = float(
            price["clean_price"]
        )

        cost_basis = (
            average_cost
            / 100.0
            * face_value
        )

        market_value = (
            current_clean_price
            / 100.0
            * face_value
        )

        unrealized_pnl = (
            market_value - cost_basis
        )

        total_pnl = (
            unrealized_pnl
            + realized_pnl
        )

        dv01 = (
            float(
                price["modified_duration"]
            )
            * market_value
            / 10_000.0
        )

        positions.append(
            LivePositionRisk(
                account_id=account[
                    "account_id"
                ],
                instrument_id=instrument_id,
                face_value=face_value,
                average_cost=average_cost,
                current_clean_price=(
                    current_clean_price
                ),
                cost_basis=cost_basis,
                market_value=market_value,
                unrealized_pnl=(
                    unrealized_pnl
                ),
                realized_pnl=realized_pnl,
                total_pnl=total_pnl,
                yield_to_maturity=float(
                    price[
                        "yield_to_maturity"
                    ]
                ),
                g_spread_bps=float(
                    price["g_spread_bps"]
                ),
                modified_duration=float(
                    price[
                        "modified_duration"
                    ]
                ),
                convexity=float(
                    price["convexity"]
                ),
                dv01=dv01,
                quality_status=str(
                    price[
                        "quality_status"
                    ]
                ),
                curve_version=int(
                    price["curve_version"]
                ),
                reference_version=int(
                    price[
                        "reference_version"
                    ]
                ),
            )
        )

    positions.sort(
        key=lambda item:
            abs(item.market_value),
        reverse=True,
    )

    total_market_value = sum(
        position.market_value
        for position in positions
    )

    total_cost_basis = sum(
        position.cost_basis
        for position in positions
    )

    total_unrealized_pnl = sum(
        position.unrealized_pnl
        for position in positions
    )

    total_realized_pnl = sum(
        position.realized_pnl
        for position in positions
    )

    total_face_value = sum(
        position.face_value
        for position in positions
    )

    total_dv01 = sum(
        position.dv01
        for position in positions
    )

    denominator = sum(
        abs(position.market_value)
        for position in positions
    )

    def weighted(
        attribute: str,
    ) -> float:
        if denominator == 0.0:
            return 0.0

        return sum(
            getattr(
                position,
                attribute,
            )
            * abs(
                position.market_value
            )
            / denominator
            for position in positions
        )

    cash_balance = float(
        account["cash_balance"]
    )

    total_pnl = (
        total_unrealized_pnl
        + total_realized_pnl
    )

    return LiveAccountRisk(
        account_id=account["account_id"],
        account_name=account[
            "account_name"
        ],
        cash_balance=cash_balance,
        position_count=len(positions),
        total_face_value=(
            total_face_value
        ),
        total_cost_basis=(
            total_cost_basis
        ),
        total_market_value=(
            total_market_value
        ),
        total_unrealized_pnl=(
            total_unrealized_pnl
        ),
        total_realized_pnl=(
            total_realized_pnl
        ),
        total_pnl=total_pnl,
        weighted_yield_to_maturity=(
            weighted(
                "yield_to_maturity"
            )
        ),
        weighted_g_spread_bps=(
            weighted(
                "g_spread_bps"
            )
        ),
        weighted_modified_duration=(
            weighted(
                "modified_duration"
            )
        ),
        weighted_convexity=(
            weighted("convexity")
        ),
        total_dv01=total_dv01,
        net_liquidation_value=(
            cash_balance
            + total_market_value
        ),
        positions=positions,
    )
