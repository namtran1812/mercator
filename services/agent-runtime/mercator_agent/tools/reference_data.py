from __future__ import annotations

import os
from typing import Any

import requests

from mercator_agent.state.models import (
    SecurityResolution,
)


REFERENCE_DATA_URL = os.getenv(
    "REFERENCE_DATA_URL",
    "http://127.0.0.1:8001",
).rstrip("/")


def search_instruments(
    query: str,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    query = query.strip()

    if not query:
        return []

    response = requests.get(
        f"{REFERENCE_DATA_URL}/instruments/search",
        params={
            "q": query,
            "limit": limit,
        },
        timeout=15,
    )

    response.raise_for_status()

    payload = response.json()

    if not isinstance(
        payload,
        list,
    ):
        raise ValueError(
            "Reference Data search "
            "returned an unexpected payload."
        )

    return payload


def resolve_securities(
    query: str,
    *,
    instrument_type: str | None = None,
    limit: int = 50,
) -> SecurityResolution:
    results = search_instruments(
        query,
        limit=limit,
    )

    if instrument_type:
        filtered = [
            row
            for row in results
            if row.get(
                "instrument_type"
            ) == instrument_type
        ]
    else:
        filtered = results

    instrument_ids = [
        int(
            row["instrument_id"]
        )
        for row in filtered
        if row.get(
            "instrument_id"
        )
        is not None
    ]

    issuer_name = None

    if filtered:
        issuer_name = filtered[
            0
        ].get(
            "issuer_name"
        )

    return SecurityResolution(
        query=query,

        instrument_ids=
            instrument_ids,

        instrument_type=
            instrument_type,

        issuer_name=
            issuer_name,

        result_count=
            len(
                instrument_ids
            ),
    )
