from __future__ import annotations

import os
from typing import Any

import requests

from mercator_agent.state.models import (
    InstrumentProfile,
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


def _profile_from_payload(
    payload: dict[str, Any],
) -> InstrumentProfile:
    return InstrumentProfile(
        instrument_id=int(
            payload["instrument_id"]
        ),

        instrument_type=str(
            payload["instrument_type"]
        ),

        issuer_name=str(
            payload["issuer_name"]
        ),

        cusip=payload.get("cusip"),
        isin=payload.get("isin"),
        ticker=payload.get("ticker"),

        coupon_rate=(
            float(
                payload["coupon_rate"]
            )
            if payload.get(
                "coupon_rate"
            )
            is not None
            else None
        ),

        maturity_date=
            payload.get(
                "maturity_date"
            ),

        rating=
            payload.get(
                "rating"
            ),

        sector=
            payload.get(
                "sector"
            ),

        currency=str(
            payload.get(
                "currency",
                "USD",
            )
        ),

        reference_version=(
            int(
                payload["version_id"]
            )
            if payload.get(
                "version_id"
            )
            is not None
            else None
        ),
    )


def get_instrument_profile(
    instrument_id: int,
) -> InstrumentProfile:
    response = requests.get(
        (
            f"{REFERENCE_DATA_URL}"
            f"/instruments/{instrument_id}"
        ),
        timeout=15,
    )

    response.raise_for_status()

    payload = response.json()

    if not isinstance(
        payload,
        dict,
    ):
        raise ValueError(
            "Reference Data instrument lookup "
            "returned an unexpected payload."
        )

    return _profile_from_payload(
        payload
    )


def get_instrument_profiles(
    instrument_ids: list[int],
) -> list[InstrumentProfile]:
    results: list[
        InstrumentProfile
    ] = []

    for instrument_id in dict.fromkeys(
        instrument_ids
    ):
        results.append(
            get_instrument_profile(
                instrument_id
            )
        )

    return results


def find_peer_profiles(
    profile: InstrumentProfile,
    *,
    maturity_window_years: float = 3.0,
    limit: int = 50,
) -> list[InstrumentProfile]:
    params: dict[str, Any] = {
        "instrument_type":
            profile.instrument_type,

        "currency":
            profile.currency,

        "exclude_instrument_id":
            profile.instrument_id,

        "limit":
            limit,
    }

    if profile.sector:
        params["sector"] = (
            profile.sector
        )

    if profile.maturity_date is not None:
        from datetime import (
            datetime,
            timedelta,
            timezone,
        )

        center = datetime.combine(
            profile.maturity_date,
            datetime.min.time(),
            tzinfo=timezone.utc,
        )

        window = timedelta(
            days=365.25
            * maturity_window_years
        )

        params["maturity_start"] = (
            center - window
        ).isoformat()

        params["maturity_end"] = (
            center + window
        ).isoformat()

    response = requests.get(
        (
            f"{REFERENCE_DATA_URL}"
            "/instruments/peers"
        ),
        params=params,
        timeout=15,
    )

    response.raise_for_status()

    payload = response.json()

    if not isinstance(
        payload,
        list,
    ):
        raise ValueError(
            "Reference Data peer lookup "
            "returned an unexpected payload."
        )

    return [
        _profile_from_payload(
            row
        )
        for row in payload
        if isinstance(
            row,
            dict,
        )
    ]


def get_instrument_version(
    instrument_id: int,
    reference_version: int,
) -> InstrumentProfile:
    """
    Resolve the exact reference-data version used by a historical
    evaluated price.

    The versions endpoint is intentionally used instead of an as-of
    lookup because evaluated_prices stores the exact version_id that
    participated in pricing.
    """
    response = requests.get(
        (
            f"{REFERENCE_DATA_URL}"
            f"/instruments/{instrument_id}/versions"
        ),
        timeout=15,
    )

    response.raise_for_status()

    payload = response.json()

    if not isinstance(payload, list):
        raise ValueError(
            "Reference Data versions lookup returned "
            "an unexpected payload."
        )

    for row in payload:
        if (
            int(row.get("version_id", -1))
            == reference_version
        ):
            return _profile_from_payload(row)

    raise ValueError(
        "Reference version "
        f"{reference_version} was not found for "
        f"instrument {instrument_id}."
    )
