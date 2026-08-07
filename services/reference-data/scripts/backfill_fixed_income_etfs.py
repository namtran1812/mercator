from __future__ import annotations

import os
import random
import uuid
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row


POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "postgresql://mercator:mercator@localhost:5433/mercator",
)

CONSTITUENTS_PER_ETF = 50


def main() -> None:
    random.seed(20260806)

    now = datetime.now(
        timezone.utc,
    )

    with psycopg.connect(
        POSTGRES_DSN,
        row_factory=dict_row,
    ) as connection:

        with connection.cursor() as cursor:

            # --------------------------------------------------
            # Current corporate bonds only.
            # ETFs must not become synthetic constituents here.
            # --------------------------------------------------

            cursor.execute(
                """
                SELECT DISTINCT instrument_id
                FROM instrument_versions
                WHERE instrument_type = 'CORPORATE_BOND'
                  AND valid_to IS NULL
                  AND recorded_to IS NULL
                ORDER BY instrument_id
                """
            )

            bond_ids = [
                int(row["instrument_id"])
                for row in cursor.fetchall()
            ]

            # --------------------------------------------------
            # Current ETF security-master records.
            # --------------------------------------------------

            cursor.execute(
                """
                SELECT DISTINCT ON (instrument_id)
                    instrument_id,
                    issuer_name,
                    ticker,
                    rating,
                    sector
                FROM instrument_versions
                WHERE instrument_type = 'FIXED_INCOME_ETF'
                  AND valid_to IS NULL
                  AND recorded_to IS NULL
                ORDER BY
                    instrument_id,
                    source_priority ASC,
                    recorded_from DESC
                """
            )

            etfs = cursor.fetchall()

            print(
                f"Corporate bonds available: {len(bond_ids)}"
            )

            print(
                f"ETFs found: {len(etfs)}"
            )

            if (
                len(bond_ids)
                < CONSTITUENTS_PER_ETF
            ):
                raise RuntimeError(
                    "Not enough corporate bonds "
                    "to construct ETF baskets."
                )

            # --------------------------------------------------
            # Synthetic ETF composition data can be rebuilt.
            #
            # This closes/removes the previous synthetic basket
            # rows, including accidental ETF constituents.
            # --------------------------------------------------

            cursor.execute(
                """
                DELETE FROM fixed_income_etf_constituents
                WHERE source IN (
                    'synthetic-etf-generator',
                    'synthetic-etf-backfill'
                )
                """
            )

            for index, etf in enumerate(
                etfs,
                start=1,
            ):
                instrument_id = int(
                    etf["instrument_id"]
                )

                # ----------------------------------------------
                # Create ETF metadata only when missing.
                # Existing ETF versions (e.g. 10001+) stay intact.
                # ----------------------------------------------

                cursor.execute(
                    """
                    SELECT 1
                    FROM fixed_income_etf_versions
                    WHERE instrument_id = %s
                      AND valid_to IS NULL
                      AND recorded_to IS NULL
                    LIMIT 1
                    """,
                    (
                        instrument_id,
                    ),
                )

                exists = (
                    cursor.fetchone()
                    is not None
                )

                if not exists:
                    ticker = (
                        etf["ticker"]
                        or f"ETF{instrument_id}"
                    )

                    fund_name = (
                        etf["issuer_name"]
                        or ticker
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
                            'synthetic-etf-backfill',
                            %s
                        )
                        """,
                        (
                            instrument_id,
                            fund_name,
                            "Mercator Fixed Income Benchmark",
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

                # ----------------------------------------------
                # Generate 50 CORPORATE BOND constituents.
                # ----------------------------------------------

                constituent_ids = random.sample(
                    bond_ids,
                    CONSTITUENTS_PER_ETF,
                )

                raw_weights = [
                    random.random()
                    for _ in constituent_ids
                ]

                total_weight = sum(
                    raw_weights
                )

                for (
                    constituent_id,
                    raw_weight,
                ) in zip(
                    constituent_ids,
                    raw_weights,
                    strict=True,
                ):
                    weight = (
                        raw_weight
                        / total_weight
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
                            'synthetic-etf-backfill',
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

                if (
                    index % 50 == 0
                    or index == len(etfs)
                ):
                    print(
                        f"Processed {index}/{len(etfs)} ETFs"
                    )

        connection.commit()

    print(
        "ETF metadata/composition backfill complete."
    )


if __name__ == "__main__":
    main()
