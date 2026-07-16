from __future__ import annotations

import os

import psycopg
from psycopg.rows import dict_row
from redis import Redis

POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "postgresql://mercator:mercator@localhost:5432/mercator",
)

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0",
)


def main() -> None:
    redis = Redis.from_url(
        REDIS_URL,
        decode_responses=True,
    )

    with psycopg.connect(
        POSTGRES_DSN,
        row_factory=dict_row,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    instrument_id,
                    curve_name,
                    tenor,
                    dependency_weight
                FROM instrument_curve_dependencies
                ORDER BY
                    curve_name,
                    tenor,
                    instrument_id
                """
            )

            rows = cursor.fetchall()

    pipeline = redis.pipeline(transaction=False)

    existing_keys = redis.scan_iter(
        "mercator:dependencies:*"
    )

    keys = list(existing_keys)

    if keys:
        pipeline.delete(*keys)

    for row in rows:
        set_key = (
            "mercator:dependencies:"
            f"{row['curve_name']}:{row['tenor']}"
        )

        weight_key = (
            "mercator:dependency-weight:"
            f"{row['instrument_id']}:"
            f"{row['curve_name']}:"
            f"{row['tenor']}"
        )

        pipeline.sadd(
            set_key,
            row["instrument_id"],
        )

        pipeline.set(
            weight_key,
            row["dependency_weight"],
        )

    pipeline.execute()

    print(
        f"Loaded {len(rows):,} dependencies into Redis."
    )


if __name__ == "__main__":
    main()
