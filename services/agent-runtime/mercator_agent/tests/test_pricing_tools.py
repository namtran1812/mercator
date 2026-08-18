from __future__ import annotations

import json

from mercator_agent.tools import pricing


class FakeRedis:
    def __init__(
        self,
        payloads: dict[str, str],
    ) -> None:
        self.payloads = payloads

    def mget(
        self,
        keys: list[str],
    ) -> list[str | None]:
        return [
            self.payloads.get(key)
            for key in keys
        ]


class FakeQueryResult:
    def __init__(
        self,
        rows: list[tuple],
    ) -> None:
        self.result_rows = rows


class FakeClickHouse:
    def __init__(
        self,
        rows: list[tuple],
    ) -> None:
        self.rows = rows

    def query(
        self,
        query: str,
        *,
        parameters: dict,
    ) -> FakeQueryResult:
        del query
        del parameters

        return FakeQueryResult(
            self.rows
        )


def test_latest_prices_uses_redis(
    monkeypatch,
) -> None:
    payload = {
        "instrument_id": 101,
        "clean_price": 99.25,
        "dirty_price": 99.75,
        "yield_to_maturity": 0.051,
        "g_spread_bps": 125.0,
        "modified_duration": 6.5,
        "convexity": 48.0,
        "curve_version": 162,
        "reference_version": 7,
        "quality_score": 0.96,
        "quality_status": "VALID",
        "event_time":
            "2026-08-17T21:00:00Z",
        "price_change": -0.20,
        "source_event_id":
            "11111111-2222-5333-8444-555555555555",
        "calculation_trace_id":
            "aaaaaaaa-bbbb-5ccc-8ddd-eeeeeeeeeeee",
        "dependency_tenor": "10Y",
        "dependency_weight": 1.0,
    }

    monkeypatch.setattr(
        pricing,
        "_demo_mode",
        lambda: False,
    )

    monkeypatch.setattr(
        pricing,
        "_redis_client",
        lambda: FakeRedis({
            "mercator:price:101":
                json.dumps(payload),
        }),
    )

    results = pricing.latest_prices(
        [101]
    )

    assert len(results) == 1

    result = results[0]

    assert result.instrument_id == 101
    assert result.curve_version == 162
    assert result.reference_version == 7
    assert result.source == "redis"
    assert result.dependency_tenor == "10Y"


def test_latest_prices_skips_missing_keys(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        pricing,
        "_demo_mode",
        lambda: False,
    )

    monkeypatch.setattr(
        pricing,
        "_redis_client",
        lambda: FakeRedis({}),
    )

    assert pricing.latest_prices(
        [999]
    ) == []


def test_price_history_uses_clickhouse(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        pricing,
        "_clickhouse_client",
        lambda: FakeClickHouse([
            (
                101,
                "2026-08-17 21:00:00",
                99.25,
                99.75,
                0.051,
                125.0,
                6.5,
                48.0,
                162,
                7,
                0.96,
                "VALID",
                "mercator-pricer-0.1.0",
                "aaaaaaaa-bbbb-5ccc-8ddd-eeeeeeeeeeee",
                "11111111-2222-5333-8444-555555555555",
            ),
        ]),
    )

    results = pricing.price_history(
        101,
        limit=10,
    )

    assert len(results) == 1

    assert (
        results[0].instrument_id
        == 101
    )

    assert (
        results[0].curve_version
        == 162
    )

    assert (
        results[0].source
        == "clickhouse"
    )


def test_curve_events_uses_clickhouse(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        pricing,
        "_clickhouse_client",
        lambda: FakeClickHouse([
            (
                "2026-08-17 21:00:00",
                "11111111-2222-5333-8444-555555555555",
                162,
                "UST",
                "10Y",
                0.046,
                0.0461,
                "benchmark",
                "",
                "2026-08-17 21:00:01",
            ),
        ]),
    )

    results = pricing.curve_events(
        curve_name="UST",
        since_version=162,
    )

    assert len(results) == 1
    assert results[0].curve_version == 162
    assert results[0].tenor == "10Y"


def test_explain_price_move_rate_increase(
    monkeypatch,
) -> None:
    current = pricing.PriceObservation(
        instrument_id=101,
        clean_price=98.0,
        dirty_price=98.5,
        yield_to_maturity=0.05,
        g_spread_bps=120.0,
        modified_duration=5.0,
        convexity=40.0,
        quality_status="VALID",
        curve_version=10,
        reference_version=1,
        price_change=-1.0,
        source_event_id=(
            "11111111-2222-5333-8444-555555555555"
        ),
        dependency_tenor="10Y",
        source="redis",
    )

    previous = pricing.HistoricalPriceObservation(
        instrument_id=101,
        event_time="2026-08-17 20:00:00",
        clean_price=99.0,
        dirty_price=99.5,
        yield_to_maturity=0.049,
        g_spread_bps=120.0,
        modified_duration=5.0,
        convexity=40.0,
        curve_version=9,
        reference_version=1,
        quality_score=1.0,
        quality_status="VALID",
        model_version="test",
        calculation_trace_id=(
            "aaaaaaaa-bbbb-5ccc-8ddd-eeeeeeeeeeee"
        ),
        source_event_id=(
            "00000000-0000-5000-8000-000000000000"
        ),
    )

    event = pricing.CurveEventObservation(
        event_time="2026-08-17 21:00:00",
        event_id=(
            "11111111-2222-5333-8444-555555555555"
        ),
        curve_version=10,
        curve_name="UST",
        tenor="10Y",
        old_rate=0.0400,
        new_rate=0.0420,
        source="test",
        scenario_name="",
        recorded_at="2026-08-17 21:00:01",
    )

    monkeypatch.setattr(
        pricing,
        "latest_prices",
        lambda ids: [current],
    )

    monkeypatch.setattr(
        pricing,
        "price_history",
        lambda instrument_id, limit=10: [
            current.model_copy(
                update={
                    "event_time":
                        "2026-08-17 21:00:00",
                }
            ),
            previous,
        ],
    )

    monkeypatch.setattr(
        pricing,
        "curve_events",
        lambda **kwargs: [event],
    )

    result = pricing.explain_price_move(
        101
    )

    assert result.instrument_id == 101
    assert abs(
        result.rate_change_bps - 20.0
    ) < 1e-12

    assert abs(
        result.duration_return
        - (-0.01)
    ) < 1e-12

    assert abs(
        result.convexity_return
        - 0.00008
    ) < 1e-12

    assert abs(
        result.estimated_curve_return
        - (-0.00992)
    ) < 1e-12


def test_explain_price_move_rate_decrease(
    monkeypatch,
) -> None:
    current = pricing.PriceObservation(
        instrument_id=101,
        clean_price=101.0,
        dirty_price=101.5,
        yield_to_maturity=0.04,
        g_spread_bps=120.0,
        modified_duration=5.0,
        convexity=40.0,
        quality_status="VALID",
        curve_version=10,
        reference_version=1,
        price_change=1.0,
        source_event_id=(
            "11111111-2222-5333-8444-555555555555"
        ),
        dependency_tenor="10Y",
        source="redis",
    )

    event = pricing.CurveEventObservation(
        event_time="2026-08-17 21:00:00",
        event_id=(
            "11111111-2222-5333-8444-555555555555"
        ),
        curve_version=10,
        curve_name="UST",
        tenor="10Y",
        old_rate=0.0420,
        new_rate=0.0400,
        source="test",
        scenario_name="",
        recorded_at="2026-08-17 21:00:01",
    )

    monkeypatch.setattr(
        pricing,
        "latest_prices",
        lambda ids: [current],
    )

    monkeypatch.setattr(
        pricing,
        "price_history",
        lambda instrument_id, limit=10: [],
    )

    monkeypatch.setattr(
        pricing,
        "curve_events",
        lambda **kwargs: [event],
    )

    result = pricing.explain_price_move(
        101
    )

    assert abs(
        result.rate_change_bps - (-20.0)
    ) < 1e-12

    assert result.duration_return > 0.0

    assert result.estimated_curve_return > 0.0


def test_explain_price_move_requires_exact_event_match(
    monkeypatch,
) -> None:
    current = pricing.PriceObservation(
        instrument_id=101,
        clean_price=100.0,
        dirty_price=100.5,
        yield_to_maturity=0.05,
        g_spread_bps=120.0,
        modified_duration=5.0,
        convexity=40.0,
        quality_status="VALID",
        curve_version=10,
        source_event_id=(
            "11111111-2222-5333-8444-555555555555"
        ),
        dependency_tenor="10Y",
        source="redis",
    )

    wrong_event = pricing.CurveEventObservation(
        event_time="2026-08-17 21:00:00",
        event_id=(
            "99999999-2222-5333-8444-555555555555"
        ),
        curve_version=10,
        curve_name="UST",
        tenor="10Y",
        old_rate=0.0400,
        new_rate=0.0410,
        source="test",
        scenario_name="",
        recorded_at="2026-08-17 21:00:01",
    )

    monkeypatch.setattr(
        pricing,
        "latest_prices",
        lambda ids: [current],
    )

    monkeypatch.setattr(
        pricing,
        "price_history",
        lambda instrument_id, limit=10: [],
    )

    monkeypatch.setattr(
        pricing,
        "curve_events",
        lambda **kwargs: [wrong_event],
    )

    result = pricing.explain_price_move(
        101
    )

    assert result.old_rate is None
    assert result.new_rate is None
    assert result.rate_change_bps is None

    assert (
        "no matching stored curve event"
        in result.explanation.lower()
    )


def test_explain_price_move_uses_previous_history(
    monkeypatch,
) -> None:
    current = pricing.PriceObservation(
        instrument_id=101,
        clean_price=101.0,
        dirty_price=101.5,
        yield_to_maturity=0.05,
        g_spread_bps=120.0,
        modified_duration=5.0,
        convexity=40.0,
        quality_status="VALID",
        curve_version=10,
        price_change=None,
        source_event_id=(
            "11111111-2222-5333-8444-555555555555"
        ),
        dependency_tenor="10Y",
        source="redis",
    )

    previous = pricing.HistoricalPriceObservation(
        instrument_id=101,
        event_time="2026-08-17 20:00:00",
        clean_price=100.0,
        dirty_price=100.5,
        yield_to_maturity=0.05,
        g_spread_bps=120.0,
        modified_duration=5.0,
        convexity=40.0,
        curve_version=9,
        reference_version=1,
        quality_score=1.0,
        quality_status="VALID",
        model_version="test",
        calculation_trace_id=(
            "aaaaaaaa-bbbb-5ccc-8ddd-eeeeeeeeeeee"
        ),
        source_event_id=(
            "00000000-0000-5000-8000-000000000000"
        ),
    )

    event = pricing.CurveEventObservation(
        event_time="2026-08-17 21:00:00",
        event_id=(
            "11111111-2222-5333-8444-555555555555"
        ),
        curve_version=10,
        curve_name="UST",
        tenor="10Y",
        old_rate=0.0410,
        new_rate=0.0400,
        source="test",
        scenario_name="",
        recorded_at="2026-08-17 21:00:01",
    )

    monkeypatch.setattr(
        pricing,
        "latest_prices",
        lambda ids: [current],
    )

    monkeypatch.setattr(
        pricing,
        "price_history",
        lambda instrument_id, limit=10: [
            previous
        ],
    )

    monkeypatch.setattr(
        pricing,
        "curve_events",
        lambda **kwargs: [event],
    )

    result = pricing.explain_price_move(
        101
    )

    assert result.previous_clean_price == 100.0
    assert result.observed_price_change == 1.0
    assert result.observed_return == 0.01


def test_explain_price_move_missing_price() -> None:
    from unittest.mock import patch

    with patch.object(
        pricing,
        "latest_prices",
        return_value=[],
    ):
        try:
            pricing.explain_price_move(
                999
            )

        except ValueError as error:
            assert (
                "no current price"
                in str(error).lower()
            )

        else:
            raise AssertionError(
                "Expected ValueError."
            )
