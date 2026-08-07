from __future__ import annotations

import os
import random
import uuid
from datetime import datetime, timezone

import psycopg


POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "postgresql://mercator:mercator@localhost:5433/mercator",
)

ETF_COUNT = 20
FIRST_ETF_ID = 10_001

ISSUERS = [
    "Mercator Asset Management",
    "Northstar Funds",
    "Atlas Index Partners",
    "Lattice Capital",
]

BENCHMARKS = [
    "Mercator US Aggregate Bond Index",
    "Mercator Investment Grade Corporate Index",
    "Mercator Short Duration Credit Index",
    "Mercator Long Duration Corporate Index",
]

SECTORS = [
    "Fixed Income ETF",
]

RATINGS = [
    "AAA",
    "AA",
    "A",
]


def main() -> None:
    random.seed(42)

    now = datetime.now(
        timezone.utc,
    )

    with psycopg.connect(
        POSTGRES_DSN,
    ) as connection:

        with connection.cursor() as cursor:

            for offset in range(
                ETF_COUNT
            ):
                instrument_id = (
                    FIRST_ETF_ID
                    + offset
                )

                issuer = random.choice(
                    ISSUERS
                )

                benchmark = random.choice(
                    BENCHMARKS
                )

                ticker = (
                    f"MFI{offset + 1:02d}"
                )

                cusip = (
                    f"ETF{instrument_id:06d}"
                )

                isin = (
                    f"US9{instrument_id:09d}"
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
                    VALUES (
                        %s,
                        'FIXED_INCOME_ETF',
                        %s,
                        %s,
                        %s,
                        %s,
                        NULL,
                        NULL,
                        %s,
                        %s,
                        'USD',
                        %s,
                        NULL,
                        %s,
                        NULL,
                        'synthetic-etf-generator',
                        100,
                        %s
                    )
                    """,
                    (
                        instrument_id,
                        cusip,
                        isin,
                        ticker,
                        issuer,
                        random.choice(
                            RATINGS
                        ),
                        "Fixed Income ETF",
                        now,
                        now,
                        uuid.uuid4(),
                    ),
                )

                cursor.execute(
                    """
                    INSERT INTO fixed_income_etf_versions (
                        instrument_id,
                        fund_name,
                        benchmark_name,
                        expense_ratio,
                        shares_outstanding,
                        nav,
                        valid_from,
                        valid_to,
                        recorded_from,
                        recorded_to,
                        source,
                        source_event_id
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        NULL,
                        %s,
                        NULL,
                        'synthetic-etf-generator',
                        %s
                    )
                    """,
                    (
                        instrument_id,
                        f"{issuer} {benchmark}",
                        benchmark,
                        random.uniform(
                            0.0005,
                            0.0040,
                        ),
                        random.randint(
                            5_000_000,
                            100_000_000,
                        ),
                        random.uniform(
                            85.0,
                            115.0,
                        ),
                        now,
                        now,
                        uuid.uuid4(),
                    ),
                )

                constituents = (
                    random.sample(
                        range(
                            1,
                            10_001,
                        ),
                        50,
                    )
                )

                raw_weights = [
                    random.random()
                    for _ in constituents
                ]

                total = sum(
                    raw_weights
                )

                for (
                    constituent_id,
                    raw_weight,
                ) in zip(
                    constituents,
                    raw_weights,
                    strict=True,
                ):
                    weight = (
                        raw_weight
                        / total
                    )

                    cursor.execute(
                        """
                        INSERT INTO fixed_income_etf_constituents (
                            etf_instrument_id,
                            constituent_instrument_id,
                            weight,
                            face_value,
                            valid_from,
                            valid_to,
                            recorded_from,
                            recorded_to,
                            source,
                            source_event_id
                        )
                        VALUES (
                            %s,
                            %s,
                            %s,
                            NULL,
                            %s,
                            NULL,
                            %s,
                            NULL,
                            'synthetic-etf-generator',
                            %s
                        )
                        """,
                        (
                            instrument_id,
                            constituent_id,
                            weight,
                            now,
                            now,
                            uuid.uuid4(),
                        ),
                    )

        connection.commit()

    print(
        f"Generated {ETF_COUNT} fixed-income ETFs."
    )


if __name__ == "__main__":
    main()
