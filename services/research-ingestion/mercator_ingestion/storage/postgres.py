from __future__ import annotations

import json
import os
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from mercator_ingestion.models.document import (
    DocumentReference,
    ResearchDocument,
)

POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "postgresql://mercator:mercator@localhost:5432/mercator",
)


class ResearchDocumentStore:
    def __init__(
        self,
        dsn: str = POSTGRES_DSN,
    ) -> None:
        self._dsn = dsn

    def known_urls(
        self,
        source_name: str,
    ) -> set[str]:
        with psycopg.connect(
            self._dsn,
            row_factory=dict_row,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT canonical_url
                    FROM research_documents
                    WHERE source_name = %s
                    """,
                    (source_name,),
                )

                return {
                    row["canonical_url"]
                    for row in cursor.fetchall()
                }

    def upsert_discovered(
        self,
        reference: DocumentReference,
    ) -> UUID:
        with psycopg.connect(
            self._dsn,
            row_factory=dict_row,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO research_documents (
                        source_name,
                        source_document_id,
                        canonical_url,
                        title,
                        author,
                        series,
                        category,
                        published_at,
                        metadata
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s::jsonb
                    )
                    ON CONFLICT (
                        source_name,
                        source_document_id
                    )
                    DO UPDATE SET
                        canonical_url = EXCLUDED.canonical_url,
                        title = EXCLUDED.title,
                        author = COALESCE(
                            EXCLUDED.author,
                            research_documents.author
                        ),
                        series = COALESCE(
                            EXCLUDED.series,
                            research_documents.series
                        ),
                        category = COALESCE(
                            EXCLUDED.category,
                            research_documents.category
                        ),
                        published_at = COALESCE(
                            EXCLUDED.published_at,
                            research_documents.published_at
                        ),
                        metadata = (
                            research_documents.metadata
                            || EXCLUDED.metadata
                        )
                    RETURNING document_id
                    """,
                    (
                        reference.source_name,
                        reference.source_document_id,
                        str(reference.canonical_url),
                        reference.title,
                        reference.author,
                        reference.series,
                        reference.category,
                        reference.published_at,
                        json.dumps(reference.metadata),
                    ),
                )

                row = cursor.fetchone()
                connection.commit()

        if row is None:
            raise RuntimeError(
                "Document upsert did not return an ID"
            )

        return row["document_id"]

    def save_extracted(
        self,
        document_id: UUID,
        document: ResearchDocument,
    ) -> None:
        with psycopg.connect(self._dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE research_documents
                    SET
                        title = %s,
                        author = %s,
                        series = %s,
                        category = %s,
                        published_at = %s,
                        fetched_at = %s,
                        summary = %s,
                        normalized_text = %s,
                        content_hash = %s,
                        extraction_status = 'EXTRACTED',
                        extraction_error = NULL,
                        metadata = metadata || %s::jsonb
                    WHERE document_id = %s
                    """,
                    (
                        document.reference.title,
                        document.reference.author,
                        document.reference.series,
                        document.reference.category,
                        document.reference.published_at,
                        document.fetched_at,
                        document.summary,
                        document.normalized_text,
                        document.content_hash,
                        json.dumps(document.metadata),
                        document_id,
                    ),
                )

                cursor.execute(
                    """
                    DELETE FROM research_document_spans
                    WHERE document_id = %s
                    """,
                    (document_id,),
                )

                cursor.executemany(
                    """
                    INSERT INTO research_document_spans (
                        document_id,
                        span_index,
                        section_heading,
                        span_text,
                        start_character,
                        end_character,
                        content_hash
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    [
                        (
                            document_id,
                            span.span_index,
                            span.section_heading,
                            span.span_text,
                            span.start_character,
                            span.end_character,
                            span.content_hash,
                        )
                        for span in document.spans
                    ],
                )

            connection.commit()

    def mark_failure(
        self,
        document_id: UUID,
        error: str,
    ) -> None:
        with psycopg.connect(self._dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE research_documents
                    SET
                        extraction_status = 'FAILED',
                        extraction_error = %s,
                        fetched_at = now()
                    WHERE document_id = %s
                    """,
                    (
                        error[:2_000],
                        document_id,
                    ),
                )

            connection.commit()
