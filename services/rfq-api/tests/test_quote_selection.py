from __future__ import annotations


def best_quote(
    side: str,
    quotes: list[dict[str, float]],
) -> dict[str, float]:
    if side == "BUY":
        return min(
            quotes,
            key=lambda quote: quote["price"],
        )

    return max(
        quotes,
        key=lambda quote: quote["price"],
    )


def test_buy_selects_lowest_price() -> None:
    quotes = [
        {"price": 100.12},
        {"price": 100.08},
        {"price": 100.15},
    ]

    assert (
        best_quote("BUY", quotes)["price"]
        == 100.08
    )


def test_sell_selects_highest_price() -> None:
    quotes = [
        {"price": 99.88},
        {"price": 99.93},
        {"price": 99.90},
    ]

    assert (
        best_quote("SELL", quotes)["price"]
        == 99.93
    )
