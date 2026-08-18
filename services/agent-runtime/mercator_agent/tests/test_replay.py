from __future__ import annotations

from datetime import date

import pytest

from mercator_agent.state.models import (
    CurveEventObservation,
    HistoricalPriceObservation,
    InstrumentProfile,
)

from mercator_agent.tools import replay


def _price() -> HistoricalPriceObservation:
    return HistoricalPriceObservation(
        instrument_id=2902,
        event_time="2026-08-18 01:38:31",
        clean_price=498.49,
        dirty_price=498.95,
        yield_to_maturity=0.0624,
        g_spread_bps=144.0,
        modified_duration=13.36,
        convexity=204.0,
        curve_version=162,
        reference_version=2902,
        quality_score=1.0,
        quality_status="VALID",
        model_version="test",
        calculation_trace_id=
            "11111111-1111-1111-1111-111111111111",
        source_event_id=
            "22222222-2222-2222-2222-222222222222",
    )


def _profile() -> InstrumentProfile:
    return InstrumentProfile(
        instrument_id=2902,
        instrument_type="CORPORATE_BOND",
        issuer_name="Harbor Utilities",
        # Reference Data API representation:
        # percentage, not decimal.
        coupon_rate=5.25,
        maturity_date=date(2042, 7, 23),
        rating="BBB-",
        sector="Technology",
        currency="USD",
        reference_version=2902,
    )


def _event(
    tenor: str = "30Y",
    new_rate: float = 0.0431,
) -> CurveEventObservation:
    return CurveEventObservation(
        event_time="2026-08-18 01:38:30",
        event_id="event",
        curve_version=162,
        curve_name="UST",
        tenor=tenor,
        old_rate=0.043,
        new_rate=new_rate,
        source="test",
        scenario_name="live",
        recorded_at="2026-08-18 01:38:30",
    )


def test_build_replay_snapshot_verified(
    monkeypatch,
) -> None:
    price = _price()
    profile = _profile()

    events = [
        _event("1Y", 0.04),
        _event("30Y", 0.0431),
    ]

    monkeypatch.setattr(
        replay,
        "historical_price_as_of",
        lambda instrument_id, as_of: price,
    )

    monkeypatch.setattr(
        replay,
        "get_instrument_version",
        lambda instrument_id, reference_version:
            profile,
    )

    monkeypatch.setattr(
        replay,
        "replay_curve_state",
        lambda curve_version:
            replay.CurveReplayState(
                curve_version=curve_version,
                valuation_date="2026-07-15",
                curve_points=
                    replay._reconstructed_curve_points(
                        events
                    ),
                curve_events=events,
            ),
    )

    captured = {}

    def verify(request):
        captured.update(request)

        return {
            "status": "REPLAY_VERIFIED",
            "instrument_id": 2902,
            "curve_version": 162,
            "reference_version": 2902,
            "persisted_clean_price": 498.49,
            "persisted_dirty_price": 498.95,
            "replayed_clean_price": 498.49,
            "replayed_dirty_price": 498.95,
            "clean_price_error": 0.0,
            "dirty_price_error": 0.0,
            "absolute_tolerance": 1e-10,
        }

    monkeypatch.setattr(
        replay,
        "_run_price_replay_verifier",
        verify,
    )

    result = replay.build_replay_snapshot(
        2902,
        as_of="2026-08-18T02:00:00Z",
    )

    assert (
        result.replay_status
        == "REPLAY_VERIFIED"
    )

    assert result.replayed_clean_price == 498.49
    assert result.clean_price_error == 0.0

    assert captured["curve_version"] == 162
    assert captured["reference_version"] == 2902

    assert captured["spread_bps"] == 144.0

    # Critical unit-boundary assertion.
    assert captured["coupon_rate"] == pytest.approx(
        0.0525
    )


def test_replay_uses_price_reference_version(
    monkeypatch,
) -> None:
    price = _price()

    price.reference_version = 41

    profile = _profile()
    profile.reference_version = 41

    captured = {}

    monkeypatch.setattr(
        replay,
        "historical_price_as_of",
        lambda instrument_id, as_of: price,
    )

    def version_lookup(
        instrument_id,
        reference_version,
    ):
        captured["reference_version"] = (
            reference_version
        )

        return profile

    monkeypatch.setattr(
        replay,
        "get_instrument_version",
        version_lookup,
    )

    monkeypatch.setattr(
        replay,
        "replay_curve_state",
        lambda curve_version:
            replay.CurveReplayState(
                curve_version=curve_version,
                valuation_date="2026-07-15",
                curve_points=[
                    {
                        "maturity_years": 30.0,
                        "zero_rate": 0.0431,
                    }
                ],
                curve_events=[
                    _event(
                        "30Y",
                        0.0431,
                    )
                ],
            ),
    )

    monkeypatch.setattr(
        replay,
        "_run_price_replay_verifier",
        lambda request: {
            "status": "REPLAY_VERIFIED",
            "replayed_clean_price":
                price.clean_price,
            "replayed_dirty_price":
                price.dirty_price,
            "clean_price_error": 0.0,
            "dirty_price_error": 0.0,
        },
    )

    replay.build_replay_snapshot(
        2902,
        as_of="2026-08-18T02:00:00Z",
    )

    assert captured["reference_version"] == 41


def test_curve_reconstruction_keeps_latest_rate() -> None:
    events = [
        _event("10Y", 0.041),
        _event("10Y", 0.042),
        _event("30Y", 0.045),
    ]

    assert replay._reconstructed_curve_points(
        events
    ) == [
        {
            "maturity_years": 10.0,
            "zero_rate": 0.042,
        },
        {
            "maturity_years": 30.0,
            "zero_rate": 0.045,
        },
    ]


def test_negative_tolerance_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="non-negative",
    ):
        replay.build_replay_snapshot(
            2902,
            as_of="2026-08-18T02:00:00Z",
            absolute_tolerance=-1.0,
        )
