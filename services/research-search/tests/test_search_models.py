from __future__ import annotations

from app.models import SearchRequest


def test_search_request_defaults() -> None:
    request = SearchRequest(
        query="liquidity and debt"
    )

    assert request.limit == 10
    assert request.cik is None
    assert request.forms is None


def test_search_request_filters() -> None:
    request = SearchRequest(
        query="interest rate risk",
        cik="320193",
        forms=["10-K"],
        limit=5,
    )

    assert request.cik == "320193"
    assert request.forms == ["10-K"]
    assert request.limit == 5
