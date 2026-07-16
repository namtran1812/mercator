from __future__ import annotations

import os
import random
import uuid
from datetime import date, datetime, timedelta, timezone

import psycopg

POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "postgresql://mercator:mercator@localhost:5432/mercator",
)

ISSUERS = [
    "Apex Technologies",
    "Northstar Energy",
    "Meridian Financial",
    "Atlas Industrial",
    "Helios Healthcare",
    "Orion Communications",
    "Summit Consumer",
    "Lattice Software",
    "Harbor Utilities",
    "Vanguard Transportation",
]

SECTORS = [
    "Technology",
    "Energy",
    "Financials",
    "Industrials",
    "Healthcare",
    "Communications",
    "Consumer",
    "Utilities",
]

RATINGS = ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-"]


def random_cusip(index: int) -> str:
    return f"{index:09d}"[-9:]


def random_isin(index: int) -> str:
    return f"US{index:010d}"[-12:]


def generate_bond(index: int) -> tuple:
    today = date.today()
    maturity = today + timedelta(days=random.randint(365, 30 * 365))

    return (
        index,
        "CORPORATE_BOND",
        random_cusip(index),
        random_isin(index),
        None,
        random.choice(ISSUERS),
        round(random.uniform(1.0, 8.0), 4),
        maturity,
        random.choice(RATINGS),
        random.choice(SECTORS),
        "USD",
        datetime.now(timezone.utc),
        None,
        datetime.now(timezone.utc),
        None,
        "synthetic-generator",
        100,
        uuid.uuid4(),
    )


def generate_etf(index: int) -> tuple:
    return (
        index,
        "FIXED_INCOME_ETF",
        None,
        None,
        f"MFI{index % 1000:03d}",
        f"Mercator Fixed Income ETF {index}",
        None,
        None,
        random.choice(RATINGS),
        random.choice(SECTORS),
        "USD",
        datetime.now(timezone.utc),
        None,
        datetime.now(timezone.utc),
        None,
        "synthetic-generator",
        100,
        uuid.uuid4(),
    )


def main() -> None:
    random.seed(42)

    instruments = []

    for index in range(1, 9501):
        instruments.append(generate_bond(index))

    for index in range(9501, 10001):
        instruments.append(generate_etf(index))

    insert_sql = """
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
        VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (source_event_id) DO NOTHING
    """

    with psycopg.connect(POSTGRES_DSN) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM instrument_versions WHERE source = %s",
                ("synthetic-generator",),
            )
            cursor.executemany(insert_sql, instruments)

        connection.commit()

    print(f"Loaded {len(instruments):,} synthetic instruments.")


if __name__ == "__main__":
    main()
