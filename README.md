# Mercator

A production-style fixed-income research, pricing, and analytics platform for corporate bonds and fixed-income ETFs.

Mercator combines real-time evaluated pricing, versioned reference data, portfolio analytics, risk and stress testing, ETF basket analysis, deterministic market replay, and agent-based research behind a single workstation.

The full local system uses a C++ event-driven pricing engine backed by Kafka, PostgreSQL, ClickHouse, and Redis.

**Live Demo:** https://mercator-khgs.onrender.com

> The public deployment runs in demo mode using deterministic market snapshots and Neon-backed reference data. The full local architecture supports PostgreSQL, ClickHouse, Kafka, Redis, and the C++ pricing worker.

---

## Overview

Mercator is designed around the infrastructure and workflows behind a fixed-income research and pricing platform rather than a standalone dashboard.

The system supports:

- 10,000+ corporate bonds and fixed-income ETFs
- C++ event-driven evaluated pricing
- Kafka-based curve event processing
- dependency-aware selective repricing
- adaptive selective vs. full-universe repricing
- versioned reference data
- evaluated bond prices and historical observations
- yield, spread, duration, and convexity analytics
- ClickHouse analytical price history
- Redis latest-price state
- WebSocket price streaming
- event ordering and version-gap detection
- idempotent event persistence and replay
- relative-value analysis
- portfolio risk decomposition
- historical VaR
- stress and scenario analysis
- hedge recommendations
- portfolio and risk-budget optimization
- fixed-income ETF NAV and basket analytics
- deterministic market replay
- natural-language research queries through an agent runtime
- a terminal-style research workstation

---

## Live Demo

**Mercator Workstation**

https://mercator-khgs.onrender.com

Example agent query:

```text
Show the NAV discount, market quote, and basket analytics for ETF 9501.
```

Example routing decision:

```text
intent: etf_analytics
fast_path: true

routing:
  research: false
  prices: true
  relative_value: false
  risk: false
  stress: false
  hedge: false
  etf_analytics: true
```

The hosted version is intentionally lightweight so it can run on free infrastructure. It uses deterministic market data while retaining the same research and analytics interfaces used by the full local system.

---

## Architecture

```text
                         ┌──────────────────────┐
                         │  Mercator Workbench  │
                         │  HTML / CSS / JS     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      Market API      │
                         │       FastAPI        │
                         └──────────┬───────────┘
                                    │
             ┌──────────────────────┼──────────────────────┐
             │                      │                      │
             ▼                      ▼                      ▼
    ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
    │  Reference Data  │   │  Agent Runtime   │   │ Market Analytics │
    │     Service      │   │                  │   │                  │
    └────────┬─────────┘   └────────┬─────────┘   └────────┬─────────┘
             │                      │                      │
             ▼                      │                      ▼
    ┌──────────────────┐            │             ┌──────────────────┐
    │    PostgreSQL    │◄───────────┘             │    ClickHouse    │
    │ versioned data   │                          │ pricing/history  │
    └──────────────────┘                          └────────▲─────────┘
                                                         │
                                                         │
                                              ┌──────────┴──────────┐
                                              │ C++ Pricing Worker  │
                                              │ adaptive repricing  │
                                              └──────────▲──────────┘
                                                         │
                                                         ▼
                                                   ┌───────────┐
                                                   │   Kafka   │
                                                   └───────────┘
                                                         │
                                                         │
                                              ┌──────────▼──────────┐
                                              │       Redis         │
                                              │ latest price state  │
                                              └──────────┬──────────┘
                                                         │
                                                         ▼
                                                   WebSockets
```

### Full local infrastructure

```text
PostgreSQL
ClickHouse
Kafka
Redis
C++ Pricing Engine
FastAPI Services
WebSocket Streaming Gateway
```

### Public deployment

```text
Browser
   │
   ▼
Render
Mercator Market API
   │
   ├── Workbench
   │
   ├── Market analytics
   │
   ├── Reference Data gateway
   │        │
   │        ▼
   │      Neon
   │    PostgreSQL
   │
   └── Agent gateway
            │
            ▼
       Agent Runtime
```

The Market API acts as the public gateway, allowing the browser to use same-origin endpoints without exposing internal service addresses.

---

## Event-Driven Pricing Pipeline

The full local architecture includes a C++ event-driven pricing worker responsible for processing curve updates and generating evaluated fixed-income prices.

```text
Curve Update
     │
     ▼
┌─────────────┐
│    Kafka    │
└──────┬──────┘
       │
       ▼
┌────────────────────────────┐
│     C++ Pricing Worker     │
│                            │
│  Curve event parser        │
│  Version guard             │
│  Dependency graph          │
│  Adaptive repricing        │
│  Bond pricing analytics    │
└────────────┬───────────────┘
             │
       ┌─────┴─────┐
       ▼           ▼
┌────────────┐ ┌────────────┐
│ ClickHouse │ │   Redis    │
│ historical │ │ latest     │
│ prices     │ │ prices     │
└────────────┘ └─────┬──────┘
                     │
                     ▼
                 WebSocket
                  Gateway
```

A curve event contains:

```text
event_id
event_time
previous_version
new_version
updates
```

Each update identifies the changed curve node, its maturity, and its old and new rates.

---

## Adaptive Repricing

Mercator does not automatically reprice the entire instrument universe after every market-data update.

The pricing engine maintains dependencies between instruments and curve nodes and determines which instruments are materially affected by each event.

The worker chooses between:

```text
SKIP
SELECTIVE
FULL
```

### SKIP

No repricing is required when the update does not materially affect instrument valuations under the configured pricing-error budget.

### SELECTIVE

Only instruments dependent on the changed curve region are recalculated.

This reduces unnecessary computation for localized curve movements.

### FULL

If the affected portion of the universe becomes sufficiently large, the worker performs a full-universe reprice instead of maintaining a large selective set.

The decision uses:

```text
dependency fanout
pricing-error budget
affected-instrument fraction
full-reprice threshold
```

The full-reprice fraction is configurable through:

```text
FULL_REPRICE_FRACTION
```

---

## Dependency-Aware Pricing

Each instrument maintains exposure to relevant curve nodes.

For example, a movement in the 30-year Treasury curve does not necessarily require recalculating every security in the universe.

The dependency graph identifies affected instruments before pricing begins.

Observed fanouts in the current synthetic universe include:

```text
2Y update     → up to 9,500 affected instruments
5Y update     → up to 8,874 affected instruments
10Y update    → up to 7,541 affected instruments
30Y update    → up to 6,566 affected instruments
```

Broad updates cross the configured threshold and trigger full repricing, while smaller fanouts can remain selective.

---

## Event Ordering and Version Guard

Curve events are processed using monotonically increasing versions.

The pricing worker maintains the current committed curve version and classifies incoming events before applying them.

It detects:

```text
VALID NEXT VERSION
DUPLICATE
STALE
GAP
```

For an expected transition:

```text
current version = N
previous_version = N
new_version = N + 1
```

the event may proceed.

An already-processed event is rejected as a duplicate.

An event older than the committed state is rejected as stale.

An event that jumps ahead of the expected version is classified as a gap rather than silently corrupting the pricing state.

---

## Failure Recovery

Kafka offsets are not committed immediately when an event is consumed.

The processing order is:

```text
1. consume Kafka event
2. validate event version
3. construct next curve state
4. determine affected instruments
5. calculate evaluated prices
6. persist prices to ClickHouse
7. publish latest prices to Redis
8. commit version state
9. commit Kafka offset
```

If durable persistence fails, the Kafka offset is not advanced.

The event can therefore be redelivered and processed again after the downstream dependency recovers.

This behavior was exercised during load testing when ClickHouse temporarily rejected an insert because of its configured memory limit. Processing resumed after the persistence layer recovered without advancing past the failed event.

---

## Idempotent Persistence

Kafka provides at-least-once delivery semantics, so a worker can receive the same event again after a partial failure.

Mercator protects ClickHouse from duplicate logical pricing records using a deduplication token derived from:

```text
source_event_id
```

The ClickHouse insert uses:

```text
insert_deduplication_token
```

for event-level retry protection.

Logical uniqueness is validated across:

```text
(source_event_id, instrument_id)
```

Recovery and replay testing produced:

```text
duplicate logical rows: 0
```

after processing repeated and redelivered events.

---

## Evaluated Pricing

Mercator maintains evaluated fixed-income prices and analytics including:

```text
clean price
dirty price
yield to maturity
G-spread
modified duration
convexity
quality score
quality status
curve version
reference version
event time
received time
source event ID
model version
calculation trace ID
```

Example observation:

```json
{
  "instrument_id": 1,
  "clean_price": 806.3362,
  "dirty_price": 806.4362,
  "yield_to_maturity": 0.046,
  "g_spread_bps": 114.0,
  "modified_duration": 2.1,
  "convexity": 5.9535,
  "quality_score": 0.95,
  "quality_status": "VALID"
}
```

Evaluated-price history is persisted in ClickHouse for analytical queries.

---

## Live Price State

Historical observations and current market state serve different workloads.

ClickHouse stores the historical evaluated-price stream.

Redis maintains the latest price for each instrument.

A latest-price record contains fields such as:

```text
instrument_id
clean_price
dirty_price
yield_to_maturity
g_spread_bps
modified_duration
convexity
curve_version
quality_status
event_time
price_change
source_event_id
dependency_tenor
dependency_weight
```

Example:

```json
{
  "instrument_id": 1,
  "curve_version": 5,
  "quality_status": "VALID",
  "dependency_tenor": "30Y",
  "dependency_weight": 1.0,
  "price_change": -3.3604452587
}
```

Redis provides low-latency access to the current evaluated state without querying historical ClickHouse data.

---

## Streaming Gateway

The streaming gateway subscribes to:

```text
mercator:price-updates
```

through Redis Pub/Sub.

Incoming price updates are broadcast to connected WebSocket clients through:

```text
/ws/prices
```

This separates durable analytical history from low-latency application updates.

```text
C++ Pricing Worker
       │
       ▼
     Redis
       │
       ▼
  Redis Pub/Sub
       │
       ▼
 FastAPI Gateway
       │
       ▼
   WebSocket
       │
       ▼
    Browser
```

---

## End-to-End Validation

Mercator includes a production-path smoke test covering:

```text
Kafka
  │
  ▼
C++ Pricing Worker
  │
  ├──────────► ClickHouse
  │
  └──────────► Redis
```

The test:

1. determines the current curve version
2. generates the next valid curve event
3. publishes it to Kafka
4. waits for the C++ worker
5. verifies ClickHouse persistence
6. verifies the expected unique instrument count
7. verifies Redis advanced to the same curve version
8. checks logical duplicate counts

A validated selective repricing run produced:

```text
previous version: 28
new version: 29

ClickHouse rows:       4000
Unique instruments:    4000
Redis curve version:   29
Global logical duplicates: 0
```

Result:

```text
Kafka → C++ worker → ClickHouse → Redis verified successfully.
```

---

## Pricing Load Test

A 20-event workload was executed against the production-path pricing worker using a 9,500-instrument universe.

The workload rotated updates across:

```text
2Y
5Y
10Y
30Y
```

and exercised both selective and full-universe repricing.

### Strategy distribution

```text
FULL        15
SELECTIVE    5
```

### Measured worker latency

```text
samples      20
minimum      690.427 ms
p50         1162.119 ms
p95         1538.771 ms
p99         1701.939 ms
maximum     1701.939 ms
```

The measured path includes pricing and downstream persistence rather than only the mathematical pricing function.

The workload ranged from:

```text
6,566 selectively repriced instruments
```

to:

```text
9,500 fully repriced instruments
```

per event.

---

## Pricing Correctness

Mercator validates several layers of pricing behavior independently.

The C++ test suite covers:

```text
evaluated pricing
yield curves
dependency graphs
data quality
clean-price calculations
quote reconciliation
curve-event pipelines
adaptive repricing
```

Current CTest targets:

```text
mercator-pricing-tests
mercator-yield-curve-tests
mercator-dependency-graph-tests
mercator-data-quality-tests
mercator-clean-price-tests
mercator-quote-reconciliation-tests
mercator-curve-event-pipeline-tests
mercator-adaptive-repricing-tests
```

All eight pricing-engine test suites are expected to pass before changes are merged.

---

## Continuous Integration

The repository includes a GitHub Actions workflow for the C++ pricing engine:

```text
.github/workflows/pricing-engine-ci.yml
```

CI builds the pricing engine and executes its automated tests to catch pricing, dependency, event-processing, and adaptive-repricing regressions.

---

## Reference Data

The reference-data service manages the instrument universe and associated metadata.

The hosted dataset contains:

```text
9,500 corporate bonds
520 fixed-income ETFs
10,020 total instruments
26,000 ETF constituent records
19,980 curve dependencies
```

Reference data includes fields such as:

```text
instrument_id
instrument_type
issuer_name
CUSIP
ISIN
ticker
rating
sector
```

Example:

```json
{
  "instrument_id": 1,
  "instrument_type": "CORPORATE_BOND",
  "issuer_name": "Northstar Energy",
  "cusip": "000000001",
  "isin": "US0000000001",
  "ticker": null,
  "rating": "A+",
  "sector": "Industrials"
}
```

Reference data is stored using versioned records so historical state can be reconstructed rather than overwriting previous values.

---

## Fixed-Income ETF Analytics

Mercator models fixed-income ETFs separately from individual bonds.

Each ETF can contain:

- fund metadata
- benchmark information
- NAV
- market quote
- basket constituents
- constituent weights
- creation-unit quantities
- cash components
- accrued interest
- basket analytics

For example, ETF `9501` contains a 50-bond basket in the hosted reference dataset.

The agent can answer:

```text
Show the NAV discount, market quote, and basket analytics for ETF 9501.
```

and route directly to the ETF analytics path without invoking unrelated research or risk tools.

---

## Relative-Value Analytics

Mercator provides relative-value analysis across fixed-income instruments.

The system can compare securities using characteristics such as:

- yield
- G-spread
- duration
- price
- credit quality
- curve exposure

This provides a reusable analytical layer for identifying securities trading rich or cheap relative to comparable instruments.

---

## Portfolio Risk

Mercator includes portfolio-level fixed-income risk analytics.

### Risk decomposition

Break portfolio exposure into instrument and risk-factor contributions.

### Historical VaR

Estimate portfolio losses from historical market movements.

### Stress testing

Apply deterministic market shocks and measure resulting portfolio changes.

### Scenario analysis

Evaluate portfolios under configurable market scenarios.

### Hedge recommendations

Generate candidate hedges based on portfolio exposures and available instruments.

### Portfolio optimization

Optimize portfolio allocations under configurable constraints.

### Risk-budget optimization

Allocate positions according to desired risk contributions rather than only notional weights.

---

## Agent Runtime

Mercator includes an agent runtime for natural-language fixed-income research.

Example:

```text
Show the NAV discount, market quote, and basket analytics for ETF 9501.
```

The planner converts the question into an execution plan:

```python
{
    "provider": "deterministic",
    "intent": "etf_analytics",
    "issuer": None,
    "fast_path": True,
    "routing": {
        "research": False,
        "prices": True,
        "relative_value": False,
        "risk": False,
        "stress": False,
        "hedge": False,
        "etf_analytics": True,
    },
}
```

Instead of sending every question through every subsystem, the planner selectively invokes only the required tools.

Agent capabilities include:

```text
issuer resolution
security resolution
reference-data retrieval
price retrieval
research retrieval
relative-value analysis
risk analysis
stress analysis
hedge analysis
ETF analytics
brief composition
```

The deterministic provider also allows the system to operate without requiring a paid external LLM API.

---

## Research Pipeline

Mercator includes infrastructure for storing and retrieving fixed-income research.

The schema supports:

- research documents
- document spans
- SEC filings
- filing sections
- filing chunks
- issuer mappings
- credit signals
- hybrid research search

This allows research results to be connected to structured issuer and security data rather than treated as isolated text documents.

---

## Market Replay

Mercator supports deterministic replay of historical or simulated market events.

Replay infrastructure makes it possible to:

- reproduce market states
- inspect event ranges
- replay pricing changes
- test analytics against deterministic inputs
- debug behavior from historical sequences

Curve replay events use the same versioned event contract as live simulated curve updates.

The workstation exposes replay and stream controls through the Operations interface.

---

## Workstation

The frontend is intentionally designed as a minimal fixed-income research terminal rather than a conventional consumer dashboard.

The interface uses:

- a single monospace terminal font
- constrained typography
- minimal color
- no gradients
- no decorative shadows
- fixed workstation navigation
- dense data tables
- consistent panel geometry
- desktop-oriented layouts

Primary workspaces include:

```text
Overview
Market
History
Portfolio
Risk
Operations
Agent
```

---

## Technology

### Pricing Engine

```text
C++20
CMake
librdkafka
libcurl
libpq
```

### Backend

```text
Python
FastAPI
Pydantic
psycopg
httpx
```

### Data

```text
PostgreSQL
ClickHouse
Redis
```

### Streaming

```text
Apache Kafka
Redis Pub/Sub
WebSockets
```

### Frontend

```text
HTML
CSS
JavaScript
```

### Infrastructure

```text
Docker
Docker Compose
GitHub Actions
Render
Neon
```

---

## Repository Structure

```text
mercator/
├── services/
│   ├── agent-runtime/
│   │   └── mercator_agent/
│   │       ├── llm/
│   │       ├── nodes/
│   │       ├── state/
│   │       └── tools/
│   │
│   ├── analytics/
│   │
│   ├── market-api/
│   │   └── app/
│   │       ├── static/
│   │       │   ├── css/
│   │       │   ├── js/
│   │       │   └── workbench.html
│   │       └── ...
│   │
│   ├── pricing-engine/
│   │   ├── benchmarks/
│   │   ├── include/
│   │   │   └── mercator/
│   │   │       └── pricing/
│   │   ├── src/
│   │   ├── tests/
│   │   └── validation/
│   │
│   ├── reference-data/
│   │   ├── app/
│   │   ├── migrations/
│   │   └── scripts/
│   │
│   ├── research-search/
│   ├── rfq-api/
│   ├── rfq-stream/
│   │
│   └── streaming-pricer/
│       ├── app/
│       ├── legacy/
│       ├── scripts/
│       └── tests/
│
├── scripts/
│   ├── benchmarks/
│   ├── dev/
│   └── tests/
│
├── .github/
│   └── workflows/
│       └── pricing-engine-ci.yml
│
├── docker-compose.yml
├── requirements.txt
└── render.yaml
```

---

## Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/namtran1812/mercator.git
cd mercator
```

### 2. Create a Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
```

The local infrastructure expects configuration for PostgreSQL, ClickHouse, Kafka, and Redis.

Do not commit `.env`.

### 5. Start infrastructure

```bash
docker compose up -d
```

This starts:

```text
PostgreSQL
ClickHouse
Kafka
Redis
```

Check:

```bash
docker compose ps
```

---

## Building the C++ Pricing Engine

Configure the build:

```bash
cmake \
  -S services/pricing-engine \
  -B build/pricing-engine
```

Build:

```bash
cmake \
  --build build/pricing-engine \
  -j
```

Run the test suite:

```bash
ctest \
  --test-dir build/pricing-engine \
  --output-on-failure
```

---

## Running the Pricing Worker

Example local configuration:

```bash
export KAFKA_BOOTSTRAP_SERVERS='localhost:9092'

export CLICKHOUSE_URL='http://127.0.0.1:8123'
export CLICKHOUSE_DATABASE='mercator'
export CLICKHOUSE_USERNAME='mercator'
export CLICKHOUSE_PASSWORD='mercator'

export REDIS_URL='redis://127.0.0.1:6380/0'

export INITIAL_CURVE_VERSION='2'
export PRICING_ERROR_BUDGET_BPS='0.25'
export FULL_REPRICE_FRACTION='0.70'
```

Start the worker:

```bash
./build/pricing-engine/mercator-pricing-worker
```

Example output:

```text
Mercator C++ pricing worker started
topic=market.curves.v1
brokers=localhost:9092
instruments=9500
curve_version=2
full_reprice_fraction=0.7
```

Processed events report their selected strategy:

```text
event=<event-id>
version=<version>
strategy=SELECTIVE
affected=6566/9500
repriced=6566
latency_ms=<latency>
```

---

## Streaming Gateway

Start the FastAPI streaming gateway:

```bash
cd services/streaming-pricer

export REDIS_URL='redis://127.0.0.1:6380/0'

uvicorn \
  app.main:app \
  --host 127.0.0.1 \
  --port 8006
```

Health endpoint:

```bash
curl http://127.0.0.1:8006/health
```

WebSocket:

```text
ws://127.0.0.1:8006/ws/prices
```

---

## Reference Data Setup

Apply the SQL migrations under:

```text
services/reference-data/migrations/
```

Generate the synthetic instrument universe:

```bash
python \
  services/reference-data/scripts/generate_instruments.py
```

Generate curve dependencies:

```bash
python \
  services/reference-data/scripts/generate_curve_dependencies.py
```

Generate fixed-income ETFs:

```bash
python \
  services/reference-data/scripts/generate_fixed_income_etfs.py
```

Backfill ETF metadata and baskets:

```bash
python \
  services/reference-data/scripts/backfill_fixed_income_etfs.py
```

---

## API Examples

### Health

```bash
curl http://127.0.0.1:8005/health
```

Response:

```json
{
  "status": "ok"
}
```

### Latest prices

```bash
curl \
  'http://127.0.0.1:8005/prices/latest?limit=3'
```

### Search instruments

```bash
curl \
  'http://127.0.0.1:8005/instruments/search?q=Northstar&limit=3'
```

### Market summary

```bash
curl \
  http://127.0.0.1:8005/market/summary
```

### Agent query

```bash
curl \
  -X POST \
  http://127.0.0.1:8005/agent/query \
  -H 'Content-Type: application/json' \
  -d '{
    "question":
      "Show the NAV discount, market quote, and basket analytics for ETF 9501."
  }'
```

---

## Public API Examples

Set:

```bash
export MERCATOR_URL='https://mercator-khgs.onrender.com'
```

Health:

```bash
curl "$MERCATOR_URL/health"
```

Reference data:

```bash
curl \
  "$MERCATOR_URL/instruments/search?q=Northstar&limit=3"
```

Agent:

```bash
curl \
  -X POST \
  "$MERCATOR_URL/agent/query" \
  -H 'Content-Type: application/json' \
  -d '{
    "question":
      "Show the NAV discount, market quote, and basket analytics for ETF 9501."
  }'
```

---

## Deployment

The public Mercator demo is deployed using:

```text
Render        application hosting
Neon          PostgreSQL
```

The production Market API acts as a gateway to the internal Reference Data and Agent Runtime services.

Secrets such as:

```text
POSTGRES_DSN
```

are supplied through deployment environment variables and are never stored in the repository.

### Demo mode

The public instance runs with:

```text
MERCATOR_DEMO_MODE=true
```

Demo mode replaces infrastructure that would otherwise require continuously running ClickHouse, Kafka, and Redis services with deterministic data while preserving the application workflows.

The complete event-driven architecture remains available locally for development, testing, replay, and benchmarking.

---

## Design Goals

Mercator was built around several engineering principles.

**Determinism.** Pricing, replay, and demo workflows should be reproducible.

**Event correctness.** Market updates should be processed in version order, with duplicates, stale events, and gaps explicitly handled.

**Failure safety.** Kafka progress should not advance before downstream pricing results are durably accepted.

**Idempotency.** Event redelivery should not create duplicate logical pricing observations.

**Selective computation.** Reprice only the instruments materially affected by a market update when doing so is cheaper than full recomputation.

**Service boundaries.** Reference data, pricing, analytics, research, and agent execution remain separate concerns.

**Historical correctness.** Reference data and evaluated prices preserve historical state rather than destructively replacing it.

**Low-latency state.** Historical analytics and latest-price retrieval use storage systems suited to their respective workloads.

**Observability.** Processing strategy, affected instrument counts, repricing counts, versions, and latency remain inspectable.

**Deployment portability.** The application can run against the full local infrastructure or a lightweight public-demo configuration.

---

## Example Pricing Workflow

```text
Curve movement
      │
      ▼
Kafka curve event
      │
      ▼
C++ Pricing Worker
      │
      ├── Validate event version
      │
      ├── Update curve state
      │
      ├── Resolve dependency fanout
      │
      ├── Select SKIP / SELECTIVE / FULL
      │
      └── Calculate evaluated prices
               │
          ┌────┴────┐
          ▼         ▼
     ClickHouse    Redis
     historical    latest
       prices      prices
          │          │
          │          ▼
          │      Pub/Sub
          │          │
          │          ▼
          │      WebSocket
          │          │
          └────┬─────┘
               ▼
        Mercator Workstation
```

---

## Example Research Workflow

```text
User
 │
 │ "Analyze ETF 9501"
 ▼
Agent Planner
 │
 ├── Resolve security
 │
 ├── Retrieve market price
 │
 └── Run ETF analytics
         │
         ▼
Reference Data
 │
 ├── ETF metadata
 └── 50 bond constituents
         │
         ▼
ETF Analytics
 │
 ├── NAV
 ├── market quote
 ├── premium / discount
 └── basket statistics
         │
         ▼
Agent Response
```

The planner avoids unnecessary research, stress, hedge, or portfolio computations when they are not required.

