from __future__ import annotations

import json
import os
import sys
import time
import uuid

import requests
from confluent_kafka import Producer
from redis import Redis


KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092",
)

CURVE_TOPIC = os.getenv(
    "CURVE_TOPIC",
    "market.curves.v1",
)

CLICKHOUSE_URL = os.getenv(
    "CLICKHOUSE_URL",
    "http://127.0.0.1:8123",
)

CLICKHOUSE_DATABASE = os.getenv(
    "CLICKHOUSE_DATABASE",
    "mercator",
)

CLICKHOUSE_USERNAME = os.getenv(
    "CLICKHOUSE_USERNAME",
    "mercator",
)

CLICKHOUSE_PASSWORD = os.getenv(
    "CLICKHOUSE_PASSWORD",
    "mercator",
)

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://127.0.0.1:6380/0",
)

TIMEOUT_SECONDS = float(
    os.getenv(
        "E2E_TIMEOUT_SECONDS",
        "30",
    )
)


def fail(message: str) -> None:
    print(
        f"\nFAILED: {message}",
        file=sys.stderr,
    )
    raise SystemExit(1)


def clickhouse_query(
    query: str,
) -> str:
    response = requests.get(
        CLICKHOUSE_URL,
        params={
            "database":
                CLICKHOUSE_DATABASE,
            "query":
                query,
        },
        auth=(
            CLICKHOUSE_USERNAME,
            CLICKHOUSE_PASSWORD,
        ),
        timeout=10,
    )

    response.raise_for_status()

    return response.text.strip()


def latest_curve_version() -> int:
    result = clickhouse_query(
        """
        SELECT max(curve_version)
        FROM evaluated_prices
        """
    )

    if not result:
        return 0

    return int(result)


def publish_event(
    event: dict[str, object],
) -> None:
    producer = Producer({
        "bootstrap.servers":
            KAFKA_BOOTSTRAP_SERVERS,
    })

    producer.produce(
        CURVE_TOPIC,
        key="30Y",
        value=json.dumps(event),
    )

    remaining = producer.flush(10)

    if remaining != 0:
        fail(
            f"{remaining} Kafka messages "
            "were not delivered"
        )


def wait_for_clickhouse(
    event_id: str,
) -> tuple[int, int]:
    deadline = (
        time.time()
        + TIMEOUT_SECONDS
    )

    while time.time() < deadline:
        result = clickhouse_query(
            f"""
            SELECT
                count(),
                uniqExact(instrument_id)
            FROM evaluated_prices
            WHERE source_event_id =
                toUUID('{event_id}')
            """
        )

        parts = result.split()

        if len(parts) == 2:
            rows = int(parts[0])
            instruments = int(parts[1])

            if rows > 0:
                return (
                    rows,
                    instruments,
                )

        time.sleep(0.25)

    fail(
        "timed out waiting for "
        "ClickHouse persistence"
    )


def wait_for_redis(
    redis: Redis,
    event_id: str,
    version: int,
) -> dict[str, object]:
    deadline = (
        time.time()
        + TIMEOUT_SECONDS
    )

    while time.time() < deadline:
        raw = redis.get(
            "mercator:price:1"
        )

        if raw:
            payload = json.loads(
                raw
            )

            if (
                payload.get(
                    "source_event_id"
                )
                == event_id
                and payload.get(
                    "curve_version"
                )
                == version
            ):
                return payload

        time.sleep(0.25)

    fail(
        "timed out waiting for "
        "Redis publication"
    )


def logical_duplicate_count() -> int:
    result = clickhouse_query(
        """
        SELECT count()
        FROM
        (
            SELECT
                source_event_id,
                instrument_id,
                count() AS copies
            FROM evaluated_prices
            GROUP BY
                source_event_id,
                instrument_id
            HAVING copies > 1
        )
        """
    )

    return int(result)


def main() -> None:
    redis = Redis.from_url(
        REDIS_URL,
        decode_responses=True,
    )

    try:
        redis.ping()
    except Exception as error:
        fail(
            f"Redis unavailable: {error}"
        )

    try:
        clickhouse_query(
            "SELECT 1"
        )
    except Exception as error:
        fail(
            f"ClickHouse unavailable: {error}"
        )


    previous_version = (
        latest_curve_version()
    )

    new_version = (
        previous_version + 1
    )

    event_id = str(
        uuid.uuid4()
    )


    print("=" * 60)
    print("MERCATOR PRICING WORKER E2E")
    print("=" * 60)

    print(
        "previous version:",
        previous_version,
    )

    print(
        "new version:",
        new_version,
    )

    print(
        "event:",
        event_id,
    )


    event = {
        "event_id":
            event_id,

        "event_time":
            time.strftime(
                "%Y-%m-%dT%H:%M:%SZ",
                time.gmtime(),
            ),

        "previous_version":
            previous_version,

        "new_version":
            new_version,

        "updates": [
            {
                "node_id":
                    9,

                "maturity_years":
                    30.0,

                "old_rate":
                    0.0497,

                "new_rate":
                    0.0498,
            }
        ],
    }


    print("\nPublishing Kafka event...")

    publish_event(
        event
    )


    rows, instruments = (
        wait_for_clickhouse(
            event_id
        )
    )

    print(
        "ClickHouse rows:",
        rows,
    )

    print(
        "Unique instruments:",
        instruments,
    )


    if rows != instruments:
        fail(
            "ClickHouse contains duplicate "
            "logical instrument results"
        )


    payload = wait_for_redis(
        redis,
        event_id,
        new_version,
    )


    print(
        "Redis curve version:",
        payload.get(
            "curve_version"
        ),
    )

    print(
        "Redis instrument:",
        payload.get(
            "instrument_id"
        ),
    )

    print(
        "Redis price change:",
        payload.get(
            "price_change"
        ),
    )


    duplicates = (
        logical_duplicate_count()
    )

    print(
        "Global logical duplicates:",
        duplicates,
    )


    if duplicates != 0:
        fail(
            "logical duplicate rows exist"
        )


    print()
    print("=" * 60)
    print("PASS")
    print("=" * 60)

    print(
        "Kafka → C++ worker → ClickHouse "
        "→ Redis verified successfully."
    )


if __name__ == "__main__":
    main()
