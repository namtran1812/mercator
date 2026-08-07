#!/usr/bin/env bash

set -e

PORT="${PORT:-10000}"

export MERCATOR_DEMO_MODE="${MERCATOR_DEMO_MODE:-true}"
export REFERENCE_DATA_URL="http://127.0.0.1:8001"
export AGENT_RUNTIME_URL="http://127.0.0.1:8006"
export MARKET_API_URL="http://127.0.0.1:${PORT}"

PYTHONPATH=services/reference-data \
uvicorn app.main:app \
  --host 127.0.0.1 \
  --port 8001 &

REFERENCE_PID=$!

PYTHONPATH=services/agent-runtime \
uvicorn mercator_agent.main:app \
  --host 127.0.0.1 \
  --port 8006 &

AGENT_PID=$!

cleanup() {
  kill \
    "$REFERENCE_PID" \
    "$AGENT_PID" \
    2>/dev/null \
    || true
}

trap cleanup EXIT INT TERM

PYTHONPATH=services/market-api \
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "$PORT"
