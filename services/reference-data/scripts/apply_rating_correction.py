from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import psycopg

POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "postgresql://mercator:mercator@localhost:5432/mercator",
)


def main() -> None:
    now = datetime.now(timezone.utc)
    effective_from = now - timedelta(days=7)

    with psycopg.connect(POSTGRES_DSN) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM instrument_versions
                WHERE instrument_id = 1
                  AND recorded_to IS NULL
                ORDER BY recorded_from DESC
                LIMIT 1
                """
            )

            current = cursor.fetchone()

            if current is None:
                raise RuntimeError("Instrument 1 does not exist")

            cursor.execute(
                """
                UPDATE instrument_versions
                SET recorded_to = %s
                WHERE version_id = %s
                """,
                (now, current[0]),
            )

            cursor.execute(
                """
                INSERT INTO instrument_versions (
                    instrument_id,
                    instrument_type,
                    cusip,
                    isin,
                    ticker,
                    issuer_name,
                    coupon_rate,
                    maturity_date,
                    rating,
                    sector,
                    currency,
                    valid_from,
                    valid_to,
                    recorded_from,
                    recorded_to,
                    source,
                    source_priority,
                    source_event_id
                )
                SELECT
                    instrument_id,
                    instrument_type,
                    cusip,
                    isin,
                    ticker,
                    issuer_name,
                    coupon_rate,
                    maturity_date,
                    'BBB+',
                    sector,
                    currency,
                    %s,
                    valid_to,
                    %s,
                    NULL,
                    'ratings-correction-feed',
                    10,
                    %s
                FROM instrument_versions
                WHERE version_id = %s
                """,
                (
                    effective_from,
                    now,
                    uuid.uuid4(),
                    current[0],
                ),
            )

        connection.commit()

    print("Applied rating correction to instrument 1.")
    print(f"Effective from: {effective_from.isoformat()}")
    print(f"Recorded at:   {now.isoformat()}")


if __name__ == "__main__":
    main()
