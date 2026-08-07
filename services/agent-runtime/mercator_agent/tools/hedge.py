from __future__ import annotations

import os

import requests

from mercator_agent.state.models import (
    HedgeRecommendationSnapshot,
)


MARKET_API_URL = os.getenv(
    "MARKET_API_URL",
    "http://127.0.0.1:8005",
).rstrip("/")


def get_hedge_recommendations(
    instrument_ids: list[int],
    *,
    position_notional: float = 1_000_000.0,
    hedge_ratio: float = 1.0,
    include_credit_hedge: bool = True,
) -> HedgeRecommendationSnapshot:
    response = requests.post(
        f"{MARKET_API_URL}/risk/hedge-recommendations",
        json={
            "instrument_ids":
                instrument_ids,

            "position_notional":
                position_notional,

            "hedge_ratio":
                hedge_ratio,

            "include_credit_hedge":
                include_credit_hedge,
        },
        timeout=30,
    )

    response.raise_for_status()

    return HedgeRecommendationSnapshot.model_validate(
        response.json()
    )
