from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

import psycopg

POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "postgresql://mercator:mercator@localhost:5432/mercator",
)


class SecFilingStore:
    def __init__(
        self,
        dsn: str = POSTGRES_DSN,
    ) -> None:
        self._dsn = dsn

    def upsert_issuer(
        self,
        submissions: dict[str, Any],
    ) -> None:
        cik = str(submissions["cik"]).zfill(10)

        with psycopg.connect(self._dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO sec_issuers (
                        cik,
                        entity_name,
                        tickers,
                        exchanges,
                        sic,
                        sic_description,
                        fiscal_year_end
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (cik)
                    DO UPDATE SET
                        entity_name = EXCLUDED.entity_name,
                        tickers = EXCLUDED.tickers,
                        exchanges = EXCLUDED.exchanges,
                        sic = EXCLUDED.sic,
                        sic_description =
                            EXCLUDED.sic_description,
                        fiscal_year_end =
                            EXCLUDED.fiscal_year_end,
                        updated_at = now()
                    """,
                    (
                        cik,
                        submissions["name"],
                        submissions.get("tickers", []),
                        submissions.get("exchanges", []),
                        submissions.get("sic"),
                        submissions.get("sicDescription"),
                        submissions.get("fiscalYearEnd"),
                    ),
                )

            connection.commit()

    def upsert_recent_filings(
        self,
        submissions: dict[str, Any],
        *,
        allowed_forms: set[str],
    ) -> int:
        cik = str(submissions["cik"]).zfill(10)
        recent = submissions["filings"]["recent"]

        rows: list[tuple[object, ...]] = []

        for index, accession_number in enumerate(
            recent["accessionNumber"]
        ):
            form_type = recent["form"][index]

            if form_type not in allowed_forms:
                continue

            primary_document = (
                recent["primaryDocument"][index]
            )

            filing_url, index_url = self._filing_urls(
                cik,
                accession_number,
                primary_document,
            )

            acceptance = (
                recent.get("acceptanceDateTime", [None])[index]
                if index < len(
                    recent.get("acceptanceDateTime", [])
                )
                else None
            )

            rows.append(
                (
                    cik,
                    accession_number,
                    form_type,
                    recent["filingDate"][index],
                    recent["reportDate"][index] or None,
                    self._parse_sec_datetime(acceptance),
                    primary_document,
                    (
                        recent["primaryDocDescription"][index]
                        if index < len(
                            recent.get(
                                "primaryDocDescription",
                                [],
                            )
                        )
                        else None
                    ),
                    filing_url,
                    index_url,
                    json.dumps(
                        {
                            "act": recent["act"][index]
                            if index < len(recent["act"])
                            else None,
                            "file_number": (
                                recent["fileNumber"][index]
                                if index
                                < len(recent["fileNumber"])
                                else None
                            ),
                            "film_number": (
                                recent["filmNumber"][index]
                                if index
                                < len(recent["filmNumber"])
                                else None
                            ),
                        }
                    ),
                )
            )

        with psycopg.connect(self._dsn) as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO sec_filings (
                        cik,
                        accession_number,
                        form_type,
                        filing_date,
                        report_date,
                        acceptance_datetime,
                        primary_document,
                        primary_document_description,
                        filing_url,
                        index_url,
                        metadata
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s::jsonb
                    )
                    ON CONFLICT (
                        cik,
                        accession_number
                    )
                    DO UPDATE SET
                        form_type = EXCLUDED.form_type,
                        filing_date = EXCLUDED.filing_date,
                        report_date = EXCLUDED.report_date,
                        acceptance_datetime =
                            EXCLUDED.acceptance_datetime,
                        primary_document =
                            EXCLUDED.primary_document,
                        primary_document_description =
                            EXCLUDED.primary_document_description,
                        filing_url = EXCLUDED.filing_url,
                        index_url = EXCLUDED.index_url,
                        metadata = EXCLUDED.metadata
                    """,
                    rows,
                )

            connection.commit()

        return len(rows)

    @staticmethod
    def _filing_urls(
        cik: str,
        accession_number: str,
        primary_document: str,
    ) -> tuple[str, str]:
        numeric_cik = str(int(cik))
        accession_path = accession_number.replace("-", "")

        base = (
            "https://www.sec.gov/Archives/edgar/data/"
            f"{numeric_cik}/{accession_path}"
        )

        return (
            f"{base}/{primary_document}",
            f"{base}/{accession_number}-index.html",
        )

    @staticmethod
    def _parse_sec_datetime(
        value: str | None,
    ) -> datetime | None:
        if not value:
            return None

        normalized = value.strip()

        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"

        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            pass

        for date_format in (
            "%Y%m%d%H%M%S",
            "%Y%m%d%H%M%S.%f",
        ):
            try:
                return datetime.strptime(
                    value,
                    date_format,
                )
            except ValueError:
                continue

        raise ValueError(
            f"Unsupported SEC datetime format: {value!r}"
        )
