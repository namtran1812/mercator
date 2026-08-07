from __future__ import annotations

import os

import requests

from mercator_agent.state.models import (
    PortfolioRiskSnapshot,
)


MARKET_API_URL = os.getenv(
    "MARKET_API_URL",
    "http://127.0.0.1:8005",
).rstrip("/")


def get_risk_decomposition(
    instrument_ids: list[int],
    *,
    position_notional: float = 1_000_000.0,
) -> PortfolioRiskSnapshot:
    response = requests.post(
        f"{MARKET_API_URL}/risk/decomposition",
        json={
            "instrument_ids":
                instrument_ids,

            "position_notional":
                position_notional,
        },
        timeout=30,
    )

    response.raise_for_status()

    payload = response.json()

    return PortfolioRiskSnapshot.model_validate(
        payload
    )
