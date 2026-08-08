from __future__ import annotations

import argparse
import json
import os
import time
import uuid
from datetime import datetime

import clickhouse_connect
from confluent_kafka import Producer

TOPIC = "market.curves.v1"


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--scenario-name",
        required=True,
    )

    parser.add_argument(
        "--speed",
        type=float,
        default=10.0,
        help=(
            "Replay speed multiplier. "
            "10 means ten times faster."
        ),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10_000,
    )

    arguments = parser.parse_args()

    if arguments.speed <= 0:
        raise ValueError(
            "Replay speed must be positive"
        )

    clickhouse = clickhouse_connect.get_client(
        host=os.getenv(
            "CLICKHOUSE_HOST",
            "localhost",
        ),
        port=int(
            os.getenv(
                "CLICKHOUSE_PORT",
                "8123",
            )
        ),
        username=os.getenv(
            "CLICKHOUSE_USERNAME",
            "mercator",
        ),
        password=os.getenv(
            "CLICKHOUSE_PASSWORD",
            "mercator",
        ),
        database=os.getenv(
            "CLICKHOUSE_DATABASE",
            "mercator",
        ),
    )

    producer = Producer(
        {
            "bootstrap.servers": os.getenv(
                "KAFKA_BOOTSTRAP_SERVERS",
                "localhost:9092",
            ),
            "client.id":
                "mercator-replay-producer",
        }
    )

    result = clickhouse.query(
        """
        SELECT
            event_time,
            curve_version,
            tenor,
            old_rate,
            new_rate
        FROM curve_events
        WHERE scenario_name =
            {scenario_name:String}
        ORDER BY
            event_time,
            curve_version
        LIMIT {limit:UInt32}
        """,
        parameters={
            "scenario_name":
                arguments.scenario_name,
            "limit": arguments.limit,
        },
    )

    rows = result.result_rows

    if not rows:
        raise RuntimeError(
            "No replay events were found"
        )

    print(
        f"Replaying {len(rows):,} events "
        f"at {arguments.speed:.1f}x speed"
    )

    previous_time: datetime | None = None

    for index, row in enumerate(
        rows,
        start=1,
    ):
        (
            event_time,
            curve_version,
            tenor,
            old_rate,
            new_rate,
        ) = row

        if previous_time is not None:
            original_delay = (
                event_time - previous_time
            ).total_seconds()

            replay_delay = max(
                0.0,
                original_delay / arguments.speed,
            )

            time.sleep(replay_delay)

        tenor_to_node = {
            "3M": (1, 0.25),
            "6M": (2, 0.50),
            "1Y": (3, 1.00),
            "2Y": (4, 2.00),
            "3Y": (5, 3.00),
            "5Y": (6, 5.00),
            "7Y": (7, 7.00),
            "10Y": (8, 10.00),
            "30Y": (9, 30.00),
        }

        node_id, maturity_years = (
            tenor_to_node[tenor]
        )

        new_version = int(curve_version)
        previous_version = new_version - 1

        replay_event = {
            "event_id": str(uuid.uuid4()),
            "event_time":
                datetime.now(
                    event_time.tzinfo
                ).isoformat(),
            "previous_version":
                previous_version,
            "new_version":
                new_version,
            "updates": [
                {
                    "node_id": node_id,
                    "maturity_years":
                        maturity_years,
                    "old_rate":
                        float(old_rate),
                    "new_rate":
                        float(new_rate),
                }
            ],
        }

        producer.produce(
            TOPIC,
            key=tenor,
            value=json.dumps(replay_event),
        )

        producer.poll(0)

        print(
            f"[{index}/{len(rows)}] "
            f"{tenor}: "
            f"{old_rate * 100:.4f}% -> "
            f"{new_rate * 100:.4f}%"
        )

        previous_time = event_time

    producer.flush(10)

    print("Replay complete.")


if __name__ == "__main__":
    main()
