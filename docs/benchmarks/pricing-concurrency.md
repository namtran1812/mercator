# Pricing Concurrency Benchmark

Mercator's event-driven C++ pricing worker was benchmarked across a
9,500-instrument fixed-income universe using the same 20-event curve-update
workload for each concurrency configuration.

Each workload rotated updates across the 2Y, 5Y, 10Y, and 30Y curve nodes and
exercised both FULL and SELECTIVE repricing.

## Results

| Pricing workers | Pricing mean (ms) | Pricing p50 (ms) | Pricing p95 (ms) | Pipeline mean (ms) | Pipeline p50 (ms) | Pipeline p95 (ms) |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 574.274 | 553.915 | 714.749 | 968.202 | 937.794 | 1120.038 |
| 2 | 285.355 | 283.724 | 318.192 | 668.814 | 677.937 | 827.067 |
| 4 | 170.651 | 161.484 | 228.843 | 574.683 | 542.974 | 724.456 |
| 8 | 146.594 | 133.908 | 194.014 | 574.003 | 527.428 | 671.707 |
| auto | 180.508 | 146.709 | 292.736 | 627.075 | 580.260 | 910.720 |

## Improvement

Relative to the single-worker baseline:

- 2 workers reduced mean pipeline latency by 30.92%.
- 4 workers reduced mean pipeline latency by 40.64%.
- 8 workers reduced mean pipeline latency by 40.71%.
- automatic hardware concurrency reduced mean pipeline latency by 35.23%.

At 8 workers:

- mean pricing latency fell from 574.274 ms to 146.594 ms, a 74.5% reduction;
- pricing p95 fell from 714.749 ms to 194.014 ms, a 72.9% reduction;
- mean measured worker-pipeline latency fell from 968.202 ms to 574.003 ms,
  a 40.7% reduction;
- pipeline p95 fell from 1120.038 ms to 671.707 ms, a 40.0% reduction.

## Interpretation

Pricing scales strongly through eight workers, but total pipeline latency
largely saturates between four and eight workers.

The 4-to-8-worker change reduces mean pricing time from 170.651 ms to
146.594 ms while mean pipeline latency remains approximately 574 ms.

This indicates that after parallelizing instrument valuation, downstream
ClickHouse persistence and Redis publication become the dominant contributors
to event-processing latency.

Mercator therefore defaults the dedicated pricing worker to eight pricing
workers while retaining PRICING_WORKERS as a runtime configuration option.

PRICING_WORKERS=0 selects automatic hardware concurrency.
