from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import clickhouse_connect

INPUT_PATH = Path("artifacts/evaluated-prices.jsonl")


def from_epoch_microseconds(value: int) -> datetime:
    return datetime.fromtimestamp(
        value / 1_000_000,
        tz=timezone.utc,
    )


def stable_uuid(value: str) -> str:
    return str(uuid5(NAMESPACE_URL, value))


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(INPUT_PATH)

    client = clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USERNAME", "mercator"),
        password=os.getenv("CLICKHOUSE_PASSWORD", "mercator"),
        database=os.getenv("CLICKHOUSE_DATABASE", "mercator"),
    )

    rows: list[list[object]] = []

    with INPUT_PATH.open() as input_file:
        for line in input_file:
            record = json.loads(line)

            rows.append(
                [
                    from_epoch_microseconds(record["event_time_us"]),
                    from_epoch_microseconds(record["received_time_us"]),
                    record["instrument_id"],
                    record["clean_price"],
                    record["dirty_price"],
                    record["yield_to_maturity"],
                    record["g_spread_bps"],
                    record["modified_duration"],
                    record["convexity"],
                    record["reference_version"],
                    record["curve_version"],
                    record["model_version"],
                    record["quality_status"],
                    record["quality_score"],
                    stable_uuid(record["calculation_trace_id"]),
                    stable_uuid(record["source_event_id"]),
                ]
            )

    client.insert(
        "evaluated_prices",
        rows,
        column_names=[
            "event_time",
            "received_time",
            "instrument_id",
            "clean_price",
            "dirty_price",
            "yield_to_maturity",
            "g_spread_bps",
            "modified_duration",
            "convexity",
            "reference_version",
            "curve_version",
            "model_version",
            "quality_status",
            "quality_score",
            "calculation_trace_id",
            "source_event_id",
        ],
    )

    print(f"Inserted {len(rows):,} evaluated prices.")


if __name__ == "__main__":
    main()
