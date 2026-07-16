from __future__ import annotations

import os
from datetime import datetime
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "postgresql://mercator:mercator@localhost:5432/mercator",
)


class RFQRepository:
    def create_rfq(
        self,
        *,
        rfq_id: UUID,
        account_id: UUID,
        instrument_id: int,
        side: str,
        quantity: float,
        client: str,
        requested_at: datetime,
    ) -> dict[str, Any]:
        with psycopg.connect(
            POSTGRES_DSN,
            row_factory=dict_row,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO rfqs (
                        id,
                        account_id,
                        instrument_id,
                        side,
                        quantity,
                        client,
                        requested_at,
                        status
                    )
                    VALUES (
                        %s, %s, %s, %s,
                        %s, %s, %s, 'REQUESTED'
                    )
                    RETURNING *
                    """,
                    (
                        rfq_id,
                        account_id,
                        instrument_id,
                        side,
                        quantity,
                        client,
                        requested_at,
                    ),
                )

                row = cursor.fetchone()
                connection.commit()

        if row is None:
            raise RuntimeError(
                "RFQ insert returned no row"
            )

        return row

    def get_rfq(
        self,
        rfq_id: UUID,
    ) -> dict[str, Any] | None:
        with psycopg.connect(
            POSTGRES_DSN,
            row_factory=dict_row,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM rfqs
                    WHERE id = %s
                    """,
                    (rfq_id,),
                )

                return cursor.fetchone()

    def update_rfq_status(
        self,
        *,
        rfq_id: UUID,
        status: str,
    ) -> None:
        with psycopg.connect(
            POSTGRES_DSN
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE rfqs
                    SET status = %s
                    WHERE id = %s
                    """,
                    (
                        status,
                        rfq_id,
                    ),
                )

            connection.commit()

    def upsert_dealer_quote(
        self,
        *,
        quote_id: UUID,
        rfq_id: UUID,
        dealer: str,
        price: float,
        spread_bps: float,
        latency_ms: int,
        quoted_at: datetime,
        expires_at: datetime,
        inventory_adjustment_bps: float,
        size_adjustment_bps: float,
    ) -> dict[str, Any]:
        with psycopg.connect(
            POSTGRES_DSN,
            row_factory=dict_row,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO dealer_quotes (
                        id,
                        rfq_id,
                        dealer,
                        price,
                        spread_bps,
                        latency_ms,
                        quoted_at,
                        expires_at,
                        quote_status,
                        inventory_adjustment_bps,
                        size_adjustment_bps
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, 'ACTIVE',
                        %s, %s
                    )
                    ON CONFLICT (
                        rfq_id,
                        dealer
                    )
                    DO UPDATE SET
                        id = EXCLUDED.id,
                        price = EXCLUDED.price,
                        spread_bps =
                            EXCLUDED.spread_bps,
                        latency_ms =
                            EXCLUDED.latency_ms,
                        quoted_at =
                            EXCLUDED.quoted_at,
                        expires_at =
                            EXCLUDED.expires_at,
                        quote_status = 'ACTIVE',
                        inventory_adjustment_bps =
                            EXCLUDED.inventory_adjustment_bps,
                        size_adjustment_bps =
                            EXCLUDED.size_adjustment_bps
                    RETURNING *
                    """,
                    (
                        quote_id,
                        rfq_id,
                        dealer,
                        price,
                        spread_bps,
                        latency_ms,
                        quoted_at,
                        expires_at,
                        inventory_adjustment_bps,
                        size_adjustment_bps,
                    ),
                )

                row = cursor.fetchone()
                connection.commit()

        if row is None:
            raise RuntimeError(
                "Dealer quote insert returned no row"
            )

        return row

    def list_quotes(
        self,
        rfq_id: UUID,
    ) -> list[dict[str, Any]]:
        with psycopg.connect(
            POSTGRES_DSN,
            row_factory=dict_row,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM dealer_quotes
                    WHERE rfq_id = %s
                    ORDER BY
                        quoted_at,
                        dealer
                    """,
                    (rfq_id,),
                )

                return cursor.fetchall()

    def execute_quote(
        self,
        *,
        rfq_id: UUID,
        quote_id: UUID,
        execution_id: UUID,
        executed_at: datetime,
    ) -> tuple[dict[str, Any], int]:
        with psycopg.connect(
            POSTGRES_DSN,
            row_factory=dict_row,
        ) as connection:
            with connection.transaction():
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT *
                        FROM rfqs
                        WHERE id = %s
                        FOR UPDATE
                        """,
                        (rfq_id,),
                    )

                    rfq = cursor.fetchone()

                    if rfq is None:
                        raise LookupError(
                            "RFQ not found"
                        )

                    if rfq["status"] == "EXECUTED":
                        raise ValueError(
                            "RFQ has already been executed"
                        )

                    if rfq["status"] in (
                        "CANCELLED",
                        "EXPIRED",
                    ):
                        raise ValueError(
                            f"RFQ cannot be executed from "
                            f"status {rfq['status']}"
                        )

                    cursor.execute(
                        """
                        SELECT *
                        FROM dealer_quotes
                        WHERE id = %s
                          AND rfq_id = %s
                        FOR UPDATE
                        """,
                        (
                            quote_id,
                            rfq_id,
                        ),
                    )

                    quote = cursor.fetchone()

                    if quote is None:
                        raise LookupError(
                            "Dealer quote not found"
                        )

                    if quote["quote_status"] != "ACTIVE":
                        raise ValueError(
                            "Dealer quote is not active"
                        )

                    if (
                        quote["expires_at"] is not None
                        and quote["expires_at"]
                        <= executed_at
                    ):
                        cursor.execute(
                            """
                            UPDATE dealer_quotes
                            SET quote_status = 'EXPIRED'
                            WHERE id = %s
                            """,
                            (quote_id,),
                        )

                        raise ValueError(
                            "Dealer quote has expired"
                        )

                    cursor.execute(
                        """
                        UPDATE dealer_quotes
                        SET quote_status = 'EXECUTED'
                        WHERE id = %s
                        """,
                        (quote_id,),
                    )

                    cursor.execute(
                        """
                        UPDATE dealer_quotes
                        SET quote_status = 'REJECTED'
                        WHERE rfq_id = %s
                          AND id <> %s
                          AND quote_status = 'ACTIVE'
                        """,
                        (
                            rfq_id,
                            quote_id,
                        ),
                    )

                    rejected_quote_count = (
                        cursor.rowcount
                    )

                    cursor.execute(
                        """
                        INSERT INTO executions (
                            id,
                            rfq_id,
                            quote_id,
                            account_id,
                            instrument_id,
                            side,
                            client,
                            dealer,
                            price,
                            quantity,
                            executed_at,
                            execution_status
                        )
                        VALUES (
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s,
                            %s, 'EXECUTED'
                        )
                        RETURNING *
                        """,
                        (
                            execution_id,
                            rfq_id,
                            quote_id,
                            rfq["account_id"],
                            rfq["instrument_id"],
                            rfq["side"],
                            rfq["client"],
                            quote["dealer"],
                            quote["price"],
                            rfq["quantity"],
                            executed_at,
                        ),
                    )

                    execution = cursor.fetchone()

                    if execution is None:
                        raise RuntimeError(
                            "Execution insert returned no row"
                        )

                    cursor.execute(
                        """
                        UPDATE rfqs
                        SET status = 'EXECUTED'
                        WHERE id = %s
                        """,
                        (rfq_id,),
                    )

            connection.commit()

        return (
            execution,
            rejected_quote_count,
        )

    def account_summary(
        self,
        account_id: UUID,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        with psycopg.connect(
            POSTGRES_DSN,
            row_factory=dict_row,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM trading_accounts
                    WHERE account_id = %s
                    """,
                    (account_id,),
                )

                account = cursor.fetchone()

                if account is None:
                    raise LookupError(
                        "Trading account not found"
                    )

                cursor.execute(
                    """
                    SELECT *
                    FROM positions
                    WHERE account_id = %s
                      AND face_value <> 0
                    ORDER BY
                        abs(face_value) DESC,
                        instrument_id
                    """,
                    (account_id,),
                )

                positions = cursor.fetchall()

        return account, positions
    def analytics_summary(
        self,
    ) -> tuple[
        dict[str, Any],
        list[dict[str, Any]],
    ]:
        with psycopg.connect(
            POSTGRES_DSN,
            row_factory=dict_row,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        count(*) AS rfq_count,

                        count(*) FILTER (
                            WHERE quote_count > 0
                        ) AS quoted_rfq_count,

                        count(*) FILTER (
                            WHERE was_executed
                        ) AS executed_rfq_count,

                        COALESCE(
                            avg(quote_count),
                            0
                        ) AS average_quotes_per_rfq,

                        COALESCE(
                            avg(average_latency_ms),
                            0
                        ) AS average_dealer_latency_ms,

                        COALESCE(
                            avg(execution_latency_ms)
                                FILTER (
                                    WHERE was_executed
                                ),
                            0
                        ) AS average_execution_latency_ms,

                        COALESCE(
                            sum(quantity),
                            0
                        ) AS total_notional,

                        COALESCE(
                            sum(quantity) FILTER (
                                WHERE was_executed
                            ),
                            0
                        ) AS executed_notional

                    FROM rfq_analytics
                    """
                )

                summary = cursor.fetchone()

                cursor.execute(
                    """
                    SELECT
                        percentile_cont(0.95)
                        WITHIN GROUP (
                            ORDER BY latency_ms
                        ) AS p95_latency_ms
                    FROM dealer_quotes
                    """
                )

                latency = cursor.fetchone()

                cursor.execute(
                    """
                    SELECT
                        q.dealer,

                        count(*) AS quote_count,

                        count(*) FILTER (
                            WHERE q.quote_status =
                                'EXECUTED'
                        ) AS execution_count,

                        COALESCE(
                            avg(q.latency_ms),
                            0
                        ) AS average_latency_ms,

                        COALESCE(
                            avg(q.spread_bps),
                            0
                        ) AS average_spread_bps,

                        COALESCE(
                            avg(q.price),
                            0
                        ) AS average_price

                    FROM dealer_quotes q

                    GROUP BY q.dealer

                    ORDER BY
                        execution_count DESC,
                        quote_count DESC,
                        q.dealer
                    """
                )

                dealers = cursor.fetchall()

        if summary is None:
            raise RuntimeError(
                "RFQ analytics query returned no row"
            )

        summary["p95_dealer_latency_ms"] = (
            float(latency["p95_latency_ms"])
            if latency
            and latency["p95_latency_ms"]
            is not None
            else 0.0
        )

        return summary, dealers
