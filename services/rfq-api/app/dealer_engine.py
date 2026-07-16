from __future__ import annotations

import json
import os
import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import clickhouse_connect
from confluent_kafka import Consumer, Producer

from .repository import RFQRepository

RFQ_REQUESTED_TOPIC = "market.rfq.requested"
RFQ_QUOTED_TOPIC = "market.rfq.quoted"


@dataclass(frozen=True)
class DealerProfile:
    name: str
    base_half_spread_bps: float
    inventory_bias_bps: float
    latency_min_ms: int
    latency_max_ms: int
    reliability: float


DEALERS = [
    DealerProfile(
        name="Northstar Markets",
        base_half_spread_bps=4.0,
        inventory_bias_bps=-1.0,
        latency_min_ms=80,
        latency_max_ms=180,
        reliability=0.99,
    ),
    DealerProfile(
        name="Atlas Credit",
        base_half_spread_bps=5.5,
        inventory_bias_bps=1.5,
        latency_min_ms=30,
        latency_max_ms=100,
        reliability=0.97,
    ),
    DealerProfile(
        name="Orion Fixed Income",
        base_half_spread_bps=7.0,
        inventory_bias_bps=0.0,
        latency_min_ms=10,
        latency_max_ms=60,
        reliability=0.94,
    ),
]


def latest_clean_price(
    client,
    instrument_id: int,
) -> float:
    result = client.query(
        """
        SELECT
            argMax(clean_price, event_time)
        FROM evaluated_prices
        WHERE instrument_id =
            {instrument_id:UInt64}
        """,
        parameters={
            "instrument_id": instrument_id,
        },
    )

    if not result.result_rows:
        raise LookupError(
            f"No price found for instrument {instrument_id}"
        )

    value = result.result_rows[0][0]

    if value is None:
        raise LookupError(
            f"No price found for instrument {instrument_id}"
        )

    return float(value)


def size_adjustment_bps(
    quantity: float,
) -> float:
    if quantity >= 10_000_000:
        return 5.0

    if quantity >= 5_000_000:
        return 3.0

    if quantity >= 1_000_000:
        return 1.0

    return 0.25


def calculate_quote(
    *,
    mid_price: float,
    side: str,
    quantity: float,
    dealer: DealerProfile,
    random_generator: random.Random,
) -> tuple[float, float, float]:
    size_adjustment = size_adjustment_bps(
        quantity
    )

    noise_bps = random_generator.gauss(
        0.0,
        0.75,
    )

    effective_half_spread_bps = max(
        0.5,
        dealer.base_half_spread_bps
        + size_adjustment
        + dealer.inventory_bias_bps
        + noise_bps,
    )

    price_adjustment = (
        mid_price
        * effective_half_spread_bps
        / 10_000.0
    )

    # Client BUY means dealer sells, so client pays offer.
    if side == "BUY":
        quote_price = (
            mid_price + price_adjustment
        )
    else:
        quote_price = (
            mid_price - price_adjustment
        )

    return (
        quote_price,
        effective_half_spread_bps,
        size_adjustment,
    )


def main() -> None:
    repository = RFQRepository()

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

    bootstrap_servers = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS",
        "localhost:9092",
    )

    consumer = Consumer(
        {
            "bootstrap.servers":
                bootstrap_servers,
            "group.id":
                "mercator-dealer-engine",
            "auto.offset.reset":
                "earliest",
            "enable.auto.commit": True,
        }
    )

    producer = Producer(
        {
            "bootstrap.servers":
                bootstrap_servers,
            "client.id":
                "mercator-dealer-engine",
        }
    )

    consumer.subscribe(
        [RFQ_REQUESTED_TOPIC]
    )

    random_generator = random.Random(42)

    print(
        f"Dealer engine listening on "
        f"{RFQ_REQUESTED_TOPIC}"
    )

    try:
        while True:
            message = consumer.poll(1.0)

            if message is None:
                continue

            if message.error():
                print(message.error())
                continue

            event = json.loads(
                message.value().decode("utf-8")
            )

            rfq_id = UUID(event["rfq_id"])
            instrument_id = int(
                event["instrument_id"]
            )
            side = str(event["side"])
            quantity = float(
                event["quantity"]
            )

            repository.update_rfq_status(
                rfq_id=rfq_id,
                status="QUOTING",
            )

            try:
                mid_price = latest_clean_price(
                    clickhouse,
                    instrument_id,
                )
            except Exception as error:
                print(
                    f"RFQ {rfq_id} failed: {error}"
                )
                continue

            for dealer in DEALERS:
                if (
                    random_generator.random()
                    > dealer.reliability
                ):
                    continue

                latency_ms = (
                    random_generator.randint(
                        dealer.latency_min_ms,
                        dealer.latency_max_ms,
                    )
                )

                time.sleep(
                    latency_ms / 1_000.0
                )

                (
                    quote_price,
                    quote_spread_bps,
                    size_adjustment,
                ) = calculate_quote(
                    mid_price=mid_price,
                    side=side,
                    quantity=quantity,
                    dealer=dealer,
                    random_generator=random_generator,
                )

                quoted_at = datetime.now(
                    timezone.utc
                )

                expires_at = (
                    quoted_at
                    + timedelta(seconds=30)
                )

                quote_id = uuid4()

                quote = (
                    repository.upsert_dealer_quote(
                        quote_id=quote_id,
                        rfq_id=rfq_id,
                        dealer=dealer.name,
                        price=quote_price,
                        spread_bps=(
                            quote_spread_bps
                        ),
                        latency_ms=latency_ms,
                        quoted_at=quoted_at,
                        expires_at=expires_at,
                        inventory_adjustment_bps=(
                            dealer.inventory_bias_bps
                        ),
                        size_adjustment_bps=(
                            size_adjustment
                        ),
                    )
                )

                payload = {
                    "event_type": "RFQ_QUOTED",
                    "quote_id": str(
                        quote["id"]
                    ),
                    "rfq_id": str(rfq_id),
                    "instrument_id":
                        instrument_id,
                    "side": side,
                    "quantity": quantity,
                    "dealer": dealer.name,
                    "price": quote_price,
                    "spread_bps":
                        quote_spread_bps,
                    "latency_ms":
                        latency_ms,
                    "quoted_at":
                        quoted_at.isoformat(),
                    "expires_at":
                        expires_at.isoformat(),
                }

                producer.produce(
                    RFQ_QUOTED_TOPIC,
                    key=str(rfq_id),
                    value=json.dumps(payload),
                )

                producer.poll(0)

                print(
                    f"{rfq_id} | "
                    f"{dealer.name} | "
                    f"{quote_price:.4f} | "
                    f"{latency_ms} ms"
                )

            producer.flush(5)

            repository.update_rfq_status(
                rfq_id=rfq_id,
                status="QUOTED",
            )

    finally:
        consumer.close()


if __name__ == "__main__":
    main()
