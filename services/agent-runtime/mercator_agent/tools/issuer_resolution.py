from __future__ import annotations

import os

import psycopg
from psycopg.rows import dict_row

from mercator_agent.state.models import IssuerResolution


POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "postgresql://mercator:mercator@localhost:5432/mercator",
)


def resolve_issuer(
    *,
    issuer: str | None,
    cik: str | None,
) -> IssuerResolution:
    conditions: list[str] = []
    parameters: list[object] = []

    if cik:
        conditions.append("cik = %s")
        parameters.append(cik.zfill(10))

    elif issuer:
        conditions.append(
            """
            (
                entity_name ILIKE %s
                OR %s = ANY(tickers)
            )
            """
        )

        search_pattern = f"%{issuer}%"

        parameters.extend(
            [
                search_pattern,
                issuer.upper(),
            ]
        )

    else:
        raise ValueError(
            "Either issuer or CIK is required"
        )

    query = f"""
        SELECT
            cik,
            entity_name,
            tickers
        FROM sec_issuers
        WHERE {" AND ".join(conditions)}
        ORDER BY
            CASE
                WHEN lower(entity_name) =
                    lower(%s)
                THEN 0
                ELSE 1
            END,
            entity_name
        LIMIT 1
    """

    exact_name = issuer or ""

    with psycopg.connect(
        POSTGRES_DSN,
        row_factory=dict_row,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                [
                    *parameters,
                    exact_name,
                ],
            )

            row = cursor.fetchone()

    if row is None:
        raise LookupError(
            f"Issuer was not found: {issuer or cik}"
        )

    return IssuerResolution(
        cik=row["cik"],
        issuer_name=row["entity_name"],
        tickers=list(row["tickers"]),
    )
