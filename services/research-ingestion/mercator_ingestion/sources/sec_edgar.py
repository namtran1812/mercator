from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class SecEdgarConfig:
    user_agent: str
    minimum_delay_seconds: float = 0.2
    timeout_seconds: float = 30.0


class SecEdgarClient:
    BASE_DATA_URL = "https://data.sec.gov"
    ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data"

    def __init__(self, config: SecEdgarConfig) -> None:
        if "@" not in config.user_agent:
            raise ValueError(
                "SEC user agent should include a contact email"
            )

        self._minimum_delay_seconds = (
            config.minimum_delay_seconds
        )
        self._last_request_time = 0.0
        self._lock = asyncio.Lock()

        self._client = httpx.AsyncClient(
            timeout=config.timeout_seconds,
            follow_redirects=True,
            headers={
                "User-Agent": config.user_agent,
                "Accept-Encoding": "gzip, deflate",
                "Accept": "application/json",
            },
        )

    async def __aenter__(self) -> "SecEdgarClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self._client.aclose()

    async def get_submissions(
        self,
        cik: str,
    ) -> dict[str, Any]:
        normalized_cik = cik.zfill(10)

        return await self._get_json(
            f"{self.BASE_DATA_URL}/submissions/"
            f"CIK{normalized_cik}.json"
        )

    async def get_company_facts(
        self,
        cik: str,
    ) -> dict[str, Any]:
        normalized_cik = cik.zfill(10)

        return await self._get_json(
            f"{self.BASE_DATA_URL}/api/xbrl/"
            f"companyfacts/CIK{normalized_cik}.json"
        )

    @classmethod
    def filing_urls(
        cls,
        cik: str,
        accession_number: str,
        primary_document: str,
    ) -> tuple[str, str]:
        numeric_cik = str(int(cik))
        accession_path = accession_number.replace("-", "")

        base = (
            f"{cls.ARCHIVES_URL}/"
            f"{numeric_cik}/{accession_path}"
        )

        return (
            f"{base}/{primary_document}",
            f"{base}/{accession_number}-index.html",
        )

    async def _get_json(
        self,
        url: str,
    ) -> dict[str, Any]:
        async with self._lock:
            loop = asyncio.get_running_loop()
            now = loop.time()

            delay = (
                self._minimum_delay_seconds
                - (now - self._last_request_time)
            )

            if delay > 0:
                await asyncio.sleep(delay)

            response = await self._client.get(url)
            self._last_request_time = loop.time()

        response.raise_for_status()
        return response.json()
