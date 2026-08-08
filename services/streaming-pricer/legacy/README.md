# Legacy Python Streaming Pricer

This directory contains the original Python selective streaming-pricing prototype.

It is retained for historical reference only.

The authoritative live pricing path is now:

Kafka curve events
→ C++ pricing worker
→ ClickHouse evaluated prices
→ Redis latest-price cache / pub-sub
→ FastAPI WebSocket gateway

Do not run `legacy/consumer.py` in production or local integration tests.
