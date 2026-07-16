from __future__ import annotations

from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from .config import POSTGRES_DSN


class ResearchRepository:
    def __init__(
        self,
        dsn: str = POSTGRES_DSN,
    ) -> None:
        self._dsn = dsn

    def all_chunks(self) -> list[dict[str, Any]]:
        with psycopg.connect(
            self._dsn,
            row_factory=dict_row,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        c.chunk_id,
                        c.chunk_text,
                        c.section_name,
                        c.chunk_index,
                        f.cik,
                        i.entity_name AS issuer_name,
                        f.form_type,
                        f.filing_date,
                        f.accession_number,
                        f.filing_url,
                        f.index_url
                    FROM sec_filing_chunks c
                    JOIN sec_filings f
                      ON f.filing_id = c.filing_id
                    JOIN sec_issuers i
                      ON i.cik = f.cik
                    ORDER BY
                        f.filing_date DESC,
                        c.chunk_index
                    """
                )

                return cursor.fetchall()

    def chunks_by_ids(
        self,
        chunk_ids: list[UUID],
    ) -> dict[UUID, dict[str, Any]]:
        if not chunk_ids:
            return {}

        with psycopg.connect(
            self._dsn,
            row_factory=dict_row,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        c.chunk_id,
                        c.chunk_text,
                        c.section_name,
                        c.chunk_index,
                        f.cik,
                        i.entity_name AS issuer_name,
                        f.form_type,
                        f.filing_date,
                        f.accession_number,
                        f.filing_url,
                        f.index_url
                    FROM sec_filing_chunks c
                    JOIN sec_filings f
                      ON f.filing_id = c.filing_id
                    JOIN sec_issuers i
                      ON i.cik = f.cik
                    WHERE c.chunk_id = ANY(%s)
                    """,
                    (chunk_ids,),
                )

                rows = cursor.fetchall()

        return {
            row["chunk_id"]: row
            for row in rows
        }

    def lexical_search(
        self,
        *,
        query: str,
        cik: str | None,
        forms: list[str] | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        conditions = [
            """
            c.search_vector @@
            websearch_to_tsquery('english', %s)
            """
        ]

        where_parameters: list[object] = [query]

        if cik:
            conditions.append("f.cik = %s")
            where_parameters.append(cik.zfill(10))

        if forms:
            conditions.append("f.form_type = ANY(%s)")
            where_parameters.append(forms)

        sql = f"""
            SELECT
                c.chunk_id,
                c.chunk_text,
                c.section_name,
                c.chunk_index,
                f.cik,
                i.entity_name AS issuer_name,
                f.form_type,
                f.filing_date,
                f.accession_number,
                f.filing_url,
                f.index_url,
                ts_rank_cd(
                    c.search_vector,
                    websearch_to_tsquery('english', %s)
                ) AS lexical_rank
            FROM sec_filing_chunks c
            JOIN sec_filings f
              ON f.filing_id = c.filing_id
            JOIN sec_issuers i
              ON i.cik = f.cik
            WHERE {" AND ".join(conditions)}
            ORDER BY
                lexical_rank DESC,
                f.filing_date DESC
            LIMIT %s
        """

        parameters: list[object] = [
            query,
            *where_parameters,
            limit,
        ]

        with psycopg.connect(
            self._dsn,
            row_factory=dict_row,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql,
                    parameters,
                )

                return cursor.fetchall()
