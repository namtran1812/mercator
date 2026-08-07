from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: str) -> dict:
    return json.loads(
        Path(path).read_text()
    )


def index(report: dict) -> dict:
    return {
        result["name"]: result
        for result in report[
            "results"
        ]
    }


def improvement(
    before: float,
    after: float,
) -> float:
    if before == 0:
        return 0.0

    return (
        (before - after)
        / before
        * 100.0
    )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "baseline",
    )

    parser.add_argument(
        "candidate",
    )

    args = parser.parse_args()

    before = index(
        load(args.baseline),
    )

    after = index(
        load(args.candidate),
    )

    print()
    print(
        "MERCATOR LATENCY COMPARISON"
    )
    print("=" * 100)

    print(
        f"{'Benchmark':30}"
        f"{'Before p95':>14}"
        f"{'After p95':>14}"
        f"{'Improvement':>15}"
    )

    print("-" * 100)

    improvements = []

    for name in sorted(
        before.keys()
        & after.keys()
    ):
        before_p95 = (
            before[name]
            ["latency_ms"]
            ["p95"]
        )

        after_p95 = (
            after[name]
            ["latency_ms"]
            ["p95"]
        )

        gain = improvement(
            before_p95,
            after_p95,
        )

        improvements.append(
            gain,
        )

        print(
            f"{name:30}"
            f"{before_p95:14.2f}"
            f"{after_p95:14.2f}"
            f"{gain:14.2f}%"
        )

    if improvements:
        average = (
            sum(improvements)
            / len(improvements)
        )

        print("-" * 100)

        print(
            f"{'Average':58}"
            f"{average:14.2f}%"
        )


if __name__ == "__main__":
    main()
