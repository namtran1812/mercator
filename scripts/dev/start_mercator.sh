#!/usr/bin/env bash

set -e

cd "$(dirname "$0")/../.."

source .venv/bin/activate

set -a
source .env
set +a

echo "Starting infrastructure..."
docker compose up -d

echo "Waiting for infrastructure..."
sleep 4

mkdir -p artifacts/logs

start_service() {
    name="$1"
    port="$2"
    command="$3"

    if lsof -tiTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
        echo "✓ $name already running on $port"
        return
    fi

    echo "Starting $name on $port..."

    nohup bash -c "$command" \
        > "artifacts/logs/${name}.log" \
        2>&1 &

    sleep 2

    if lsof -tiTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
        echo "✓ $name started"
    else
        echo "✗ $name failed"
        echo "  Check artifacts/logs/${name}.log"
    fi
}


start_service \
    "reference-data" \
    "8001" \
    "PYTHONPATH=services/reference-data uvicorn app.main:app --host 127.0.0.1 --port 8001"


start_service \
    "research-search" \
    "8003" \
    "python -m uvicorn app.main:app --app-dir services/research-search --host 127.0.0.1 --port 8003"


start_service \
    "market-api" \
    "8005" \
    "python -m uvicorn app.main:app --app-dir services/market-api --host 127.0.0.1 --port 8005"


start_service \
    "streaming-pricer" \
    "8006" \
    "REDIS_URL=redis://127.0.0.1:6380/0 python -m uvicorn app.main:app --app-dir services/streaming-pricer --host 127.0.0.1 --port 8006"


echo
echo "============================================================"
echo "MERCATOR"
echo "============================================================"

for port in 8001 8003 8005 8006 11434
do
    printf "Port %-5s " "$port"

    if lsof -tiTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
        echo "✓"
    else
        echo "✗"
    fi
done

echo
echo "Workbench:"
echo "http://127.0.0.1:8005/workbench"
