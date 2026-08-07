from __future__ import annotations

from datetime import (
    datetime,
    timedelta,
    timezone,
)
from math import sin

from .models import (
    LatestBondPrice,
    MarketQuoteSnapshot,
    MarketSummary,
    PriceHistoryPoint,
)


def demo_latest_price(
    instrument_id: int,
    *,
    event_time: datetime | None = None,
) -> LatestBondPrice:
    now = (
        event_time
        or datetime.now(
            timezone.utc
        )
    )

    clean_price = (
        760.0
        + (
            instrument_id
            * 37
        )
        % 360
        + sin(
            instrument_id
            * 0.73
        )
        * 14
    )

    yield_to_maturity = (
        0.045
        + (
            instrument_id
            % 40
        )
        * 0.001
    )

    g_spread_bps = (
        85.0
        + (
            instrument_id
            * 29
        )
        % 315
    )

    modified_duration = (
        2.0
        + (
            instrument_id
            % 145
        )
        / 10.0
    )

    convexity = (
        modified_duration
        * modified_duration
        * 1.35
    )

    dirty_price = (
        clean_price
        + (
            instrument_id
            % 31
        )
        / 10.0
    )

    return LatestBondPrice(
        instrument_id=
            instrument_id,

        clean_price=
            clean_price,

        dirty_price=
            dirty_price,

        yield_to_maturity=
            yield_to_maturity,

        g_spread_bps=
            g_spread_bps,

        modified_duration=
            modified_duration,

        convexity=
            convexity,

        quality_score=
            0.95,

        quality_status=
            "VALID",

        curve_version=
            2,

        reference_version=
            1,

        event_time=
            now,
    )


def demo_latest_prices(
    *,
    limit: int,
    minimum_quality_score: float,
) -> list[LatestBondPrice]:
    if minimum_quality_score > 0.95:
        return []

    return [
        demo_latest_price(
            instrument_id
        )
        for instrument_id
        in range(
            1,
            limit + 1,
        )
    ]


def demo_latest_prices_by_ids(
    instrument_ids: list[int],
) -> list[LatestBondPrice]:
    return [
        demo_latest_price(
            instrument_id
        )
        for instrument_id
        in instrument_ids
    ]


def demo_market_summary() -> MarketSummary:
    prices = demo_latest_prices(
        limit=500,
        minimum_quality_score=0.0,
    )

    widest = max(
        prices,
        key=lambda item:
            item.g_spread_bps,
    )

    return MarketSummary(
        instrument_count=
            len(prices),

        average_clean_price=
            sum(
                item.clean_price
                for item in prices
            )
            / len(prices),

        average_yield_to_maturity=
            sum(
                item.yield_to_maturity
                for item in prices
            )
            / len(prices),

        average_g_spread_bps=
            sum(
                item.g_spread_bps
                for item in prices
            )
            / len(prices),

        widest_instrument_id=
            widest.instrument_id,

        widest_g_spread_bps=
            widest.g_spread_bps,
    )


def demo_price_history(
    *,
    instrument_id: int,
    limit: int,
) -> list[PriceHistoryPoint]:
    now = datetime.now(
        timezone.utc
    )

    points = []

    count = min(
        limit,
        120,
    )

    for index in range(
        count
    ):
        event_time = (
            now
            - timedelta(
                hours=index,
            )
        )

        latest = demo_latest_price(
            instrument_id,
            event_time=event_time,
        )

        movement = (
            sin(
                (
                    instrument_id
                    + index
                )
                * 0.41
            )
            * 2.5
        )

        clean_price = (
            latest.clean_price
            + movement
        )

        points.append(
            PriceHistoryPoint(
                event_time=
                    event_time,

                clean_price=
                    clean_price,

                dirty_price=
                    latest.dirty_price
                    + movement,

                yield_to_maturity=
                    latest.yield_to_maturity
                    - movement
                    / 10000.0,

                g_spread_bps=
                    latest.g_spread_bps
                    - movement
                    * 2.0,

                modified_duration=
                    latest.modified_duration,

                convexity=
                    latest.convexity,

                quality_score=
                    latest.quality_score,

                quality_status=
                    latest.quality_status,

                curve_version=
                    latest.curve_version,

                reference_version=
                    latest.reference_version,

                model_version=
                    "demo-v1",

                calculation_trace_id=
                    (
                        "demo-"
                        f"{instrument_id}-"
                        f"{index}"
                    ),

                source_event_id=
                    (
                        "demo-source-"
                        f"{instrument_id}-"
                        f"{index}"
                    ),
            )
        )

    return points


def demo_market_quote(
    instrument_id: int,
) -> MarketQuoteSnapshot:
    now = datetime.now(
        timezone.utc
    )

    if instrument_id >= 9500:
        mid = (
            95.0
            + (
                instrument_id
                % 37
            )
            * 0.013
        )

    else:
        mid = (
            demo_latest_price(
                instrument_id
            ).clean_price
        )

    spread = (
        0.04
        + (
            instrument_id
            % 7
        )
        * 0.01
    )

    return MarketQuoteSnapshot(
        instrument_id=
            instrument_id,

        bid=
            mid
            - spread
            / 2.0,

        ask=
            mid
            + spread
            / 2.0,

        mid=
            mid,

        source=
            "mercator-demo",

        source_reliability=
            0.95,

        accepted=
            True,

        event_time=
            now,
    )
