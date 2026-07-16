from __future__ import annotations

import os
import random

import psycopg

POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "postgresql://mercator:mercator@localhost:5432/mercator",
)

TENORS = [
    "3M",
    "6M",
    "1Y",
    "2Y",
    "3Y",
    "5Y",
    "7Y",
    "10Y",
    "30Y",
]


def dependency_tenors(
    maturity_years: float,
) -> list[tuple[str, float]]:
    nodes = [
        (0.25, "3M"),
        (0.50, "6M"),
        (1.00, "1Y"),
        (2.00, "2Y"),
        (3.00, "3Y"),
        (5.00, "5Y"),
        (7.00, "7Y"),
        (10.00, "10Y"),
        (30.00, "30Y"),
    ]

    if maturity_years <= nodes[0][0]:
        return [(nodes[0][1], 1.0)]

    if maturity_years >= nodes[-1][0]:
        return [(nodes[-1][1], 1.0)]

    for index in range(1, len(nodes)):
        upper_years, upper_tenor = nodes[index]
        lower_years, lower_tenor = nodes[index - 1]

        if maturity_years <= upper_years:
            width = upper_years - lower_years

            upper_weight = (
                maturity_years - lower_years
            ) / width

            lower_weight = 1.0 - upper_weight

            return [
                (lower_tenor, lower_weight),
                (upper_tenor, upper_weight),
            ]

    raise RuntimeError("Unable to resolve dependencies")


def main() -> None:
    random.seed(42)

    rows: list[tuple[int, str, str, float]] = []

    for instrument_id in range(1, 10_001):
        maturity_years = random.uniform(
            0.20,
            30.0,
        )

        for tenor, weight in dependency_tenors(
            maturity_years
        ):
            rows.append(
                (
                    instrument_id,
                    "UST",
                    tenor,
                    weight,
                )
            )

    with psycopg.connect(POSTGRES_DSN) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                TRUNCATE TABLE
                    instrument_curve_dependencies
                """
            )

            cursor.executemany(
                """
                INSERT INTO instrument_curve_dependencies (
                    instrument_id,
                    curve_name,
                    tenor,
                    dependency_weight
                )
                VALUES (%s, %s, %s, %s)
                """,
                rows,
            )

        connection.commit()

    print(
        f"Loaded {len(rows):,} curve dependencies "
        "for 10,000 instruments."
    )


if __name__ == "__main__":
    main()
