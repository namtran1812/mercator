from __future__ import annotations

import time

from fastapi import Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

HTTP_REQUESTS = Counter(
    "mercator_rfq_http_requests_total",
    "Total RFQ API HTTP requests",
    ["method", "path", "status"],
)

HTTP_LATENCY = Histogram(
    "mercator_rfq_http_request_duration_seconds",
    "RFQ API request latency",
    ["method", "path"],
)

RFQS_CREATED = Counter(
    "mercator_rfqs_created_total",
    "Total RFQs created",
    ["side"],
)

TRADES_EXECUTED = Counter(
    "mercator_trades_executed_total",
    "Total trades executed",
    ["side", "dealer"],
)


async def metrics_middleware(
    request: Request,
    call_next,
):
    started = time.perf_counter()

    response = await call_next(request)

    elapsed = (
        time.perf_counter() - started
    )

    path = request.url.path

    HTTP_REQUESTS.labels(
        method=request.method,
        path=path,
        status=response.status_code,
    ).inc()

    HTTP_LATENCY.labels(
        method=request.method,
        path=path,
    ).observe(elapsed)

    return response


def metrics_response() -> Response:
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
