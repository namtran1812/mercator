from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import clickhouse_connect
import redis

from mercator_agent.state.models import (
    CurveEventObservation,
    CurveReplayState,
    HistoricalPriceObservation,
    PriceMoveAttribution,
    PriceObservation,
)


REDIS_HOST = os.getenv(
    "REDIS_HOST",
    "127.0.0.1",
)

REDIS_PORT = int(
    os.getenv(
        "REDIS_PORT",
        "6380",
    )
)

REDIS_DB = int(
    os.getenv(
        "REDIS_DB",
        "0",
    )
)


def _demo_latest_prices(
    instrument_ids: list[int],
) -> list[PriceObservation]:
    return [
        PriceObservation(
            instrument_id=instrument_id,

            clean_price=
                760.0
                + (
                    instrument_id * 37
                )
                % 360,

            dirty_price=
                762.0
                + (
                    instrument_id * 37
                )
                % 360,

            yield_to_maturity=
                0.045
                + (
                    instrument_id % 40
                )
                * 0.001,

            g_spread_bps=
                85.0
                + (
                    instrument_id * 29
                )
                % 315,

            modified_duration=
                2.0
                + (
                    instrument_id % 145
                )
                / 10.0,

            convexity=None,

            quality_score=0.95,
            quality_status="VALID",

            curve_version=2,
            reference_version=1,

            source="demo",
        )
        for instrument_id
        in instrument_ids
    ]


def _demo_mode() -> bool:
    return (
        os.getenv(
            "MERCATOR_DEMO_MODE",
            "false",
        ).lower()
        in {
            "1",
            "true",
            "yes",
            "on",
        }
    )


def _redis_client() -> redis.Redis:
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=5,
    )


def _clickhouse_client():
    return clickhouse_connect.get_client(
        host=os.getenv(
            "CLICKHOUSE_HOST",
            "localhost",
        ),
        port=int(
            os.getenv(
                "CLICKHOUSE_PORT",
                "8123",
            )
        ),
        username=os.getenv(
            "CLICKHOUSE_USERNAME",
            "mercator",
        ),
        password=os.getenv(
            "CLICKHOUSE_PASSWORD",
            "mercator",
        ),
        database=os.getenv(
            "CLICKHOUSE_DATABASE",
            "mercator",
        ),
    )


def latest_prices(
    instrument_ids: list[int],
) -> list[PriceObservation]:
    """
    Return authoritative current evaluated prices.

    Redis is the low-latency latest-state store.
    ClickHouse is intentionally not queried here.
    """

    if not instrument_ids:
        return []

    if _demo_mode():
        return _demo_latest_prices(
            instrument_ids
        )

    client = _redis_client()

    keys = [
        f"mercator:price:{instrument_id}"
        for instrument_id
        in instrument_ids
    ]

    payloads = client.mget(
        keys
    )

    results: list[
        PriceObservation
    ] = []

    for instrument_id, payload in zip(
        instrument_ids,
        payloads,
        strict=True,
    ):
        if payload is None:
            continue

        data = json.loads(
            payload
        )

        actual_instrument_id = int(
            data.get(
                "instrument_id",
                instrument_id,
            )
        )

        if actual_instrument_id != instrument_id:
            raise ValueError(
                "Redis pricing key/payload "
                "instrument mismatch: "
                f"key={instrument_id} "
                f"payload={actual_instrument_id}"
            )

        results.append(
            PriceObservation(
                instrument_id=
                    actual_instrument_id,

                clean_price=
                    float(
                        data["clean_price"]
                    ),

                dirty_price=
                    float(
                        data["dirty_price"]
                    ),

                yield_to_maturity=
                    float(
                        data[
                            "yield_to_maturity"
                        ]
                    ),

                g_spread_bps=
                    float(
                        data[
                            "g_spread_bps"
                        ]
                    ),

                modified_duration=
                    float(
                        data[
                            "modified_duration"
                        ]
                    ),

                convexity=(
                    float(
                        data["convexity"]
                    )
                    if data.get(
                        "convexity"
                    )
                    is not None
                    else None
                ),

                quality_score=
                    float(
                        data.get(
                            "quality_score",
                            1.0,
                        )
                    ),

                quality_status=
                    str(
                        data[
                            "quality_status"
                        ]
                    ),

                curve_version=
                    int(
                        data[
                            "curve_version"
                        ]
                    ),

                reference_version=(
                    int(
                        data[
                            "reference_version"
                        ]
                    )
                    if data.get(
                        "reference_version"
                    )
                    is not None
                    else None
                ),

                event_time=
                    data.get(
                        "event_time"
                    ),

                price_change=(
                    float(
                        data[
                            "price_change"
                        ]
                    )
                    if data.get(
                        "price_change"
                    )
                    is not None
                    else None
                ),

                source_event_id=
                    data.get(
                        "source_event_id"
                    ),

                calculation_trace_id=
                    data.get(
                        "calculation_trace_id"
                    ),

                dependency_tenor=
                    data.get(
                        "dependency_tenor"
                    ),

                dependency_weight=(
                    float(
                        data[
                            "dependency_weight"
                        ]
                    )
                    if data.get(
                        "dependency_weight"
                    )
                    is not None
                    else None
                ),

                source="redis",
            )
        )

    return results


def price_history(
    instrument_id: int,
    *,
    limit: int = 50,
) -> list[HistoricalPriceObservation]:
    """
    Return historical evaluated prices newest-first.
    """

    if limit <= 0:
        return []

    limit = min(
        limit,
        500,
    )

    client = _clickhouse_client()

    result = client.query(
        """
        SELECT
            instrument_id,
            event_time,
            clean_price,
            dirty_price,
            yield_to_maturity,
            g_spread_bps,
            modified_duration,
            convexity,
            curve_version,
            reference_version,
            quality_score,
            quality_status,
            model_version,
            calculation_trace_id,
            source_event_id
        FROM evaluated_prices
        WHERE instrument_id =
            {instrument_id:UInt64}
        ORDER BY event_time DESC
        LIMIT {limit:UInt32}
        """,
        parameters={
            "instrument_id":
                instrument_id,

            "limit":
                limit,
        },
    )

    return [
        HistoricalPriceObservation(
            instrument_id=int(row[0]),
            event_time=str(row[1]),

            clean_price=float(row[2]),
            dirty_price=float(row[3]),

            yield_to_maturity=
                float(row[4]),

            g_spread_bps=
                float(row[5]),

            modified_duration=
                float(row[6]),

            convexity=
                float(row[7]),

            curve_version=
                int(row[8]),

            reference_version=
                int(row[9]),

            quality_score=
                float(row[10]),

            quality_status=
                str(row[11]),

            model_version=
                str(row[12]),

            calculation_trace_id=
                str(row[13]),

            source_event_id=
                str(row[14]),

            source="clickhouse",
        )
        for row
        in result.result_rows
    ]


def curve_events(
    *,
    curve_name: str = "UST",
    since_version: int | None = None,
    limit: int = 50,
) -> list[CurveEventObservation]:
    """
    Return recent yield-curve events newest-first.
    """

    if limit <= 0:
        return []

    limit = min(
        limit,
        500,
    )

    client = _clickhouse_client()

    version_filter = ""

    parameters: dict[str, object] = {
        "curve_name":
            curve_name,

        "limit":
            limit,
    }

    if since_version is not None:
        version_filter = """
        AND curve_version >=
            {since_version:UInt64}
        """

        parameters[
            "since_version"
        ] = since_version

    result = client.query(
        f"""
        SELECT
            event_time,
            event_id,
            curve_version,
            curve_name,
            tenor,
            old_rate,
            new_rate,
            source,
            scenario_name,
            recorded_at
        FROM curve_events
        WHERE curve_name =
            {{curve_name:String}}
        {version_filter}
        ORDER BY
            curve_version DESC,
            event_time DESC
        LIMIT {{limit:UInt32}}
        """,
        parameters=parameters,
    )

    return [
        CurveEventObservation(
            event_time=str(row[0]),
            event_id=str(row[1]),

            curve_version=
                int(row[2]),

            curve_name=
                str(row[3]),

            tenor=
                str(row[4]),

            old_rate=
                float(row[5]),

            new_rate=
                float(row[6]),

            source=
                str(row[7]),

            scenario_name=
                str(row[8]),

            recorded_at=
                str(row[9]),
        )
        for row
        in result.result_rows
    ]


def explain_price_move(
    instrument_id: int,
) -> PriceMoveAttribution:
    """
    Deterministically attribute the latest observed price move
    to the associated yield-curve event.

    Duration and convexity provide a local approximation of the
    curve-driven return. Any unexplained difference is reported
    as a residual; no causal explanation is invented for it.
    """

    prices = latest_prices(
        [instrument_id]
    )

    if not prices:
        raise ValueError(
            "No current price available for "
            f"instrument {instrument_id}"
        )

    price = prices[0]

    events = curve_events(
        since_version=price.curve_version,
        limit=50,
    )

    event = next(
        (
            item
            for item in events
            if (
                item.curve_version
                == price.curve_version
                and (
                    price.source_event_id is None
                    or item.event_id
                    == price.source_event_id
                )
                and (
                    price.dependency_tenor is None
                    or item.tenor
                    == price.dependency_tenor
                )
            )
        ),
        None,
    )

    previous_price = None

    history = price_history(
        instrument_id,
        limit=10,
    )

    for observation in history:
        if (
            observation.curve_version
            < price.curve_version
        ):
            previous_price = observation
            break

    observed_change = price.price_change

    if (
        observed_change is None
        and previous_price is not None
    ):
        observed_change = (
            price.clean_price
            - previous_price.clean_price
        )

    previous_clean_price = (
        previous_price.clean_price
        if previous_price is not None
        else (
            price.clean_price
            - observed_change
            if observed_change is not None
            else None
        )
    )

    observed_return = None

    if (
        observed_change is not None
        and previous_clean_price is not None
        and previous_clean_price != 0.0
    ):
        observed_return = (
            observed_change
            / previous_clean_price
        )

    if event is None:
        return PriceMoveAttribution(
            instrument_id=instrument_id,
            curve_version=price.curve_version,
            source_event_id=price.source_event_id,
            dependency_tenor=price.dependency_tenor,
            current_clean_price=price.clean_price,
            previous_clean_price=previous_clean_price,
            observed_price_change=observed_change,
            observed_return=observed_return,
            modified_duration=price.modified_duration,
            convexity=price.convexity,
            explanation=(
                "The latest price move is available, but no "
                "matching stored curve event was found, so "
                "Mercator cannot make a deterministic "
                "curve attribution."
            ),
        )

    delta_y = (
        event.new_rate
        - event.old_rate
    )

    rate_change_bps = (
        delta_y
        * 10_000.0
    )

    duration_return = (
        -price.modified_duration
        * delta_y
    )

    convexity_return = (
        0.5
        * price.convexity
        * delta_y
        * delta_y
        if price.convexity is not None
        else None
    )

    estimated_curve_return = (
        duration_return
        + (
            convexity_return
            if convexity_return is not None
            else 0.0
        )
    )

    estimated_curve_price_change = None

    if previous_clean_price is not None:
        estimated_curve_price_change = (
            previous_clean_price
            * estimated_curve_return
        )

    residual = None

    if (
        observed_change is not None
        and estimated_curve_price_change
        is not None
    ):
        residual = (
            observed_change
            - estimated_curve_price_change
        )

    direction = (
        "rose"
        if rate_change_bps > 0.0
        else "fell"
        if rate_change_bps < 0.0
        else "was unchanged"
    )

    explanation = (
        f"The {event.tenor} curve rate {direction} by "
        f"{abs(rate_change_bps):.2f} bp. "
        f"With modified duration "
        f"{price.modified_duration:.2f}"
    )

    if price.convexity is not None:
        explanation += (
            f" and convexity "
            f"{price.convexity:.2f}"
        )

    explanation += (
        ", the local duration/convexity approximation "
        f"implies a curve-driven return of "
        f"{estimated_curve_return * 100.0:.4f}%."
    )

    if observed_change is not None:
        explanation += (
            f" The observed clean-price change was "
            f"{observed_change:+.6f}."
        )

    if residual is not None:
        explanation += (
            f" The remaining residual was "
            f"{residual:+.6f}; Mercator does not assign "
            "a causal explanation to that residual "
            "without additional evidence."
        )

    return PriceMoveAttribution(
        instrument_id=instrument_id,
        curve_version=price.curve_version,
        source_event_id=price.source_event_id,
        dependency_tenor=event.tenor,
        old_rate=event.old_rate,
        new_rate=event.new_rate,
        rate_change_bps=rate_change_bps,
        previous_clean_price=previous_clean_price,
        current_clean_price=price.clean_price,
        observed_price_change=observed_change,
        observed_return=observed_return,
        modified_duration=price.modified_duration,
        convexity=price.convexity,
        duration_return=duration_return,
        convexity_return=convexity_return,
        estimated_curve_return=estimated_curve_return,
        estimated_curve_price_change=
            estimated_curve_price_change,
        residual_price_change=residual,
        explanation=explanation,
    )


def historical_price_as_of(
    instrument_id: int,
    *,
    as_of: str,
) -> HistoricalPriceObservation:
    """
    Return the most recent evaluated price whose event_time is not
    later than as_of.
    """
    client = _clickhouse_client()

    result = client.query(
        """
        SELECT
            instrument_id,
            event_time,
            clean_price,
            dirty_price,
            yield_to_maturity,
            g_spread_bps,
            modified_duration,
            convexity,
            curve_version,
            reference_version,
            quality_score,
            quality_status,
            model_version,
            calculation_trace_id,
            source_event_id
        FROM evaluated_prices
        WHERE instrument_id =
            {instrument_id:UInt64}
          AND event_time <=
            parseDateTime64BestEffort({as_of:String})
        ORDER BY event_time DESC
        LIMIT 1
        """,
        parameters={
            "instrument_id": instrument_id,
            "as_of": as_of,
        },
    )

    if not result.result_rows:
        raise ValueError(
            "No evaluated price exists at or before "
            f"{as_of} for instrument {instrument_id}."
        )

    row = result.result_rows[0]

    return HistoricalPriceObservation(
        instrument_id=int(row[0]),
        event_time=str(row[1]),
        clean_price=float(row[2]),
        dirty_price=float(row[3]),
        yield_to_maturity=float(row[4]),
        g_spread_bps=float(row[5]),
        modified_duration=float(row[6]),
        convexity=float(row[7]),
        curve_version=int(row[8]),
        reference_version=int(row[9]),
        quality_score=float(row[10]),
        quality_status=str(row[11]),
        model_version=str(row[12]),
        calculation_trace_id=str(row[13]),
        source_event_id=str(row[14]),
        source="clickhouse",
    )



def replay_curve_state(
    curve_version: int,
    *,
    curve_name: str = "UST",
) -> CurveReplayState:
    """
    Reconstruct the complete durable curve state at curve_version.

    Recovery starts from the newest persisted checkpoint at or before
    the requested version and applies only subsequent curve events.

    The event chain is validated so replay fails closed on missing or
    inconsistent durable history rather than silently constructing a
    partial curve.
    """
    if curve_version < 0:
        raise ValueError(
            "curve_version must be non-negative"
        )

    client = _clickhouse_client()

    checkpoint_result = client.query(
        """
        SELECT
            curve_version,
            valuation_date,
            maturity_years,
            zero_rates
        FROM curve_checkpoints
        WHERE curve_name = {curve_name:String}
          AND curve_version <= {curve_version:UInt64}
        ORDER BY curve_version DESC
        LIMIT 1
        """,
        parameters={
            "curve_name": curve_name,
            "curve_version": curve_version,
        },
    )

    checkpoint_version = 0
    valuation_date: str | None = None
    points: dict[float, float] = {}

    if checkpoint_result.result_rows:
        row = checkpoint_result.result_rows[0]

        checkpoint_version = int(row[0])
        valuation_date = str(row[1])

        maturities = [
            float(value)
            for value in row[2]
        ]
        rates = [
            float(value)
            for value in row[3]
        ]

        if len(maturities) != len(rates):
            raise ValueError(
                "Persisted curve checkpoint contains mismatched "
                "maturity and rate arrays."
            )

        points = dict(zip(maturities, rates))

    event_result = client.query(
        """
        SELECT
            event_time,
            event_id,
            curve_version,
            previous_version,
            curve_name,
            tenor,
            maturity_years,
            old_rate,
            new_rate,
            source,
            scenario_name,
            recorded_at
        FROM curve_events
        WHERE curve_name = {curve_name:String}
          AND curve_version > {checkpoint_version:UInt64}
          AND curve_version <= {curve_version:UInt64}
        ORDER BY
            curve_version ASC,
            recorded_at ASC,
            event_id ASC
        """,
        parameters={
            "curve_name": curve_name,
            "checkpoint_version": checkpoint_version,
            "curve_version": curve_version,
        },
    )

    events: list[CurveEventObservation] = []

    # A curve version may contain multiple persisted rows. Validate the
    # version transition once per distinct version while applying every
    # node update belonging to that version.
    current_version = checkpoint_version
    seen_event_ids: set[str] = set()
    seen_versions: set[int] = set()

    for row in event_result.result_rows:
        event_id = str(row[1])

        # MergeTree tables can expose duplicate deliveries. Event IDs
        # are the durable idempotency key for replay.
        if event_id in seen_event_ids:
            continue

        seen_event_ids.add(event_id)

        event_version = int(row[2])
        previous_version = int(row[3])

        if event_version not in seen_versions:
            if previous_version != current_version:
                raise ValueError(
                    "Curve replay history is not contiguous: "
                    f"version {event_version} declares previous "
                    f"version {previous_version}, expected "
                    f"{current_version}."
                )

            seen_versions.add(event_version)
            current_version = event_version

        maturity_years = float(row[6])

        if maturity_years <= 0.0:
            # Compatibility with history written before maturity_years
            # was persisted explicitly.
            tenor = str(row[5]).strip().upper()

            if tenor.endswith("Y"):
                maturity_years = float(tenor[:-1])
            elif tenor.endswith("M"):
                maturity_years = (
                    float(tenor[:-1]) / 12.0
                )
            else:
                raise ValueError(
                    "Persisted curve event has no usable maturity "
                    f"for tenor {row[5]!r}."
                )

        points[maturity_years] = float(row[8])

        events.append(
            CurveEventObservation(
                event_time=str(row[0]),
                event_id=event_id,
                curve_version=event_version,
                curve_name=str(row[4]),
                tenor=str(row[5]),
                old_rate=float(row[7]),
                new_rate=float(row[8]),
                source=str(row[9]),
                scenario_name=str(row[10]),
                recorded_at=str(row[11]),
            )
        )

    if current_version != curve_version:
        raise ValueError(
            "Cannot reconstruct requested curve version "
            f"{curve_version}: durable history reaches only "
            f"version {current_version}."
        )

    if not points:
        raise ValueError(
            "Cannot reconstruct curve because neither a durable "
            "checkpoint nor replayable curve events are available."
        )

    if valuation_date is None:
        raise ValueError(
            "Cannot numerically replay curve without a "
            "persisted checkpoint valuation date."
        )

    curve_points = [
        {
            "maturity_years": maturity,
            "zero_rate": rate,
        }
        for maturity, rate in sorted(points.items())
    ]

    return CurveReplayState(
        curve_version=curve_version,
        valuation_date=valuation_date,
        curve_points=curve_points,
        curve_events=events,
    )


def curve_events_through_version(
    curve_version: int,
    *,
    curve_name: str = "UST",
    limit: int = 500,
) -> list[CurveEventObservation]:
    """
    Return persisted curve events through the requested version.

    Results are oldest-first so callers can reason about the event
    sequence deterministically.
    """
    if limit <= 0:
        return []

    limit = min(limit, 500)

    client = _clickhouse_client()

    result = client.query(
        """
        SELECT
            event_time,
            event_id,
            curve_version,
            curve_name,
            tenor,
            old_rate,
            new_rate,
            source,
            scenario_name,
            recorded_at
        FROM curve_events
        WHERE curve_name =
            {curve_name:String}
          AND curve_version <=
            {curve_version:UInt64}
        ORDER BY
            curve_version DESC,
            event_time DESC
        LIMIT {limit:UInt32}
        """,
        parameters={
            "curve_name": curve_name,
            "curve_version": curve_version,
            "limit": limit,
        },
    )

    observations = [
        CurveEventObservation(
            event_time=str(row[0]),
            event_id=str(row[1]),
            curve_version=int(row[2]),
            curve_name=str(row[3]),
            tenor=str(row[4]),
            old_rate=float(row[5]),
            new_rate=float(row[6]),
            source=str(row[7]),
            scenario_name=str(row[8]),
            recorded_at=str(row[9]),
        )
        for row in result.result_rows
    ]

    observations.reverse()

    return observations
