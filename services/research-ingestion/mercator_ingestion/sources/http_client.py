from __future__ import annotations

import asyncio
from urllib.parse import urlparse

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


class PoliteHttpClient:
    def __init__(
        self,
        *,
        user_agent: str,
        minimum_delay_seconds: float = 1.5,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._minimum_delay_seconds = minimum_delay_seconds
        self._last_request_by_host: dict[str, float] = {}
        self._lock = asyncio.Lock()

        self._client = httpx.AsyncClient(
            timeout=timeout_seconds,
            follow_redirects=True,
            headers={
                "User-Agent": user_agent,
                "Accept": (
                    "text/html,application/xhtml+xml,"
                    "application/xml;q=0.9,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.8",
            },
        )

    async def __aenter__(self) -> "PoliteHttpClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self._client.aclose()

    @retry(
        retry=retry_if_exception_type(
            (
                httpx.ConnectError,
                httpx.ReadTimeout,
                httpx.RemoteProtocolError,
            )
        ),
        wait=wait_exponential(
            multiplier=1,
            min=1,
            max=10,
        ),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def get(self, url: str) -> httpx.Response:
        hostname = urlparse(url).hostname or ""

        async with self._lock:
            now = asyncio.get_running_loop().time()
            previous = self._last_request_by_host.get(hostname)

            if previous is not None:
                elapsed = now - previous
                remaining = self._minimum_delay_seconds - elapsed

                if remaining > 0:
                    await asyncio.sleep(remaining)

            response = await self._client.get(url)
            self._last_request_by_host[hostname] = (
                asyncio.get_running_loop().time()
            )

        response.raise_for_status()
        return response
