from __future__ import annotations

import os
from uuid import UUID

import psycopg

POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "postgresql://mercator:mercator@localhost:5432/mercator",
)

ACCOUNT_ID = UUID(
    "00000000-0000-0000-0000-000000000101"
)


def main() -> None:
    with psycopg.connect(POSTGRES_DSN) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO trading_accounts (
                    account_id,
                    account_name,
                    base_currency,
                    cash_balance
                )
                VALUES (
                    %s,
                    'Mercator Demo Fund',
                    'USD',
                    100000000.0
                )
                ON CONFLICT (account_id)
                DO UPDATE SET
                    account_name = EXCLUDED.account_name,
                    updated_at = now()
                """,
                (ACCOUNT_ID,),
            )

        connection.commit()

    print(
        "Seeded Mercator Demo Fund account "
        f"{ACCOUNT_ID}"
    )


if __name__ == "__main__":
    main()
