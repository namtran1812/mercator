from __future__ import annotations

import argparse
import json
import math
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import request


MARKET_API = "http://127.0.0.1:8005"
REFERENCE_API = "http://127.0.0.1:8001"


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0

    ordered = sorted(values)

    index = (
        len(ordered) - 1
    ) * percentile_value

    lower = math.floor(index)
    upper = math.ceil(index)

    if lower == upper:
        return ordered[lower]

    weight = index - lower

    return (
        ordered[lower] * (1.0 - weight)
        + ordered[upper] * weight
    )


def http_request(
    url: str,
    *,
    method: str = "GET",
    payload: dict | None = None,
) -> tuple[float, int]:
    body = None

    headers = {}

    if payload is not None:
        body = json.dumps(
            payload,
        ).encode("utf-8")

        headers[
            "Content-Type"
        ] = "application/json"

    req = request.Request(
        url,
        data=body,
        headers=headers,
        method=method,
    )

    started = time.perf_counter()

    with request.urlopen(
        req,
        timeout=30,
    ) as response:
        response.read()

        status = response.status

    elapsed_ms = (
        time.perf_counter()
        - started
    ) * 1000.0

    return elapsed_ms, status


def benchmark(
    *,
    name: str,
    iterations: int,
    warmup: int,
    url: str,
    method: str = "GET",
    payload: dict | None = None,
) -> dict:
    for _ in range(warmup):
        http_request(
            url,
            method=method,
            payload=payload,
        )

    latencies = []

    successes = 0
    failures = 0

    for _ in range(iterations):
        try:
            elapsed_ms, status = (
                http_request(
                    url,
                    method=method,
                    payload=payload,
                )
            )

            latencies.append(
                elapsed_ms,
            )

            if 200 <= status < 300:
                successes += 1
            else:
                failures += 1

        except Exception:
            failures += 1

    return {
        "name": name,
        "iterations": iterations,
        "successes": successes,
        "failures": failures,
        "success_rate": (
            successes / iterations
            if iterations
            else 0.0
        ),
        "latency_ms": {
            "mean": statistics.mean(
                latencies,
            )
            if latencies
            else 0.0,

            "median": statistics.median(
                latencies,
            )
            if latencies
            else 0.0,

            "p95": percentile(
                latencies,
                0.95,
            ),

            "p99": percentile(
                latencies,
                0.99,
            ),

            "min": min(
                latencies,
            )
            if latencies
            else 0.0,

            "max": max(
                latencies,
            )
            if latencies
            else 0.0,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--iterations",
        type=int,
        default=100,
    )

    parser.add_argument(
        "--warmup",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--output",
        default=(
            "artifacts/benchmarks/"
            "workbench-latency-baseline.json"
        ),
    )

    args = parser.parse_args()

    cases = [
        {
            "name":
                "reference.instrument_lookup",

            "url":
                f"{REFERENCE_API}/instruments/1",
        },

        {
            "name":
                "reference.search",

            "url":
                (
                    f"{REFERENCE_API}"
                    "/instruments/search"
                    "?q=Northstar&limit=8"
                ),
        },

        {
            "name":
                "market.summary",

            "url":
                f"{MARKET_API}/market/summary",
        },

        {
            "name":
                "market.latest_prices",

            "url":
                (
                    f"{MARKET_API}"
                    "/prices/latest"
                    "?limit=100"
                    "&minimum_quality_score=0.8"
                ),
        },

        {
            "name":
                "market.price_history",

            "url":
                (
                    f"{MARKET_API}"
                    "/prices/1/history"
                    "?limit=100"
                ),
        },

        {
            "name":
                "risk.decomposition",

            "url":
                (
                    f"{MARKET_API}"
                    "/risk/decomposition"
                ),

            "method":
                "POST",

            "payload": {
                "instrument_ids":
                    [1, 2, 3, 4, 5],

                "position_notional":
                    1_000_000,
            },
        },

        {
            "name":
                "portfolio.risk",

            "url":
                (
                    f"{MARKET_API}"
                    "/portfolio/risk"
                ),

            "method":
                "POST",

            "payload": {
                "positions": [
                    {
                        "instrument_id": i,
                        "face_value":
                            1_000_000,
                    }
                    for i in range(
                        1,
                        6,
                    )
                ],
            },
        },

        {
            "name":
                "relative_value.rank",

            "url":
                (
                    f"{MARKET_API}"
                    "/relative-value/rank"
                ),

            "method":
                "POST",

            "payload": {
                "instrument_ids":
                    list(
                        range(
                            1,
                            101,
                        )
                    ),

                "duration_bucket_width":
                    1.5,

                "minimum_peer_count":
                    3,
            },
        },
    ]

    results = []

    print()
    print(
        "MERCATOR LATENCY BASELINE"
    )
    print("=" * 88)

    for case in cases:
        result = benchmark(
            name=case["name"],
            iterations=args.iterations,
            warmup=args.warmup,
            url=case["url"],
            method=case.get(
                "method",
                "GET",
            ),
            payload=case.get(
                "payload",
            ),
        )

        results.append(
            result,
        )

        latency = (
            result["latency_ms"]
        )

        print(
            f"{result['name']:30} "
            f"mean={latency['mean']:8.2f} ms  "
            f"p95={latency['p95']:8.2f} ms  "
            f"p99={latency['p99']:8.2f} ms  "
            f"success={result['success_rate'] * 100:6.2f}%"
        )

    report = {
        "generated_at":
            datetime.now(
                timezone.utc,
            ).isoformat(),

        "iterations":
            args.iterations,

        "warmup":
            args.warmup,

        "results":
            results,
    }

    output = Path(
        args.output,
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            report,
            indent=2,
        )
        + "\n",
    )

    print()
    print(
        f"Saved baseline -> {output}"
    )


if __name__ == "__main__":
    main()
