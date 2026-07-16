from __future__ import annotations

import os
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row

POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "postgresql://mercator:mercator@localhost:5432/mercator",
)


def apply_execution_to_ledger(
    *,
    execution_id: UUID,
) -> dict[str, Any]:
    with psycopg.connect(
        POSTGRES_DSN,
        row_factory=dict_row,
    ) as connection:
        with connection.transaction():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM executions
                    WHERE id = %s
                    FOR UPDATE
                    """,
                    (execution_id,),
                )

                execution = cursor.fetchone()

                if execution is None:
                    raise LookupError(
                        "Execution not found"
                    )

                cursor.execute(
                    """
                    SELECT ledger_entry_id
                    FROM position_ledger_entries
                    WHERE execution_id = %s
                    """,
                    (execution_id,),
                )

                existing = cursor.fetchone()

                if existing is not None:
                    return execution

                account_id = execution["account_id"]
                instrument_id = execution["instrument_id"]
                quantity = float(execution["quantity"])
                price = float(execution["price"])
                side = execution["side"]
                executed_at: datetime = execution[
                    "executed_at"
                ]

                signed_quantity = (
                    quantity
                    if side == "BUY"
                    else -quantity
                )

                cash_change = (
                    -price / 100.0 * quantity
                    if side == "BUY"
                    else price / 100.0 * quantity
                )

                cursor.execute(
                    """
                    SELECT *
                    FROM positions
                    WHERE account_id = %s
                      AND instrument_id = %s
                    FOR UPDATE
                    """,
                    (
                        account_id,
                        instrument_id,
                    ),
                )

                current = cursor.fetchone()

                current_face = (
                    float(current["face_value"])
                    if current
                    else 0.0
                )

                current_cost = (
                    float(current["average_cost"])
                    if current
                    else 0.0
                )

                new_face = (
                    current_face + signed_quantity
                )

                realized_pnl_change = 0.0

                if side == "BUY":
                    if new_face != 0.0:
                        new_average_cost = (
                            current_face * current_cost
                            + quantity * price
                        ) / new_face
                    else:
                        new_average_cost = 0.0
                else:
                    closed_quantity = min(
                        quantity,
                        max(current_face, 0.0),
                    )

                    realized_pnl_change = (
                        price - current_cost
                    ) / 100.0 * closed_quantity

                    new_average_cost = (
                        current_cost
                        if new_face > 0.0
                        else 0.0
                    )

                cursor.execute(
                    """
                    INSERT INTO positions (
                        account_id,
                        instrument_id,
                        face_value,
                        average_cost,
                        realized_pnl,
                        updated_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (
                        account_id,
                        instrument_id
                    )
                    DO UPDATE SET
                        face_value =
                            EXCLUDED.face_value,
                        average_cost =
                            EXCLUDED.average_cost,
                        realized_pnl =
                            positions.realized_pnl
                            + EXCLUDED.realized_pnl,
                        updated_at =
                            EXCLUDED.updated_at
                    """,
                    (
                        account_id,
                        instrument_id,
                        new_face,
                        new_average_cost,
                        realized_pnl_change,
                        executed_at,
                    ),
                )

                cursor.execute(
                    """
                    UPDATE trading_accounts
                    SET
                        cash_balance =
                            cash_balance + %s,
                        updated_at = %s
                    WHERE account_id = %s
                    """,
                    (
                        cash_change,
                        executed_at,
                        account_id,
                    ),
                )

                cursor.execute(
                    """
                    INSERT INTO position_ledger_entries (
                        ledger_entry_id,
                        account_id,
                        execution_id,
                        instrument_id,
                        side,
                        quantity,
                        execution_price,
                        cash_change,
                        face_value_change,
                        created_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        uuid4(),
                        account_id,
                        execution_id,
                        instrument_id,
                        side,
                        quantity,
                        price,
                        cash_change,
                        signed_quantity,
                        executed_at,
                    ),
                )

        connection.commit()

    return execution
