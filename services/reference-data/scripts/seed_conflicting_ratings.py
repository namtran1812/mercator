from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import psycopg

POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "postgresql://mercator:mercator@localhost:5432/mercator",
)


def main() -> None:
    now = datetime.now(timezone.utc)

    observations = [
        (
            1,
            "rating",
            "BBB+",
            "rating-agency-a",
            now,
            None,
            uuid.uuid4(),
        ),
        (
            1,
            "rating",
            "BBB+",
            "rating-agency-b",
            now,
            None,
            uuid.uuid4(),
        ),
        (
            1,
            "rating",
            "A-",
            "vendor-a",
            now,
            None,
            uuid.uuid4(),
        ),
    ]

    with psycopg.connect(POSTGRES_DSN) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM reference_observations
                WHERE instrument_id = 1
                  AND field_name = 'rating'
                """
            )

            cursor.executemany(
                """
                INSERT INTO reference_observations (
                    instrument_id,
                    field_name,
                    field_value,
                    source_name,
                    valid_from,
                    valid_to,
                    source_event_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                observations,
            )

        connection.commit()

    print("Seeded conflicting rating observations.")


if __name__ == "__main__":
    main()
