# Mercator

A production-style fixed-income research and analytics workstation for corporate bonds and fixed-income ETFs.

Mercator combines reference data, evaluated pricing, portfolio analytics, risk and stress testing, ETF basket analysis, historical replay, and an agent-based research interface behind a single web application.

**Live Demo:** https://mercator-khgs.onrender.com

> The public deployment runs in demo mode using deterministic market snapshots and Neon-backed reference data. The full local architecture supports PostgreSQL, ClickHouse, Kafka, and Redis.

---

## Overview

Mercator is designed around the infrastructure and workflows behind a fixed-income research platform rather than a standalone dashboard.

The system supports:

- 10,000+ corporate bonds and fixed-income ETFs
- versioned reference data
- evaluated bond prices and historical price observations
- yield, spread, duration, and convexity analytics
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
                         │ HTML / CSS / JS      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     Market API       │
                         │      FastAPI         │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
    ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
    │ Reference Data   │  │  Agent Runtime   │  │ Market Analytics │
    │     Service      │  │                  │  │                  │
    └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
             │                     │                     │
             ▼                     │                     ▼
    ┌──────────────────┐           │            ┌──────────────────┐
    │    PostgreSQL    │◄──────────┘            │    ClickHouse    │
    │ versioned data   │                        │ pricing/history  │
    └──────────────────┘                        └──────────────────┘

                Full local infrastructure
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        ┌───────────┐         ┌───────────┐
        │   Kafka   │         │   Redis   │
        └───────────┘         └───────────┘
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

## Core Services

### Market API

The Market API is the primary application gateway.

It exposes endpoints for:

- latest evaluated prices
- market summaries
- price history
- portfolio analytics
- relative-value analysis
- carry and roll
- risk decomposition
- historical VaR
- stress testing
- hedging
- portfolio optimization
- scenario analysis
- ETF analytics
- market replay and streaming
- reference-data lookup
- agent queries

It also serves the Mercator web workstation.

---

### Reference Data

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

The full local system stores evaluated-price history in ClickHouse for efficient analytical queries.

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

Supported workflows include:

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

The workstation exposes replay and stream controls directly through the Operations interface.

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
│   ├── reference-data/
│   │   ├── app/
│   │   ├── migrations/
│   │   └── scripts/
│   │
│   ├── research-search/
│   ├── rfq-api/
│   ├── rfq-stream/
│   └── streaming-pricer/
│
├── scripts/
│   ├── benchmarks/
│   └── dev/
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

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Create your local environment from the example:

```bash
cp .env.example .env
```

The local infrastructure expects configuration for PostgreSQL and ClickHouse.

Do not commit `.env`.

### 5. Start infrastructure

```bash
docker compose up -d
```

This starts the local infrastructure used by Mercator, including:

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
Neon         PostgreSQL
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

Demo mode replaces infrastructure that would otherwise require continuously running ClickHouse/Kafka services with deterministic data while preserving the application workflows.

The complete local architecture remains available for development and benchmarking.

---

## Design Goals

Mercator was built around several engineering principles.

**Determinism.** Pricing, replay, and demo workflows should be reproducible.

**Service boundaries.** Reference data, analytics, research, and agent execution remain separate concerns.

**Historical correctness.** Reference data uses versioned records rather than destructive updates.

**Selective computation.** Agent requests route only to the analytical components required by the query.

**Observability.** System state and execution behavior should be inspectable from the workstation.

**Deployment portability.** The same application can run against the full local infrastructure or a lightweight public-demo configuration.

---

## Example Workflow

A typical research workflow looks like:

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

---

## Status

Mercator currently includes working implementations of:

- [x] Versioned fixed-income reference data
- [x] Corporate-bond universe
- [x] Fixed-income ETF universe
- [x] ETF basket modeling
- [x] Evaluated pricing
- [x] Historical pricing
- [x] Market summary analytics
- [x] Relative-value analytics
- [x] Carry and roll
- [x] Portfolio risk
- [x] Risk decomposition
- [x] Historical VaR
- [x] Stress testing
- [x] Scenario analysis
- [x] Hedge recommendations
- [x] Portfolio optimization
- [x] Risk-budget optimization
- [x] Market replay
- [x] Agent planning and routing
- [x] ETF agent analytics
- [x] Research storage/search infrastructure
- [x] Terminal-style research workstation
- [x] Public deployment

---

## Disclaimer

Mercator is an engineering and research project built with synthetic and simulated market data.

It is not connected to a live trading venue, does not provide investment advice, and should not be used for production trading or investment decisions.
