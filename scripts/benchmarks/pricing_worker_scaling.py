from __future__ import annotations

import argparse
import json
import time
import uuid

from confluent_kafka import Producer


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--start-version",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--events",
        type=int,
        default=20,
    )

    args = parser.parse_args()

    producer = Producer({
        "bootstrap.servers":
            "localhost:9092",
    })

    tenors = [
        (4, 2.0),
        (6, 5.0),
        (8, 10.0),
        (9, 30.0),
    ]

    rates = {
        2.0: 0.0400,
        5.0: 0.0430,
        10.0: 0.0460,
        30.0: 0.0495,
    }

    version = args.start_version

    for index in range(args.events):
        node_id, maturity = (
            tenors[index % len(tenors)]
        )

        old_rate = rates[maturity]

        direction = (
            1.0
            if index % 2 == 0
            else -1.0
        )

        new_rate = (
            old_rate
            + direction * 0.0001
        )

        next_version = version + 1

        event = {
            "event_id":
                str(uuid.uuid4()),

            "event_time":
                time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ",
                    time.gmtime(),
                ),

            "previous_version":
                version,

            "new_version":
                next_version,

            "updates": [
                {
                    "node_id":
                        node_id,

                    "maturity_years":
                        maturity,

                    "old_rate":
                        old_rate,

                    "new_rate":
                        new_rate,
                }
            ],
        }

        producer.produce(
            "market.curves.v1",
            key=f"{maturity}Y",
            value=json.dumps(event),
        )

        producer.flush()

        print(
            f"published "
            f"v{next_version} "
            f"{maturity}Y"
        )

        rates[maturity] = new_rate
        version = next_version

        time.sleep(0.2)


if __name__ == "__main__":
    main()
