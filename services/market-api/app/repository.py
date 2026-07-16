from __future__ import annotations

import clickhouse_connect

from .config import (
    CLICKHOUSE_DATABASE,
    CLICKHOUSE_HOST,
    CLICKHOUSE_PASSWORD,
    CLICKHOUSE_PORT,
    CLICKHOUSE_USERNAME,
)
from .models import LatestBondPrice, MarketSummary, PriceHistoryPoint


class MarketRepository:
    def __init__(self) -> None:
        self._client = clickhouse_connect.get_client(
            host=CLICKHOUSE_HOST,
            port=CLICKHOUSE_PORT,
            username=CLICKHOUSE_USERNAME,
            password=CLICKHOUSE_PASSWORD,
            database=CLICKHOUSE_DATABASE,
        )

    def latest_prices(
        self,
        *,
        limit: int,
        minimum_quality_score: float,
    ) -> list[LatestBondPrice]:
        result = self._client.query(
            """
            SELECT
                instrument_id,

                argMax(clean_price, event_time)
                    AS clean_price,

                argMax(dirty_price, event_time)
                    AS dirty_price,

                argMax(yield_to_maturity, event_time)
                    AS yield_to_maturity,

                argMax(g_spread_bps, event_time)
                    AS g_spread_bps,

                argMax(modified_duration, event_time)
                    AS modified_duration,

                argMax(convexity, event_time)
                    AS convexity,

                argMax(quality_score, event_time)
                    AS quality_score,

                argMax(quality_status, event_time)
                    AS quality_status,

                argMax(curve_version, event_time)
                    AS curve_version,

                argMax(reference_version, event_time)
                    AS reference_version,

                max(event_time)
                    AS latest_event_time

            FROM evaluated_prices

            GROUP BY instrument_id

            HAVING quality_score >=
                {minimum_quality_score:Float64}

            ORDER BY instrument_id

            LIMIT {limit:UInt32}
            """,
            parameters={
                "limit": limit,
                "minimum_quality_score":
                    minimum_quality_score,
            },
        )

        return [
            LatestBondPrice(
                instrument_id=row[0],
                clean_price=row[1],
                dirty_price=row[2],
                yield_to_maturity=row[3],
                g_spread_bps=row[4],
                modified_duration=row[5],
                convexity=row[6],
                quality_score=row[7],
                quality_status=row[8],
                curve_version=row[9],
                reference_version=row[10],
                event_time=row[11],
            )
            for row in result.result_rows
        ]

    def market_summary(self) -> MarketSummary:
        result = self._client.query(
            """
            WITH latest AS
            (
                SELECT
                    instrument_id,
                    argMax(clean_price, event_time)
                        AS clean_price,
                    argMax(yield_to_maturity, event_time)
                        AS yield_to_maturity,
                    argMax(g_spread_bps, event_time)
                        AS g_spread_bps,
                    argMax(quality_status, event_time)
                        AS quality_status
                FROM evaluated_prices
                GROUP BY instrument_id
            )
            SELECT
                count() AS instrument_count,
                avg(clean_price),
                avg(yield_to_maturity),
                avg(g_spread_bps),
                argMax(
                    instrument_id,
                    g_spread_bps
                ) AS widest_instrument_id,
                max(g_spread_bps)
                    AS widest_g_spread_bps
            FROM latest
            WHERE quality_status = 'VALID'
            """
        )

        row = result.result_rows[0]

        return MarketSummary(
            instrument_count=row[0],
            average_clean_price=row[1] or 0.0,
            average_yield_to_maturity=row[2] or 0.0,
            average_g_spread_bps=row[3] or 0.0,
            widest_instrument_id=row[4],
            widest_g_spread_bps=row[5],
        )

    def price_history(
        self,
        *,
        instrument_id: int,
        limit: int,
    ) -> list[PriceHistoryPoint]:
        result = self._client.query(
            """
            SELECT
                event_time,
                clean_price,
                dirty_price,
                yield_to_maturity,
                g_spread_bps,
                modified_duration,
                convexity,
                quality_score,
                quality_status,
                curve_version,
                reference_version,
                model_version,
                toString(calculation_trace_id),
                toString(source_event_id)
            FROM evaluated_prices
            WHERE instrument_id =
                {instrument_id:UInt64}
            ORDER BY event_time DESC
            LIMIT {limit:UInt32}
            """,
            parameters={
                "instrument_id": instrument_id,
                "limit": limit,
            },
        )

        return [
            PriceHistoryPoint(
                event_time=row[0],
                clean_price=row[1],
                dirty_price=row[2],
                yield_to_maturity=row[3],
                g_spread_bps=row[4],
                modified_duration=row[5],
                convexity=row[6],
                quality_score=row[7],
                quality_status=row[8],
                curve_version=row[9],
                reference_version=row[10],
                model_version=row[11],
                calculation_trace_id=row[12],
                source_event_id=row[13],
            )
            for row in result.result_rows
        ]

    def latest_prices_by_ids(
        self,
        instrument_ids: list[int],
    ) -> list[LatestBondPrice]:
        if not instrument_ids:
            return []

        result = self._client.query(
            """
            SELECT
                instrument_id,
                argMax(clean_price, event_time),
                argMax(dirty_price, event_time),
                argMax(yield_to_maturity, event_time),
                argMax(g_spread_bps, event_time),
                argMax(modified_duration, event_time),
                argMax(convexity, event_time),
                argMax(quality_score, event_time),
                argMax(quality_status, event_time),
                argMax(curve_version, event_time),
                argMax(reference_version, event_time),
                max(event_time)
            FROM evaluated_prices
            WHERE instrument_id IN
                {instrument_ids:Array(UInt64)}
            GROUP BY instrument_id
            ORDER BY instrument_id
            """,
            parameters={
                "instrument_ids": instrument_ids,
            },
        )

        return [
            LatestBondPrice(
                instrument_id=row[0],
                clean_price=row[1],
                dirty_price=row[2],
                yield_to_maturity=row[3],
                g_spread_bps=row[4],
                modified_duration=row[5],
                convexity=row[6],
                quality_score=row[7],
                quality_status=row[8],
                curve_version=row[9],
                reference_version=row[10],
                event_time=row[11],
            )
            for row in result.result_rows
        ]

