from __future__ import annotations

import os

import requests

from mercator_agent.state.models import (
    StressTestSnapshot,
)


MARKET_API_URL = os.getenv(
    "MARKET_API_URL",
    "http://127.0.0.1:8005",
).rstrip("/")


def run_stress_test(
    instrument_ids: list[int],
    *,
    position_notional: float = 1_000_000.0,
    treasury_parallel_bps: float = 0.0,
    treasury_2y_bps: float = 0.0,
    treasury_5y_bps: float = 0.0,
    treasury_10y_bps: float = 0.0,
    treasury_30y_bps: float = 0.0,
    credit_parallel_bps: float = 0.0,
) -> StressTestSnapshot:
    response = requests.post(
        f"{MARKET_API_URL}/stress/run",
        json={
            "instrument_ids":
                instrument_ids,

            "position_notional":
                position_notional,

            "scenario": {
                "treasury_parallel_bps":
                    treasury_parallel_bps,

                "treasury_2y_bps":
                    treasury_2y_bps,

                "treasury_5y_bps":
                    treasury_5y_bps,

                "treasury_10y_bps":
                    treasury_10y_bps,

                "treasury_30y_bps":
                    treasury_30y_bps,

                "credit_parallel_bps":
                    credit_parallel_bps,
            },
        },
        timeout=30,
    )

    response.raise_for_status()

    return StressTestSnapshot.model_validate(
        response.json()
    )
