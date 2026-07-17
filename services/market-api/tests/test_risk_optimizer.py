from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.models import (
    LatestBondPrice,
    RiskBudgetOptimizationRequest,
)
from app.risk_optimizer import (
    optimize_with_risk_budget,
)


def make_price(
    instrument_id: int,
    duration: float,
    spread: float,
    yield_to_maturity: float,
) -> LatestBondPrice:
    return LatestBondPrice(
        instrument_id=instrument_id,
        clean_price=100.0,
        dirty_price=101.0,
        yield_to_maturity=yield_to_maturity,
        g_spread_bps=spread,
        modified_duration=duration,
        convexity=30.0,
        quality_score=0.95,
        quality_status="VALID",
        curve_version=2,
        reference_version=1,
        event_time=datetime.now(
            timezone.utc
        ),
    )


def prices() -> list[LatestBondPrice]:
    return [
        make_price(1, 3.0, 100.0, 0.04),
        make_price(2, 5.0, 150.0, 0.05),
        make_price(3, 7.0, 200.0, 0.06),
        make_price(4, 10.0, 250.0, 0.07),
        make_price(5, 12.0, 300.0, 0.08),
    ]


def test_optimizer_respects_position_cap() -> None:
    response = optimize_with_risk_budget(
        prices=prices(),
        request=RiskBudgetOptimizationRequest(
            instrument_ids=[1, 2, 3, 4, 5],
            total_notional=10_000_000.0,
            max_position_percent=0.20,
            max_portfolio_dv01=1_000_000.0,
            max_portfolio_cs01=1_000_000.0,
        ),
    )

    assert all(
        allocation.weight <= 0.20 + 1e-12
        for allocation in response.allocations
    )


def test_optimizer_respects_risk_limits() -> None:
    response = optimize_with_risk_budget(
        prices=prices(),
        request=RiskBudgetOptimizationRequest(
            instrument_ids=[1, 2, 3, 4, 5],
            total_notional=10_000_000.0,
            max_position_percent=0.50,
            max_portfolio_dv01=20_000.0,
            max_portfolio_cs01=20_000.0,
        ),
    )

    assert response.portfolio_dv01 <= (
        20_000.0 + 1e-6
    )

    assert response.portfolio_cs01 <= (
        20_000.0 + 1e-6
    )


def test_tight_budget_leaves_cash() -> None:
    response = optimize_with_risk_budget(
        prices=prices(),
        request=RiskBudgetOptimizationRequest(
            instrument_ids=[1, 2, 3, 4, 5],
            total_notional=10_000_000.0,
            max_position_percent=1.0,
            max_portfolio_dv01=1_000.0,
            max_portfolio_cs01=1_000.0,
        ),
    )

    assert response.cash_notional > 0.0
    assert response.invested_percent < 1.0


def test_accounting_identity() -> None:
    response = optimize_with_risk_budget(
        prices=prices(),
        request=RiskBudgetOptimizationRequest(
            instrument_ids=[1, 2, 3, 4, 5],
            total_notional=10_000_000.0,
            max_position_percent=0.40,
            max_portfolio_dv01=100_000.0,
            max_portfolio_cs01=100_000.0,
        ),
    )

    assert (
        response.invested_notional
        + response.cash_notional
    ) == pytest.approx(
        response.requested_notional
    )

    assert sum(
        allocation.target_notional
        for allocation in response.allocations
    ) == pytest.approx(
        response.invested_notional
    )
