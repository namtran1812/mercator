from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[2]
        / "services"
        / "agent-runtime"
    ),
)

from mercator_agent.tools.pricing import (
    historical_price_as_of,
    replay_curve_state,
)
from mercator_agent.tools.reference_data import (
    get_instrument_version,
)


INSTRUMENT_ID = int(
    os.getenv(
        "MERCATOR_REPLAY_E2E_INSTRUMENT",
        "5965",
    )
)

AS_OF = os.getenv(
    "MERCATOR_REPLAY_E2E_AS_OF",
    "2026-08-18T05:19:53Z",
)

REPLAY_BINARY = Path(
    os.getenv(
        "MERCATOR_PRICE_REPLAY_BINARY",
        "build/pricing-engine/"
        "mercator-price-replay-cli",
    )
)


def fail(message: str) -> None:
    raise SystemExit(
        f"FAIL: {message}"
    )


def main() -> None:
    print("=" * 72)
    print("MERCATOR HISTORICAL REPLAY E2E")
    print("=" * 72)

    price = historical_price_as_of(
        INSTRUMENT_ID,
        as_of=AS_OF,
    )

    print(
        "instrument:",
        price.instrument_id,
    )
    print(
        "event_time:",
        price.event_time,
    )
    print(
        "curve_version:",
        price.curve_version,
    )
    print(
        "reference_version:",
        price.reference_version,
    )
    print(
        "source_event_id:",
        price.source_event_id,
    )
    print(
        "clean_price:",
        price.clean_price,
    )
    print(
        "dirty_price:",
        price.dirty_price,
    )

    reference = get_instrument_version(
        price.instrument_id,
        price.reference_version,
    )

    if reference.maturity_date is None:
        fail(
            "reference data has no maturity_date"
        )

    if reference.coupon_rate is None:
        fail(
            "reference data has no coupon_rate"
        )

    curve_state = replay_curve_state(
        price.curve_version,
        curve_name="UST",
    )

    curve_points = curve_state.curve_points
    events = curve_state.curve_events

    print(
        "curve_nodes:",
        len(curve_points),
    )
    print(
        "delta_events:",
        len(events),
    )

    if len(curve_points) != 9:
        fail(
            "expected 9 recovered curve nodes, "
            f"got {len(curve_points)}"
        )

    thirty_year = next(
        (
            point["zero_rate"]
            for point in curve_points
            if abs(
                point["maturity_years"]
                - 30.0
            ) < 1e-12
        ),
        None,
    )

    print(
        "curve_30y_rate:",
        thirty_year,
    )

    if thirty_year is None:
        fail(
            "recovered curve has no 30Y node"
        )

    request = {
        "instrument_id":
            price.instrument_id,

        "valuation_date":
            curve_state.valuation_date,

        # Reference Data API stores coupon in percent.
        # C++ pricing consumes decimal.
        "coupon_rate":
            float(reference.coupon_rate)
            / 100.0,

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
            1e-10,

        "curve_points":
            curve_points,
    }

    if not REPLAY_BINARY.exists():
        fail(
            f"replay binary not found: "
            f"{REPLAY_BINARY}"
        )

    completed = subprocess.run(
        [str(REPLAY_BINARY)],
        input=json.dumps(request),
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    print()
    print("===== VERIFIER STDOUT =====")
    print(
        completed.stdout.strip()
    )

    if completed.stderr.strip():
        print()
        print("===== VERIFIER STDERR =====")
        print(
            completed.stderr.strip()
        )

    if completed.returncode != 0:
        fail(
            "C++ replay verifier returned "
            f"{completed.returncode}"
        )

    try:
        result = json.loads(
            completed.stdout
        )
    except json.JSONDecodeError as exc:
        fail(
            "verifier returned invalid JSON: "
            f"{exc}"
        )

    print()
    print("===== REPLAY RESULT =====")
    print(
        json.dumps(
            result,
            indent=2,
        )
    )

    status = result.get(
        "status"
    )

    if status != "REPLAY_VERIFIED":
        fail(
            "historical price did not replay "
            f"exactly; status={status}"
        )

    clean_error = float(
        result.get(
            "clean_price_error",
            float("inf"),
        )
    )

    dirty_error = float(
        result.get(
            "dirty_price_error",
            float("inf"),
        )
    )

    if clean_error > 1e-10:
        fail(
            "clean price replay error exceeded "
            f"tolerance: {clean_error}"
        )

    if dirty_error > 1e-10:
        fail(
            "dirty price replay error exceeded "
            f"tolerance: {dirty_error}"
        )

    print()
    print("PASS")
    print(
        "Historical price was reproduced "
        "from durable curve + reference state."
    )


if __name__ == "__main__":
    main()
