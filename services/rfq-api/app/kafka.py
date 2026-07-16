from __future__ import annotations

import json
import os
from typing import Any

from confluent_kafka import Producer

RFQ_REQUESTED_TOPIC = "market.rfq.requested"
TRADE_EXECUTED_TOPIC = "market.trade.executed"


class KafkaPublisher:
    def __init__(self) -> None:
        self._producer = Producer(
            {
                "bootstrap.servers": os.getenv(
                    "KAFKA_BOOTSTRAP_SERVERS",
                    "localhost:9092",
                ),
                "client.id": "mercator-rfq-api",
            }
        )

    def publish(
        self,
        *,
        topic: str,
        key: str,
        payload: dict[str, Any],
    ) -> None:
        self._producer.produce(
            topic,
            key=key,
            value=json.dumps(
                payload,
                default=str,
            ),
        )

        self._producer.flush(5)
