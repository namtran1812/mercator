from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone

import clickhouse_connect
from confluent_kafka import Consumer
from redis import Redis

from .models import CurveUpdate, StreamingPrice

TOPIC = "market.curves.v1"
REDIS_CHANNEL = "mercator:price-updates"


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
    client,
    instrument_ids: list[int],
) -> list[dict[str, object]]:
    if not instrument_ids:
        return []

    result = client.query(
        """
        SELECT
            instrument_id,
            argMax(clean_price, event_time),
            argMax(dirty_price, event_time),
            argMax(yield_to_maturity, event_time),
            argMax(g_spread_bps, event_time),
            argMax(modified_duration, event_time),
            argMax(convexity, event_time),
            argMax(quality_status, event_time)
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
        {
            "instrument_id": row[0],
            "clean_price": row[1],
            "dirty_price": row[2],
            "yield_to_maturity": row[3],
            "g_spread_bps": row[4],
            "modified_duration": row[5],
            "convexity": row[6],
            "quality_status": row[7],
        }
        for row in result.result_rows
    ]


def affected_instruments(
    redis: Redis,
    event: CurveUpdate,
) -> list[int]:
    key = (
        "mercator:dependencies:"
        f"UST:{event.tenor}"
    )

    values = redis.smembers(key)

    return sorted(
        int(value)
        for value in values
    )


def dependency_weight(
    redis: Redis,
    instrument_id: int,
    tenor: str,
) -> float:
    key = (
        "mercator:dependency-weight:"
        f"{instrument_id}:UST:{tenor}"
    )

    value = redis.get(key)

    return float(value) if value is not None else 1.0


def apply_curve_update(
    base: dict[str, object],
    event: CurveUpdate,
    weight: float,
) -> StreamingPrice:
    raw_rate_change = (
        event.new_rate - event.old_rate
    )

    effective_rate_change = (
        raw_rate_change * weight
    )

    duration = float(
        base["modified_duration"]
    )

    convexity = float(
        base["convexity"]
    )

    clean_price = float(
        base["clean_price"]
    )

    dirty_price = float(
        base["dirty_price"]
    )

    percentage_change = (
        -duration * effective_rate_change
        + 0.5
        * convexity
        * effective_rate_change
        * effective_rate_change
    )

    shocked_clean_price = (
        clean_price *
        (1.0 + percentage_change)
    )

    shocked_dirty_price = (
        dirty_price *
        (1.0 + percentage_change)
    )

    return StreamingPrice(
        instrument_id=int(
            base["instrument_id"]
        ),
        clean_price=shocked_clean_price,
        dirty_price=shocked_dirty_price,
        yield_to_maturity=(
            float(base["yield_to_maturity"])
            + effective_rate_change
        ),
        g_spread_bps=float(
            base["g_spread_bps"]
        ),
        modified_duration=duration,
        convexity=convexity,
        curve_version=event.curve_version,
        quality_status=str(
            base["quality_status"]
        ),
        event_time=datetime.now(
            timezone.utc
        ),
        price_change=(
            shocked_clean_price -
            clean_price
        ),
        source_event_id=event.event_id,
        dependency_tenor=event.tenor,
        dependency_weight=weight,
    )


def main() -> None:
    redis = Redis.from_url(
        os.getenv(
            "REDIS_URL",
            "redis://localhost:6379/0",
        ),
        decode_responses=True,
    )

    clickhouse = create_clickhouse_client()

    consumer = Consumer(
        {
            "bootstrap.servers": os.getenv(
                "KAFKA_BOOTSTRAP_SERVERS",
                "localhost:9092",
            ),
            "group.id":
                "mercator-selective-streaming-pricer",
            "auto.offset.reset": "latest",
            "enable.auto.commit": True,
        }
    )

    consumer.subscribe([TOPIC])

    print(f"Listening for {TOPIC}")

    try:
        while True:
            message = consumer.poll(1.0)

            if message is None:
                continue

            if message.error():
                print(message.error())
                continue

            event = CurveUpdate.model_validate_json(
                message.value()
            )

            start = time.perf_counter()

            instrument_ids = affected_instruments(
                redis,
                event,
            )

            base_prices = load_latest_prices(
                clickhouse,
                instrument_ids,
            )

            pipeline = redis.pipeline(
                transaction=False
            )

            published = 0

            for base in base_prices:
                instrument_id = int(
                    base["instrument_id"]
                )

                weight = dependency_weight(
                    redis,
                    instrument_id,
                    event.tenor,
                )

                price = apply_curve_update(
                    base,
                    event,
                    weight,
                )

                payload = (
                    price.model_dump_json()
                )

                pipeline.set(
                    (
                        "mercator:price:"
                        f"{price.instrument_id}"
                    ),
                    payload,
                )

                pipeline.publish(
                    REDIS_CHANNEL,
                    payload,
                )

                published += 1

            pipeline.execute()

            elapsed_ms = (
                time.perf_counter() - start
            ) * 1_000.0

            avoided = (
                10_000 - len(instrument_ids)
            )

            print(
                f"Curve v{event.curve_version} "
                f"{event.tenor}: "
                f"affected={len(instrument_ids):,}, "
                f"published={published:,}, "
                f"avoided={avoided:,}, "
                f"latency={elapsed_ms:.2f} ms"
            )

    finally:
        consumer.close()


if __name__ == "__main__":
    main()
