from __future__ import annotations

import os

import requests

from mercator_agent.state.models import (
    EtfAnalyticsSnapshot,
)


MARKET_API_URL = os.getenv(
    "MARKET_API_URL",
    "http://127.0.0.1:8005",
).rstrip("/")


def get_etf_analytics(
    instrument_id: int,
) -> EtfAnalyticsSnapshot:
    response = requests.get(
        (
            f"{MARKET_API_URL}"
            f"/etfs/{instrument_id}/analytics"
        ),
        timeout=30,
    )

    response.raise_for_status()

    return EtfAnalyticsSnapshot.model_validate(
        response.json()
    )
