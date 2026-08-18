from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
from typing import Any

from mercator_agent.state.models import (
    CurveReplayState,
    ReplayReferenceSnapshot,
    ReplaySnapshot,
)

from mercator_agent.tools.pricing import (
    historical_price_as_of,
    replay_curve_state,
)

from mercator_agent.tools.reference_data import (
    get_instrument_version,
)


DEFAULT_REPLAY_TOLERANCE = 1e-10


def _default_price_replay_binary() -> Path:
    """
    Resolve the production C++ replay verifier.

    MERCATOR_PRICE_REPLAY_BINARY may be used when the agent runtime
    is launched outside the repository tree.
    """
    configured = os.getenv(
        "MERCATOR_PRICE_REPLAY_BINARY"
    )

    if configured:
        return Path(configured)

    return (
        Path(__file__).resolve().parents[4]
        / "build"
        / "pricing-engine"
        / "mercator-price-replay-cli"
    )


def _coupon_rate_decimal(
    coupon_rate: float | None,
) -> float:
    """
    Convert the Reference Data API coupon representation to the
    decimal representation consumed by the pricing engine.

    Reference Data stores coupon percentages (for example 5.25),
    while pricing consumes decimal rates (0.0525).
    """
    if coupon_rate is None:
        raise ValueError(
            "Historical reference data does not contain "
            "a coupon rate."
        )

    return float(coupon_rate) / 100.0


def _tenor_years(
    tenor: str,
) -> float:
    normalized = tenor.strip().upper()

    if normalized.endswith("Y"):
        return float(normalized[:-1])

    if normalized.endswith("M"):
        return float(normalized[:-1]) / 12.0

    raise ValueError(
        f"Unsupported replay curve tenor: {tenor!r}"
    )


def _reconstructed_curve_points(
    events,
) -> list[dict[str, float]]:
    """
    Reconstruct the terminal curve state represented by the
    persisted event stream.

    Each event stores the old and new rate for one tenor. Applying
    the events oldest-first leaves the final rate for every tenor.
    """
    points: dict[float, float] = {}

    for event in events:
        maturity_years = _tenor_years(
            event.tenor
        )

        points[maturity_years] = float(
            event.new_rate
        )

    if not points:
        raise ValueError(
            "Cannot numerically replay price because no persisted "
            "curve events exist through the requested curve version."
        )

    return [
        {
            "maturity_years": maturity,
            "zero_rate": rate,
        }
        for maturity, rate in sorted(
            points.items()
        )
    ]


def _build_verifier_request(
    *,
    price,
    reference,
    curve_points: list[dict[str, float]],
    valuation_date: str,
    absolute_tolerance: float,
) -> dict[str, Any]:
    if reference.maturity_date is None:
        raise ValueError(
            "Historical reference data does not contain "
            "a maturity date."
        )

    # The pricing worker currently constructs a deterministic
    # synthetic spread because Reference Data does not yet persist
    # a market-spread field. Historical evaluated_prices does,
    # however, persist the actual g-spread used by the observation,
    # so replay must use that persisted spread.
    return {
        "instrument_id":
            price.instrument_id,

        "valuation_date":
            valuation_date,

        "coupon_rate":
            _coupon_rate_decimal(
                reference.coupon_rate
            ),

        "maturity_date":
            reference.maturity_date.isoformat(),

        "face_value":
            1000.0,

        "payments_per_year":
            2,

        "spread_bps":
            float(price.g_spread_bps),

        "curve_version":
            int(price.curve_version),

        "reference_version":
            int(price.reference_version),

        "clean_price":
            float(price.clean_price),

        "dirty_price":
            float(price.dirty_price),

        "absolute_tolerance":
            float(absolute_tolerance),

        "curve_points":
            curve_points,
    }


def _run_price_replay_verifier(
    request: dict[str, Any],
    *,
    binary: Path | None = None,
) -> dict[str, Any]:
    executable = (
        binary
        if binary is not None
        else _default_price_replay_binary()
    )

    if not executable.exists():
        raise FileNotFoundError(
            "Mercator C++ replay verifier was not found at "
            f"{executable}. Build target "
            "'mercator-price-replay-cli' first or set "
            "MERCATOR_PRICE_REPLAY_BINARY."
        )

    completed = subprocess.run(
        [str(executable)],
        input=json.dumps(request),
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    stdout = completed.stdout.strip()

    if not stdout:
        raise RuntimeError(
            "Mercator C++ replay verifier returned no JSON. "
            f"stderr={completed.stderr.strip()!r}"
        )

    try:
        response = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "Mercator C++ replay verifier returned invalid JSON: "
            f"{stdout!r}"
        ) from error

    if not isinstance(response, dict):
        raise RuntimeError(
            "Mercator C++ replay verifier returned an "
            "unexpected payload."
        )

    if completed.returncode != 0:
        raise RuntimeError(
            "Mercator C++ replay verifier failed: "
            f"{response.get('error', response)!r}"
        )

    return response


def build_replay_snapshot(
    instrument_id: int,
    *,
    as_of: str,
    absolute_tolerance: float =
        DEFAULT_REPLAY_TOLERANCE,
) -> ReplaySnapshot:
    """
    Reconstruct and independently verify a persisted historical
    evaluated price using Mercator's production C++ pricing path.
    """
    if absolute_tolerance < 0.0:
        raise ValueError(
            "Replay absolute tolerance must be non-negative."
        )

    price = historical_price_as_of(
        instrument_id,
        as_of=as_of,
    )

    reference = get_instrument_version(
        instrument_id,
        price.reference_version,
    )

    curve_state = replay_curve_state(
        price.curve_version
    )

    curve_points = curve_state.curve_points
    events = curve_state.curve_events

    reference_snapshot = ReplayReferenceSnapshot(
        instrument_id=reference.instrument_id,
        reference_version=price.reference_version,
        issuer_name=reference.issuer_name,
        instrument_type=reference.instrument_type,
        coupon_rate=reference.coupon_rate,
        maturity_date=reference.maturity_date,
        rating=reference.rating,
        sector=reference.sector,
        currency=reference.currency,
    )

    request = _build_verifier_request(
        price=price,
        reference=reference,
        curve_points=curve_points,
        valuation_date=curve_state.valuation_date,
        absolute_tolerance=absolute_tolerance,
    )

    verification = _run_price_replay_verifier(
        request
    )

    status = str(
        verification.get(
            "status",
            "REPLAY_ERROR",
        )
    )

    if status not in {
        "REPLAY_VERIFIED",
        "REPLAY_MISMATCH",
    }:
        raise RuntimeError(
            "Mercator C++ replay verifier returned "
            f"unexpected status {status!r}."
        )

    clean_error = float(
        verification["clean_price_error"]
    )

    dirty_error = float(
        verification["dirty_price_error"]
    )

    if status == "REPLAY_VERIFIED":
        explanation = (
            "Mercator reconstructed the historical reference-data "
            "version and yield-curve state, then independently "
            "repriced the instrument through the production C++ "
            "pricing engine. The replayed clean and dirty prices "
            "match the persisted observation within the configured "
            "absolute tolerance."
        )
    else:
        explanation = (
            "Mercator reconstructed the historical reference-data "
            "version and yield-curve state and repriced the "
            "instrument through the production C++ pricing engine, "
            "but the replayed price differs from the persisted "
            "observation beyond the configured absolute tolerance."
        )

    return ReplaySnapshot(
        instrument_id=instrument_id,
        requested_as_of=as_of,
        price=price,
        reference=reference_snapshot,
        curve_version=price.curve_version,
        curve_events=events,
        calculation_trace_id=
            price.calculation_trace_id,
        source_event_id=
            price.source_event_id,
        replay_status=status,
        replayed_clean_price=float(
            verification[
                "replayed_clean_price"
            ]
        ),
        replayed_dirty_price=float(
            verification[
                "replayed_dirty_price"
            ]
        ),
        clean_price_error=clean_error,
        dirty_price_error=dirty_error,
        replay_absolute_tolerance=
            absolute_tolerance,
        explanation=explanation,
    )
