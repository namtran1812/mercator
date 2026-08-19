# Mercator

**Event-driven fixed-income pricing, market-data, and research infrastructure built for correctness under concurrency, replay, and failure.**

Mercator is a production-oriented fixed-income pricing and research system built around C++23, Python, Kafka, ClickHouse, PostgreSQL, and Redis.

The project models a realistic market-data pipeline in which yield-curve updates arrive as ordered events, trigger selective bond repricing, and propagate evaluated prices to analytical and low-latency stores.

The main engineering focus is not simply calculating bond prices. Mercator is designed around the distributed-systems problems that appear once pricing becomes stateful and event driven:

- ordered market-state transitions
- dependency-aware incremental repricing
- concurrent pricing
- durable event persistence
- deterministic replay
- stale-write prevention
- idempotent redelivery
- crash recovery
- analytical and low-latency serving
- failure-injection and end-to-end verification

---

## Architecture

```text
                        Market / Curve Updates
                                 │
                                 ▼
                        ┌─────────────────┐
                        │      Kafka      │
                        │ market.curves.v1│
                        └────────┬────────┘
                                 │
                                 ▼
                 ┌─────────────────────────────┐
                 │      Pricing Worker         │
                 │          C++23              │
                 │                             │
                 │  Event validation           │
                 │  Version guard              │
                 │  Curve replay               │
                 │  Dependency resolution      │
                 │  Selective repricing        │
                 │  Parallel pricing           │
                 └───────┬───────────┬─────────┘
                         │           │
              durable    │           │ latest state
              history    │           │
                         ▼           ▼
                ┌──────────────┐  ┌──────────────┐
                │  ClickHouse  │  │    Redis     │
                │              │  │              │
                │ curve events │  │ latest price │
                │ prices       │  │ state        │
                │ checkpoints  │  │ CAS guarded  │
                └──────────────┘  └──────────────┘
                         │
                         ▼
                Historical Replay /
                Research / Analytics

                         ▲
                         │
                ┌────────────────┐
                │   PostgreSQL   │
                │                │
                │ instruments    │
                │ reference data │
                └────────────────┘
```

---

## Core Design

Mercator separates the system into several distinct responsibilities.

### PostgreSQL — Reference Data

PostgreSQL stores instrument and reference information used by the pricing engine.

Reference data is intentionally separated from high-volume analytical output and low-latency latest-state storage.

---

### Kafka — Ordered Market Events

Yield-curve changes enter the system as Kafka events.

A curve update carries explicit transition metadata:

```json
{
  "event_id": "1d12061a-9839-45bf-ad07-8b95d86d37f8",
  "event_time": "2026-08-19T00:17:37Z",
  "previous_version": 441,
  "new_version": 442,
  "updates": [
    {
      "node_id": 9,
      "maturity_years": 30.0,
      "old_rate": 0.0412,
      "new_rate": 0.0413
    }
  ]
}
```

The transition is explicit:

```text
curve version 441
        │
        ▼
validate previous_version == 441
        │
        ▼
apply curve update
        │
        ▼
curve version 442
```

This prevents the pricing engine from treating market events as unrelated messages.

---

### C++23 Pricing Engine

The pricing core implements fixed-income analytics including:

- cash-flow generation
- yield-curve construction
- clean and dirty pricing
- accrued interest
- yield-to-maturity calculations
- G-spread calculations
- modified duration
- convexity
- historical replay
- quote reconciliation
- data-quality checks

An evaluated price contains both financial output and lineage metadata:

```cpp
struct EvaluatedPrice {
    std::uint64_t instrument_id;

    double clean_price;
    double dirty_price;
    double yield_to_maturity;
    double g_spread_bps;
    double modified_duration;
    double convexity;

    std::uint64_t curve_version;
    std::uint64_t reference_version;

    double quality_score;
    std::string quality_status;

    std::string model_version;
    std::string calculation_trace_id;
    std::string source_event_id;

    std::chrono::system_clock::time_point event_time;
    std::chrono::system_clock::time_point received_time;
};
```

The lineage fields allow a persisted price to be associated with the exact market event and curve version that produced it.

---

## Dependency-Aware Repricing

A curve update should not necessarily require repricing every instrument.

Mercator maintains dependency information between curve nodes and instruments.

```text
Curve node changes
       │
       ▼
Dependency Graph
       │
       ├────────► Bond A
       ├────────► Bond B
       ├────────► Bond C
       │
       └────────► ...
```

The repricing layer supports:

- dependency-based fan-out
- selective repricing
- materiality thresholds
- sensitivity-budget policies
- adaptive repricing
- full-reprice fallback

This makes repricing policy an explicit part of the system instead of coupling every market event to a full-universe recalculation.

---

## Parallel Repricing

Affected instruments can be priced concurrently.

```text
                  Affected Instruments
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
         Worker 1     Worker 2    Worker N
             │           │           │
             └───────────┼───────────┘
                         ▼
                  Evaluated Prices
```

Mercator includes equivalence testing to ensure parallel execution produces results consistent with the deterministic pricing path.

---

## Durable Curve Commit

One of Mercator's central correctness requirements is:

> A market event must not be acknowledged before the state required to recover it is durable.

The processing lifecycle is therefore conceptually:

```text
Kafka event
    │
    ▼
Validate transition
    │
    ▼
Persist durable curve event
    │
    ▼
Apply / recover pricing work
    │
    ▼
Persist evaluated prices
    │
    ▼
Update latest-state Redis view
    │
    ▼
Commit / acknowledge Kafka offset
```

This ordering is important because Kafka delivery is at-least-once.

A process can fail between any two stages.

---

## Crash Recovery

Mercator explicitly tests the dangerous failure window:

```text
Kafka
  │
  ▼
curve event persisted
  │
  X  PROCESS CRASHES
```

At this point:

- the curve transition is durable
- pricing may not have completed
- the Kafka offset has not been committed

When the worker restarts with the same consumer group, Kafka redelivers the event.

The system distinguishes an already-completed duplicate from an event whose durable curve transition exists but whose downstream work is incomplete.

```text
                    Redelivered Event
                           │
                           ▼
                   Durable event exists?
                     /             \
                   no               yes
                   │                 │
                   ▼                 ▼
             normal apply       completed?
                               /          \
                             no            yes
                             │              │
                             ▼              ▼
                    recover pricing      cheap ACK
```

This distinction is critical.

A duplicate event does **not** automatically mean that all effects of the original processing attempt completed.

---

## Real Crash / Restart Verification

Mercator includes an end-to-end crash-recovery test that exercises the real infrastructure path:

```text
Kafka
  │
  ▼
C++ pricing worker
  │
  ▼
durable ClickHouse curve event
  │
  X injected process crash
  │
  ▼
worker restart
  │
  ▼
Kafka redelivery
  │
  ▼
incomplete-event recovery
  │
  ├────────► ClickHouse evaluated prices
  │
  └────────► Redis latest state
```

The test verifies:

1. the curve event becomes durable
2. the worker fails inside the injected crash window
3. no evaluated prices were committed before the crash
4. Kafka redelivers the uncommitted event
5. pricing completes after restart
6. Redis advances to the recovered event
7. ClickHouse versions remain monotonic
8. redelivery produces no logical duplicate prices

A successful run produces:

```text
PASS: curve event became durable
PASS: worker failed in injected crash window
PASS: no evaluated prices were committed before crash
PASS: Kafka event was redelivered and priced
PASS: Redis latest state advanced to recovered event
PASS: ClickHouse version advanced monotonically
PASS: redelivery produced no logical duplicate prices

========================================================================
PASS: REAL CRASH / RESTART RECOVERY
========================================================================

Kafka → durable curve event → crash → restart → redelivery
→ ClickHouse → Redis verified.
```

The recovery path was also exercised repeatedly across **20 real Kafka crash/restart cycles**, with every invariant passing on all 20 runs.

```text
PASS: curve event became durable                       20
PASS: worker failed in injected crash window           20
PASS: no evaluated prices were committed before crash  20
PASS: Kafka event was redelivered and priced           20
PASS: Redis latest state advanced to recovered event   20
PASS: ClickHouse version advanced monotonically        20
PASS: redelivery produced no logical duplicate prices  20
PASS: REAL CRASH / RESTART RECOVERY                    20
```

The soak test encountered one transient ClickHouse HTTP failure, recovered through retry handling, and completed with no hard errors.

---

## Completed Duplicate Fast Path

Recovery must not make normal duplicate handling expensive.

Mercator therefore preserves a cheap path for an event whose downstream work has already completed.

```text
event=<event-id> disposition=DUPLICATE current_version=442
```

The completed duplicate test verifies that:

- the consumer advances its Kafka offset
- the event does not enter incomplete recovery
- no additional evaluated-price rows are generated

Example verification:

```text
BEFORE=6574
AFTER=6574

PASS: completed duplicate stayed on cheap ACK path
PASS: completed duplicate created zero additional price rows
```

This keeps ordinary at-least-once Kafka redelivery inexpensive while still allowing incomplete events to be recovered safely.

---

## Redis Latest-State Consistency

ClickHouse stores analytical history.

Redis serves the latest evaluated state.

That creates another distributed-systems problem: concurrent writers must never allow an older market version to overwrite a newer one.

A naive implementation such as:

```text
GET current
compare version
SET new
```

is unsafe because the comparison and write are separate operations.

Mercator instead performs the version check and state update atomically through a Redis Lua compare-and-set operation.

Conceptually:

```text
incoming version
      │
      ▼
atomic Redis CAS
      │
      ├── newer ───────► accept
      │
      ├── duplicate ───► no-op
      │
      ├── stale ───────► reject
      │
      └── conflict ────► reject
```

Observed CAS behavior:

```text
first     : 1
newer     : 1
stale     : -1
duplicate : 0
conflict  : -2

FINAL VERSION: 11
FINAL EVENT: e11
```

---

## Concurrent Writer Protection

The Redis sink was stress-tested with 100 concurrent writers attempting to update the same instrument.

Example:

```text
writes: 100
accepted: 3
stale: 97
duplicates: 0
conflicts: 0

highest accepted: 100
final version: 100
final event: event-100

PASS: concurrent writers cannot regress latest market state.
```

Another run verified that only successfully accepted monotonic transitions were published:

```text
race writes: 100
race accepted: 5
published messages: 5

accepted versions:
[93, 94, 97, 99, 100]

published versions:
[93, 94, 97, 99, 100]

duplicate result: (100, 0)
stale result: (50, -1)
conflict result: (100, -2)

final version: 100
final event: event-100

PASS: only accepted monotonic price updates are published.
```

---

## Persistent Redis Connections

The Redis pricing sink maintains a persistent connection instead of reconnecting for every evaluated price.

This avoids placing connection establishment on the per-price hot path.

The implementation also handles connection failure by discarding an invalid client context so the next publish can establish a fresh connection.

Recovery testing verifies that Redis connectivity can be re-established while preserving monotonic state.

Example:

```text
Redis recovery: client 35239 -> 35242 final_version=3

Persistent Redis sink final: curve_version=10000

Concurrent Redis CAS final:
curve_version=100
source_event_id=event-100

All Redis price sink consistency tests passed.
```

The Redis recovery and CAS suite was repeatedly exercised:

```text
PASS: 50 Redis recovery + CAS runs
```

---

## Deterministic Replay

Historical market events can be replayed through the pricing system.

Replay is useful for:

- reproducing historical state
- validating pricing changes
- investigating incidents
- comparing model versions
- research experiments
- regression testing

Because market events carry explicit version and source-event metadata, replay can preserve lineage between an input transition and its generated prices.

---

## Data Stores

Mercator deliberately uses different stores for different workloads.

| Component | Responsibility |
|---|---|
| Kafka | Ordered market-event transport and redelivery |
| PostgreSQL | Instrument and reference data |
| ClickHouse | Historical curve events, checkpoints, and evaluated prices |
| Redis | Low-latency latest evaluated-price state |
| C++23 | Pricing, replay, dependency resolution, and event processing |
| Python | Integration tests, orchestration, research, and validation |

This avoids forcing one database to handle transactional reference data, analytical history, streaming transport, and low-latency latest-state access simultaneously.

---

## Testing Strategy

Mercator includes tests across financial correctness, state transitions, concurrency, replay, persistence, and recovery.

### Pricing and Analytics

```text
analytics_test.cpp
clean_price_test.cpp
yield_curve_test.cpp
quote_reconciliation_test.cpp
data_quality_test.cpp
pricing_test.cpp
```

### Dependency and Repricing

```text
dependency_graph_test.cpp
adaptive_repricing_test.cpp
parallel_repricing_equivalence_test.cpp
```

### Event Processing and Replay

```text
curve_event_pipeline_test.cpp
curve_replay_test.cpp
test_price_replay.cpp
```

### Persistence and Recovery

```text
durable_curve_commit_test.cpp
curve_recovery_test.cpp
redis_price_sink_test.cpp
```

The durable commit failure-injection suite was exercised repeatedly:

```text
PASS: 100 durable commit failure-injection runs
```

Crash/restart redelivery behavior was also stress-tested:

```text
PASS: 500 crash/restart redelivery runs
```

The Redis consistency suite passed repeated recovery and concurrency runs, and the full Kafka → worker → ClickHouse → Redis recovery path passed a 20-cycle real-infrastructure soak test.

---

## Benchmarks

The pricing engine contains dedicated benchmarks for several repricing strategies.

```text
incremental_repricing.cpp
selective_repricing.cpp
dependency_fanout.cpp
material_repricing.cpp
sensitivity_repricing.cpp
adaptive_repricing.cpp
```

These benchmarks allow different repricing policies to be evaluated independently rather than assuming that a single strategy is optimal for every market update.

---

## Repository Structure

```text
mercator/
│
├── services/
│   │
│   ├── pricing-engine/
│   │   ├── include/
│   │   │   └── mercator/
│   │   │       └── pricing/
│   │   │
│   │   ├── src/
│   │   │   ├── analytics.cpp
│   │   │   ├── cashflow.cpp
│   │   │   ├── yield_curve.cpp
│   │   │   ├── dependency_graph.cpp
│   │   │   ├── dependency_resolver.cpp
│   │   │   ├── repricing_service.cpp
│   │   │   ├── adaptive_repricing.cpp
│   │   │   ├── curve_event_parser.cpp
│   │   │   ├── curve_replay.cpp
│   │   │   ├── durable_curve_commit.cpp
│   │   │   ├── redis_price_sink.cpp
│   │   │   ├── clickhouse_price_sink.cpp
│   │   │   └── pricing_worker.cpp
│   │   │
│   │   ├── tests/
│   │   ├── benchmarks/
│   │   └── CMakeLists.txt
│   │
│   └── streaming-pricer/
│       └── legacy/
│
├── scripts/
│   └── tests/
│       └── pricing_worker_crash_recovery_e2e.py
│
└── README.md
```

---

## Building the Pricing Engine

Mercator requires a C++23-capable toolchain and the external libraries configured by the pricing-engine CMake project, including:

- nlohmann/json
- librdkafka
- libpq
- libcurl
- hiredis

Configure and build with CMake:

```bash
cmake \
  -S services/pricing-engine \
  -B build/pricing-engine

cmake \
  --build build/pricing-engine \
  -j
```

To build the event-driven worker specifically:

```bash
cmake \
  --build build/pricing-engine \
  -j \
  --target mercator-pricing-worker
```

---

## Running Tests

Run the C++ test suite with CTest:

```bash
ctest \
  --test-dir build/pricing-engine \
  --output-on-failure
```

Individual tests can also be executed directly.

For example:

```bash
./build/pricing-engine/mercator-redis-price-sink-tests
```

and:

```bash
./build/pricing-engine/mercator-durable-curve-commit-tests
```

---

## Running the Crash-Recovery E2E Test

With Kafka, ClickHouse, Redis, and PostgreSQL running:

```bash
export POSTGRES_DSN='postgresql://mercator:mercator@localhost:5433/mercator'

python \
  scripts/tests/pricing_worker_crash_recovery_e2e.py
```

A successful execution ends with:

```text
========================================================================
PASS: REAL CRASH / RESTART RECOVERY
========================================================================

Kafka → durable curve event → crash → restart → redelivery
→ ClickHouse → Redis verified.
```

---

## Correctness Invariants

Mercator is built around several explicit invariants.

### 1. Curve versions never regress

```text
incoming_version > current_version
```

is required for a new state transition.

---

### 2. Stale Redis writes cannot overwrite newer state

The latest-price update is protected by an atomic compare-and-set operation.

---

### 3. Equal-version conflicts are rejected

The same market version cannot silently represent two different source events.

---

### 4. Durable state precedes Kafka acknowledgement

A worker must not acknowledge an event before the state necessary for recovery has been persisted.

---

### 5. Incomplete duplicate events are recoverable

If a worker crashes after durable curve persistence but before downstream pricing completion, redelivery resumes the missing work.

---

### 6. Completed duplicates remain cheap

If the event has already completed downstream processing, redelivery is acknowledged without repricing it.

---

### 7. Redelivery does not create logical duplicate prices

Crash recovery preserves one logical evaluated-price result per instrument for the recovered event.

---

### 8. Parallel pricing preserves pricing semantics

Concurrency must change throughput, not financial results.

---

## Why Mercator Exists

A toy bond pricer can be implemented with a formula and a loop.

A realistic pricing system has a different set of problems.

What happens when:

- two market updates race?
- an older writer reaches Redis after a newer one?
- Kafka redelivers an event?
- the process crashes after durable persistence but before pricing?
- a duplicate represents unfinished work?
- a completed event is delivered again?
- thousands of instruments depend on only part of a changed curve?
- pricing is parallelized?
- analytical history and latest-state serving need different storage characteristics?
- historical market state must be reconstructed exactly?

Mercator is an attempt to explore those problems directly.

The result is a fixed-income system that combines financial analytics with the event-processing, concurrency, persistence, replay, and recovery concerns found in production market infrastructure.

---

## Tech Stack

**Core**

```text
C++23
Python
CMake
```

**Streaming**

```text
Apache Kafka
librdkafka
```

**Storage**

```text
ClickHouse
PostgreSQL
Redis
```

**Infrastructure / Testing**

```text
Docker
CTest
failure injection
integration testing
crash/restart testing
concurrency stress testing
```

---

## Current Status

Mercator currently supports:

- fixed-rate bond cash-flow generation
- yield-curve pricing
- clean and dirty prices
- accrued interest
- yield and G-spread calculations
- duration and convexity
- curve-event parsing
- dependency-aware repricing
- selective and adaptive repricing
- parallel repricing
- historical price replay
- durable curve-event persistence
- curve recovery
- Kafka-driven pricing
- ClickHouse historical storage
- Redis latest-state publication
- atomic Redis version protection
- persistent Redis connections and reconnect recovery
- duplicate/stale/conflict classification
- crash-window failure injection
- incomplete-event recovery
- completed-duplicate fast path
- real Kafka crash/restart/redelivery verification
- concurrency and recovery stress testing

The project has been validated against repeated failure scenarios, including **500 crash/restart redelivery test runs**, **50 Redis recovery/CAS runs**, **100 durable-commit failure-injection runs**, and **20 full real-infrastructure Kafka crash/restart recovery cycles**.

---

## Engineering Principles

Mercator follows a few simple principles:

**Correctness before throughput.**  
A fast price is useless if it represents stale or inconsistent market state.

**Make ordering explicit.**  
Versions and source-event identifiers are part of the data model rather than assumptions hidden inside the worker.

**Assume delivery can happen more than once.**  
Kafka redelivery is treated as a normal operating condition.

**Assume processes can die anywhere.**  
Recovery behavior is designed around explicit failure windows.

**Separate history from latest state.**  
ClickHouse and Redis serve different access patterns and therefore have different consistency responsibilities.

**Optimize only after preserving semantics.**  
Selective repricing, parallel execution, persistent connections, and duplicate fast paths are layered on top of explicit correctness invariants.

**Test failure paths, not only happy paths.**  
Concurrency races, stale updates, Redis reconnects, injected crashes, Kafka redelivery, and incomplete durable state are exercised directly.

---

## License

See the repository license for details.
