from __future__ import annotations

import os

CLICKHOUSE_HOST = os.getenv(
    "CLICKHOUSE_HOST",
    "localhost",
)

CLICKHOUSE_PORT = int(
    os.getenv(
        "CLICKHOUSE_PORT",
        "8123",
    )
)

CLICKHOUSE_DATABASE = os.getenv(
    "CLICKHOUSE_DATABASE",
    "mercator",
)

CLICKHOUSE_USERNAME = os.getenv(
    "CLICKHOUSE_USERNAME",
    "mercator",
)

CLICKHOUSE_PASSWORD = os.getenv(
    "CLICKHOUSE_PASSWORD",
    "mercator",
)
