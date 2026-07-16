from __future__ import annotations

from datetime import datetime

from psycopg import Connection

from .models import InstrumentSearchResult, InstrumentVersion


def get_current_instrument(
    connection: Connection,
    instrument_id: int,
) -> InstrumentVersion | None:
    query = """
        SELECT *
        FROM instrument_versions
        WHERE instrument_id = %s
          AND valid_from <= now()
          AND (valid_to IS NULL OR valid_to > now())
          AND recorded_from <= now()
          AND (recorded_to IS NULL OR recorded_to > now())
        ORDER BY
          source_priority ASC,
          recorded_from DESC
        LIMIT 1
    """

    with connection.cursor() as cursor:
        cursor.execute(query, (instrument_id,))
        row = cursor.fetchone()

    if row is None:
        return None

    return InstrumentVersion.model_validate(row)


def get_instrument_as_of(
    connection: Connection,
    instrument_id: int,
    valid_at: datetime,
    known_at: datetime,
) -> InstrumentVersion | None:
    query = """
        SELECT *
        FROM instrument_versions
        WHERE instrument_id = %s
          AND valid_from <= %s
          AND (valid_to IS NULL OR valid_to > %s)
          AND recorded_from <= %s
          AND (recorded_to IS NULL OR recorded_to > %s)
        ORDER BY
          source_priority ASC,
          recorded_from DESC
        LIMIT 1
    """

    parameters = (
        instrument_id,
        valid_at,
        valid_at,
        known_at,
        known_at,
    )

    with connection.cursor() as cursor:
        cursor.execute(query, parameters)
        row = cursor.fetchone()

    if row is None:
        return None

    return InstrumentVersion.model_validate(row)


def search_instruments(
    connection: Connection,
    query_text: str,
    limit: int = 20,
) -> list[InstrumentSearchResult]:
    search_pattern = f"%{query_text}%"

    query = """
        SELECT DISTINCT ON (instrument_id)
            instrument_id,
            instrument_type,
            issuer_name,
            cusip,
            isin,
            ticker,
            rating,
            sector
        FROM instrument_versions
        WHERE recorded_to IS NULL
          AND valid_to IS NULL
          AND (
              issuer_name ILIKE %s
              OR cusip ILIKE %s
              OR isin ILIKE %s
              OR ticker ILIKE %s
          )
        ORDER BY
          instrument_id,
          source_priority ASC,
          recorded_from DESC
        LIMIT %s
    """

    with connection.cursor() as cursor:
        cursor.execute(
            query,
            (
                search_pattern,
                search_pattern,
                search_pattern,
                search_pattern,
                limit,
            ),
        )
        rows = cursor.fetchall()

    return [
        InstrumentSearchResult.model_validate(row)
        for row in rows
    ]


def list_versions(
    connection: Connection,
    instrument_id: int,
) -> list[InstrumentVersion]:
    query = """
        SELECT *
        FROM instrument_versions
        WHERE instrument_id = %s
        ORDER BY recorded_from ASC, valid_from ASC
    """

    with connection.cursor() as cursor:
        cursor.execute(query, (instrument_id,))
        rows = cursor.fetchall()

    return [
        InstrumentVersion.model_validate(row)
        for row in rows
    ]


def get_active_reference_observations(
    connection: Connection,
    instrument_id: int,
    field_name: str,
) -> list[dict]:
    query = """
        SELECT
            observation_id,
            instrument_id,
            field_name,
            field_value,
            source_name,
            source_priority,
            trust_score,
            valid_from,
            valid_to
        FROM reference_observations
        JOIN reference_sources USING (source_name)
        WHERE instrument_id = %s
          AND field_name = %s
          AND enabled = TRUE
          AND valid_from <= now()
          AND (valid_to IS NULL OR valid_to > now())
        ORDER BY source_priority ASC, recorded_at DESC
    """

    with connection.cursor() as cursor:
        cursor.execute(
            query,
            (
                instrument_id,
                field_name,
            ),
        )
        return cursor.fetchall()


def persist_reconciliation(
    connection: Connection,
    result,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE reconciled_reference_values
            SET recorded_to = now()
            WHERE instrument_id = %s
              AND field_name = %s
              AND recorded_to IS NULL
            """,
            (
                result.instrument_id,
                result.field_name,
            ),
        )

        cursor.execute(
            """
            INSERT INTO reconciled_reference_values (
                instrument_id,
                field_name,
                selected_value,
                selected_source,
                confidence_score,
                contributing_observations,
                valid_from,
                valid_to
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, now(), NULL
            )
            """,
            (
                result.instrument_id,
                result.field_name,
                result.selected_value,
                result.selected_source,
                result.confidence_score,
                result.contributing_observations,
            ),
        )

    connection.commit()
