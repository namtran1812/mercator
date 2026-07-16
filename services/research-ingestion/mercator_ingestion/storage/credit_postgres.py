from __future__ import annotations

import os
from typing import Any

import psycopg
from psycopg.rows import dict_row

POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "postgresql://mercator:mercator@localhost:5432/mercator",
)


class CreditSignalStore:
    def __init__(
        self,
        dsn: str = POSTGRES_DSN,
    ) -> None:
        self._dsn = dsn

    def extracted_sections(
        self,
        *,
        cik: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        with psycopg.connect(
            self._dsn,
            row_factory=dict_row,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        f.filing_id,
                        f.form_type,
                        f.filing_date,
                        s.section_id,
                        s.section_name,
                        s.normalized_text
                    FROM sec_filing_sections s
                    JOIN sec_filings f
                      ON f.filing_id = s.filing_id
                    WHERE f.cik = %s
                    ORDER BY
                        f.filing_date DESC,
                        s.section_order
                    LIMIT %s
                    """,
                    (
                        cik.zfill(10),
                        limit,
                    ),
                )

                return cursor.fetchall()

    def replace_chunks_and_signals(
        self,
        *,
        filing_id: object,
        section_id: object,
        chunks: list[object],
        signals_by_chunk: list[list[object]],
    ) -> tuple[int, int]:
        chunk_count = 0
        signal_count = 0

        with psycopg.connect(
            self._dsn,
            row_factory=dict_row,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM sec_filing_chunks
                    WHERE section_id = %s
                    """,
                    (section_id,),
                )

                for chunk, signals in zip(
                    chunks,
                    signals_by_chunk,
                    strict=True,
                ):
                    cursor.execute(
                        """
                        INSERT INTO sec_filing_chunks (
                            filing_id,
                            section_id,
                            chunk_index,
                            section_name,
                            chunk_text,
                            content_hash,
                            start_character,
                            end_character,
                            token_estimate
                        )
                        VALUES (
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s
                        )
                        RETURNING chunk_id
                        """,
                        (
                            filing_id,
                            section_id,
                            chunk.chunk_index,
                            chunk.section_name,
                            chunk.text,
                            chunk.content_hash,
                            chunk.start_character,
                            chunk.end_character,
                            chunk.token_estimate,
                        ),
                    )

                    row = cursor.fetchone()

                    if row is None:
                        raise RuntimeError(
                            "Chunk insert returned no ID"
                        )

                    chunk_id = row["chunk_id"]
                    chunk_count += 1

                    cursor.executemany(
                        """
                        INSERT INTO sec_credit_signals (
                            filing_id,
                            chunk_id,
                            signal_type,
                            signal_value,
                            confidence_score,
                            evidence_text,
                            extraction_method
                        )
                        VALUES (
                            %s, %s, %s, %s,
                            %s, %s, %s
                        )
                        """,
                        [
                            (
                                filing_id,
                                chunk_id,
                                signal.signal_type,
                                signal.signal_value,
                                signal.confidence_score,
                                signal.evidence_text,
                                signal.extraction_method,
                            )
                            for signal in signals
                        ],
                    )

                    signal_count += len(signals)

            connection.commit()

        return chunk_count, signal_count
