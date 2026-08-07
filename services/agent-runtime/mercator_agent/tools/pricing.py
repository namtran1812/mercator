from __future__ import annotations

import os

import clickhouse_connect

from mercator_agent.state.models import PriceObservation



def _demo_latest_prices(
    instrument_ids: list[int],
) -> list[PriceObservation]:
    return [
        PriceObservation(
            instrument_id=
                instrument_id,

            clean_price=
                760.0
                + (
                    instrument_id
                    * 37
                )
                % 360,

            dirty_price=
                762.0
                + (
                    instrument_id
                    * 37
                )
                % 360,

            yield_to_maturity=
                0.045
                + (
                    instrument_id
                    % 40
                )
                * 0.001,

            g_spread_bps=
                85.0
                + (
                    instrument_id
                    * 29
                )
                % 315,

            modified_duration=
                2.0
                + (
                    instrument_id
                    % 145
                )
                / 10.0,

            quality_score=
                0.95,

            quality_status=
                "VALID",

            curve_version=
                2,

            reference_version=
                1,
        )
        for instrument_id
        in instrument_ids
    ]

def latest_prices(
    instrument_ids: list[int],
) -> list[PriceObservation]:
    if not instrument_ids:
        return []

    demo_mode = (
        os.getenv(
            "MERCATOR_DEMO_MODE",
            "false",
        ).lower()
        in {
            "1",
            "true",
            "yes",
            "on",
        }
    )

    if demo_mode:
        return _demo_latest_prices(
            instrument_ids
        )

    client = clickhouse_connect.get_client(
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

    parameters = {
        "instrument_ids": instrument_ids,
    }

    result = client.query(
        """
        SELECT
            instrument_id,
            argMax(
                clean_price,
                event_time
            ) AS clean_price,
            argMax(
                dirty_price,
                event_time
            ) AS dirty_price,
            argMax(
                yield_to_maturity,
                event_time
            ) AS yield_to_maturity,
            argMax(
                g_spread_bps,
                event_time
            ) AS g_spread_bps,
            argMax(
                modified_duration,
                event_time
            ) AS modified_duration,
            argMax(
                quality_score,
                event_time
            ) AS quality_score,
            argMax(
                quality_status,
                event_time
            ) AS quality_status,
            argMax(
                curve_version,
                event_time
            ) AS curve_version,
            argMax(
                reference_version,
                event_time
            ) AS reference_version
        FROM evaluated_prices
        WHERE instrument_id IN
            {instrument_ids:Array(UInt64)}
        GROUP BY instrument_id
        ORDER BY instrument_id
        """,
        parameters=parameters,
    )

    return [
        PriceObservation(
            instrument_id=row[0],
            clean_price=row[1],
            dirty_price=row[2],
            yield_to_maturity=row[3],
            g_spread_bps=row[4],
            modified_duration=row[5],
            quality_score=row[6],
            quality_status=row[7],
            curve_version=row[8],
            reference_version=row[9],
        )
        for row in result.result_rows
    ]
