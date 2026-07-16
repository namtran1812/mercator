from __future__ import annotations

import json
import os
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
    limit: int = 250,
) -> list[dict[str, object]]:
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
        GROUP BY instrument_id
        ORDER BY instrument_id
        LIMIT {limit:UInt32}
        """,
        parameters={"limit": limit},
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


def apply_curve_update(
    base: dict[str, object],
    event: CurveUpdate,
) -> StreamingPrice:
    rate_change = event.new_rate - event.old_rate

    duration = float(base["modified_duration"])
    convexity = float(base["convexity"])
    clean_price = float(base["clean_price"])
    dirty_price = float(base["dirty_price"])

    percentage_change = (
        -duration * rate_change
        + 0.5
        * convexity
        * rate_change
        * rate_change
    )

    shocked_clean_price = (
        clean_price * (1.0 + percentage_change)
    )

    shocked_dirty_price = (
        dirty_price * (1.0 + percentage_change)
    )

    return StreamingPrice(
        instrument_id=int(base["instrument_id"]),
        clean_price=shocked_clean_price,
        dirty_price=shocked_dirty_price,
        yield_to_maturity=(
            float(base["yield_to_maturity"])
            + rate_change
        ),
        g_spread_bps=float(base["g_spread_bps"]),
        modified_duration=duration,
        convexity=convexity,
        curve_version=event.curve_version,
        quality_status=str(base["quality_status"]),
        event_time=datetime.now(timezone.utc),
        price_change=(
            shocked_clean_price - clean_price
        ),
        source_event_id=event.event_id,
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
            "group.id": "mercator-streaming-pricer",
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

            base_prices = load_latest_prices(
                clickhouse
            )

            for base in base_prices:
                price = apply_curve_update(
                    base,
                    event,
                )

                payload = price.model_dump_json()

                redis.set(
                    f"mercator:price:{price.instrument_id}",
                    payload,
                )

                redis.publish(
                    REDIS_CHANNEL,
                    payload,
                )

            print(
                f"Curve v{event.curve_version}: "
                f"{event.tenor}, "
                f"published {len(base_prices)} prices"
            )

    finally:
        consumer.close()


if __name__ == "__main__":
    main()
