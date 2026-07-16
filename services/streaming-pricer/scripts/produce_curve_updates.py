from __future__ import annotations

import argparse
import json
import os
import random
import time
import uuid
from datetime import datetime, timezone

from confluent_kafka import Producer

TOPIC = "market.curves.v1"

TENORS = [
    "3M",
    "6M",
    "1Y",
    "2Y",
    "3Y",
    "5Y",
    "7Y",
    "10Y",
    "30Y",
]

BASE_RATES = {
    "3M": 0.0430,
    "6M": 0.0420,
    "1Y": 0.0410,
    "2Y": 0.0400,
    "3Y": 0.0410,
    "5Y": 0.0430,
    "7Y": 0.0450,
    "10Y": 0.0460,
    "30Y": 0.0470,
}


def delivery_report(error, message) -> None:
    if error is not None:
        print(f"Delivery failed: {error}")
        return

    print(
        f"Published partition={message.partition()} "
        f"offset={message.offset()}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
    )

    parser.add_argument(
        "--volatility-bps",
        type=float,
        default=2.0,
    )

    arguments = parser.parse_args()

    producer = Producer(
        {
            "bootstrap.servers": os.getenv(
                "KAFKA_BOOTSTRAP_SERVERS",
                "localhost:9092",
            ),
            "client.id": "mercator-curve-simulator",
        }
    )

    random.seed(42)

    rates = dict(BASE_RATES)
    curve_version = 2

    print(f"Publishing curve updates to {TOPIC}")

    while True:
        tenor = random.choice(TENORS)

        old_rate = rates[tenor]

        shock_bps = random.gauss(
            0.0,
            arguments.volatility_bps,
        )

        new_rate = max(
            -0.01,
            old_rate + shock_bps / 10_000.0,
        )

        curve_version += 1
        rates[tenor] = new_rate

        event = {
            "event_id": str(uuid.uuid4()),
            "event_time": datetime.now(
                timezone.utc
            ).isoformat(),
            "curve_version": curve_version,
            "tenor": tenor,
            "old_rate": old_rate,
            "new_rate": new_rate,
        }

        producer.produce(
            TOPIC,
            key=tenor,
            value=json.dumps(event),
            callback=delivery_report,
        )

        producer.poll(0)
        producer.flush(5)

        print(
            f"{tenor}: "
            f"{old_rate * 100:.4f}% → "
            f"{new_rate * 100:.4f}%"
        )

        time.sleep(arguments.interval)


if __name__ == "__main__":
    main()
