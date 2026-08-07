from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from .models import FixedIncomeEtfAnalyticsResponse
from .repository import MarketRepository


REFERENCE_DATA_URL = os.getenv(
    "REFERENCE_DATA_URL",
    "http://127.0.0.1:8001",
)


class EtfAnalyticsError(Exception):
    pass


def _get_json(path: str):
    url = (
        REFERENCE_DATA_URL.rstrip("/")
        + path
    )

    try:
        with urlopen(
            url,
            timeout=10,
        ) as response:
            return json.load(response)

    except HTTPError as error:
        if error.code == 404:
            raise EtfAnalyticsError(
                "Fixed-income ETF not found"
            ) from error

        raise EtfAnalyticsError(
            f"Reference Data request failed "
            f"with status {error.code}"
        ) from error

    except URLError as error:
        raise EtfAnalyticsError(
            "Reference Data service is unavailable"
        ) from error


def build_etf_analytics(
    repository: MarketRepository,
    instrument_id: int,
) -> FixedIncomeEtfAnalyticsResponse:

    metadata = _get_json(
        f"/etfs/{instrument_id}"
    )

    constituents = _get_json(
        f"/etfs/{instrument_id}/constituents"
    )

    if not constituents:
        raise EtfAnalyticsError(
            "ETF has no active constituents"
        )

    constituent_ids = [
        int(
            row[
                "constituent_instrument_id"
            ]
        )
        for row in constituents
    ]

    prices = repository.latest_prices_by_ids(
        constituent_ids
    )

    price_by_id = {
        int(price.instrument_id): price
        for price in prices
    }

    priced_weight = 0.0

    weighted_clean_price = 0.0
    weighted_yield = 0.0
    weighted_spread = 0.0
    weighted_duration = 0.0
    weighted_convexity = 0.0

    priced_count = 0

    for constituent in constituents:

        constituent_id = int(
            constituent[
                "constituent_instrument_id"
            ]
        )

        weight = float(
            constituent["weight"]
        )

        price = price_by_id.get(
            constituent_id
        )

        if price is None:
            continue

        priced_count += 1

        priced_weight += weight

        weighted_clean_price += (
            weight
            * float(
                price.clean_price
            )
        )

        weighted_yield += (
            weight
            * float(
                price.yield_to_maturity
            )
        )

        weighted_spread += (
            weight
            * float(
                price.g_spread_bps
            )
        )

        weighted_duration += (
            weight
            * float(
                price.modified_duration
            )
        )

        weighted_convexity += (
            weight
            * float(
                price.convexity
            )
        )

    if priced_weight <= 0.0:
        raise EtfAnalyticsError(
            "No constituent prices are available"
        )

    #
    # Normalize analytical averages over the portion
    # of the ETF basket for which prices are available.
    #
    weighted_clean_price /= priced_weight
    weighted_yield /= priced_weight
    weighted_spread /= priced_weight
    weighted_duration /= priced_weight
    weighted_convexity /= priced_weight

    #
    # The existing evaluated_prices table contains
    # bond-style evaluated values for the legacy ETF IDs.
    #
    # Those values are NOT valid ETF secondary-market
    # prices and must not be compared directly with ETF NAV.
    #
    # ETF market price / premium-discount will be populated
    # later from an ETF-specific quote/pricing source.
    #
    reference_nav = (
        float(metadata["nav"])
        if metadata.get("nav")
        is not None
        else None
    )

    quote = repository.latest_market_quote(
        instrument_id
    )

    bid = (
        quote.bid
        if quote
        else None
    )

    ask = (
        quote.ask
        if quote
        else None
    )

    mid = (
        quote.mid
        if quote
        else None
    )

    market_price = mid

    bid_ask_spread = None
    bid_ask_spread_bps = None

    if (
        bid is not None
        and ask is not None
    ):
        bid_ask_spread = (
            ask - bid
        )

        if (
            mid is not None
            and mid != 0.0
        ):
            bid_ask_spread_bps = (
                bid_ask_spread
                / mid
                * 10_000.0
            )

    premium_discount_percent = None

    if (
        mid is not None
        and reference_nav is not None
        and reference_nav != 0.0
    ):
        premium_discount_percent = (
            (
                mid
                / reference_nav
            )
            - 1.0
        ) * 100.0

    return FixedIncomeEtfAnalyticsResponse(
        instrument_id=instrument_id,

        fund_name=metadata[
            "fund_name"
        ],

        benchmark_name=metadata.get(
            "benchmark_name"
        ),

        constituent_count=len(
            constituents
        ),

        priced_constituent_count=(
            priced_count
        ),

        priced_weight=priced_weight,

        missing_weight=max(
            0.0,
            1.0 - priced_weight,
        ),

        weighted_clean_price=(
            weighted_clean_price
        ),

        weighted_yield_to_maturity=(
            weighted_yield
        ),

        weighted_g_spread_bps=(
            weighted_spread
        ),

        weighted_modified_duration=(
            weighted_duration
        ),

        weighted_convexity=(
            weighted_convexity
        ),

        reference_nav=reference_nav,

        market_price=market_price,

        bid=bid,
        ask=ask,
        mid=mid,

        bid_ask_spread=(
            bid_ask_spread
        ),

        bid_ask_spread_bps=(
            bid_ask_spread_bps
        ),

        premium_discount_percent=(
            premium_discount_percent
        ),

        quote_source=(
            quote.source
            if quote
            else None
        ),

        quote_timestamp=(
            quote.event_time
            if quote
            else None
        ),

        quote_reliability=(
            quote.source_reliability
            if quote
            else None
        ),

        expense_ratio=(
            float(
                metadata[
                    "expense_ratio"
                ]
            )
            if metadata.get(
                "expense_ratio"
            )
            is not None
            else None
        ),

        shares_outstanding=(
            float(
                metadata[
                    "shares_outstanding"
                ]
            )
            if metadata.get(
                "shares_outstanding"
            )
            is not None
            else None
        ),
    )
