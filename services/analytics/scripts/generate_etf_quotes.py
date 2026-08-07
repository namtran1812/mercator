from __future__ import annotations

import os
import random
import uuid
from datetime import datetime, timezone

import psycopg
import requests
from psycopg.rows import dict_row


POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "postgresql://mercator:mercator@localhost:5433/mercator",
)

CLICKHOUSE_URL = os.getenv(
    "CLICKHOUSE_URL",
    "http://localhost:8123",
)

CLICKHOUSE_DATABASE = os.getenv(
    "CLICKHOUSE_DATABASE",
    "mercator",
)

CLICKHOUSE_USERNAME = os.getenv(
    "CLICKHOUSE_USERNAME",
    "default",
)

CLICKHOUSE_PASSWORD = os.getenv(
    "CLICKHOUSE_PASSWORD",
    "",
)


def main() -> None:
    random.seed(20260807)

    with psycopg.connect(
        POSTGRES_DSN,
        row_factory=dict_row,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    instrument_id,
                    nav
                FROM fixed_income_etf_versions
                WHERE valid_to IS NULL
                  AND recorded_to IS NULL
                ORDER BY instrument_id
                """
            )

            etfs = cursor.fetchall()

    print(
        f"Generating quotes for {len(etfs)} ETFs"
    )

    rows = []

    now = datetime.now(
        timezone.utc,
    )

    event_time = now.strftime(
        "%Y-%m-%d %H:%M:%S.%f"
    )

    for etf in etfs:
        instrument_id = int(
            etf["instrument_id"]
        )

        nav = float(
            etf["nav"]
        )

        #
        # Synthetic secondary-market ETF price.
        #
        # Keep the mid close to NAV but allow a small
        # premium/discount.
        #
        premium_discount_bps = random.uniform(
            -20.0,
            20.0,
        )

        mid = nav * (
            1.0
            + premium_discount_bps
            / 10_000.0
        )

        #
        # Synthetic bid/ask width of approximately
        # 2–12 basis points.
        #
        spread_bps = random.uniform(
            2.0,
            12.0,
        )

        half_spread = (
            mid
            * spread_bps
            / 10_000.0
            / 2.0
        )

        bid = mid - half_spread
        ask = mid + half_spread

        quote_id = str(
            uuid.uuid4()
        )

        evaluation_id = str(
            uuid.uuid4()
        )

        rows.append(
            "\t".join(
                [
                    event_time,
                    quote_id,
                    "synthetic-etf-quote",
                    str(instrument_id),
                    f"{bid:.8f}",
                    f"{ask:.8f}",
                    f"{mid:.8f}",
                    "0.95",
                    "1",
                    "",
                    evaluation_id,
                ]
            )
        )

    payload = (
        "\n".join(rows)
        + "\n"
    )

    query = (
        f"INSERT INTO {CLICKHOUSE_DATABASE}.market_quotes "
        "("
        "event_time, "
        "quote_id, "
        "source, "
        "instrument_id, "
        "bid, "
        "ask, "
        "mid, "
        "source_reliability, "
        "accepted, "
        "rejection_reason, "
        "evaluation_id"
        ") "
        "FORMAT TabSeparated"
    )

    response = requests.post(
        CLICKHOUSE_URL,
        params={
            "query": query,
        },
        data=payload.encode(),
        auth=(
            CLICKHOUSE_USERNAME,
            CLICKHOUSE_PASSWORD,
        ),
        timeout=30,
    )

    if not response.ok:
        print()
        print("CLICKHOUSE ERROR")
        print("=" * 80)
        print(response.text)
        print("=" * 80)

    response.raise_for_status()

    print(
        f"Inserted {len(rows)} ETF quotes."
    )


if __name__ == "__main__":
    main()
