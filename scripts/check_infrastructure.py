from __future__ import annotations

import os

import clickhouse_connect
import psycopg
from confluent_kafka.admin import AdminClient
from redis import Redis


def main() -> None:
    postgres_dsn = os.getenv(
        "POSTGRES_DSN",
        "postgresql://mercator:mercator@localhost:5432/mercator",
    )

    with psycopg.connect(postgres_dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            assert cursor.fetchone() == (1,)
    print("PostgreSQL: OK")

    clickhouse = clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USERNAME", "mercator"),
        password=os.getenv("CLICKHOUSE_PASSWORD", "mercator"),
        database=os.getenv("CLICKHOUSE_DATABASE", "mercator"),
    )
    assert clickhouse.command("SELECT 1") == 1
    print("ClickHouse: OK")

    redis = Redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True,
    )
    assert redis.ping()
    print("Redis: OK")

    kafka = AdminClient(
        {
            "bootstrap.servers": os.getenv(
                "KAFKA_BOOTSTRAP_SERVERS",
                "localhost:9092",
            )
        }
    )
    metadata = kafka.list_topics(timeout=10)
    print(f"Kafka: OK ({len(metadata.topics)} topics)")


if __name__ == "__main__":
    main()
