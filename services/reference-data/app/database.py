from __future__ import annotations

from collections.abc import Generator

import psycopg
from psycopg import Connection
from psycopg.rows import dict_row

from .config import POSTGRES_DSN


def get_connection() -> Connection:
    return psycopg.connect(
        POSTGRES_DSN,
        row_factory=dict_row,
    )


def connection_dependency() -> Generator[Connection, None, None]:
    connection = get_connection()

    try:
        yield connection
    finally:
        connection.close()
