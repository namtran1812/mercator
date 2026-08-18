from __future__ import annotations

from mercator_agent.state.models import (
    AgentState,
    ClientBrief,
)


def compose_brief_node(
    state: AgentState,
) -> AgentState:
    request = state["request"]

    issuer = state.get(
        "issuer"
    )

    security = state.get(
        "security"
    )

    etf_analytics = state.get(
        "etf_analytics"
    )

    evidence = state.get(
        "evidence",
        [],
    )

    prices = state.get(
        "prices",
        [],
    )

    relative_value = state.get(
        "relative_value",
        [],
    )

    price_attribution = state.get(
        "price_attribution",
        [],
    )

    quality = state.get(
        "quality"
    )

    #
    # Prefer SEC issuer resolution when available.
    #
    # For synthetic/security-master-only issuers,
    # fall back to the security resolution result.
    #
    issuer_name = None

    if issuer is not None:
        issuer_name = (
            issuer.issuer_name
        )

    elif (
        security is not None
        and security.issuer_name
    ):
        issuer_name = (
            security.issuer_name
        )

    elif request.issuer:
        issuer_name = (
            request.issuer
        )

    elif etf_analytics is not None:
        issuer_name = (
            etf_analytics.fund_name
        )

    else:
        issuer_name = (
            "Unknown issuer"
        )

    market_observations: list[str] = []

    if quality is not None:
        if quality.status == "DEGRADED":
            market_observations.append(
                (
                    "Data quality is DEGRADED "
                    f"(score {quality.score:.2f}). "
                    "Analytics remain available but "
                    "should be interpreted with reduced "
                    "confidence."
                )
            )

        elif quality.status == "BLOCKED":
            market_observations.append(
                (
                    "Data quality is BLOCKED "
                    f"(score {quality.score:.2f}). "
                    "Mercator suppressed directional "
                    "analytics that depend on the "
                    "affected market observations."
                )
            )

    #
    # Attribution text is produced by deterministic
    # analytics, not generated causal speculation.
    #
    for item in price_attribution[:5]:
        market_observations.append(
            item.explanation
        )

    if etf_analytics is not None:
        coverage_percent = (
            etf_analytics.priced_weight
            * 100.0
        )

        market_observations.append(
            (
                f"{etf_analytics.fund_name} has "
                f"reference NAV "
                f"{etf_analytics.reference_nav:.4f}"
                if etf_analytics.reference_nav
                is not None
                else (
                    f"{etf_analytics.fund_name} "
                    "has no reference NAV."
                )
            )
        )

        if etf_analytics.mid is not None:
            market_observations.append(
                (
                    f"ETF mid is "
                    f"{etf_analytics.mid:.4f}"
                    + (
                        f", with premium/discount "
                        f"{etf_analytics.premium_discount_percent:+.3f}%."
                        if etf_analytics.premium_discount_percent
                        is not None
                        else "."
                    )
                )
            )

        if (
            etf_analytics.bid is not None
            and etf_analytics.ask is not None
        ):
            market_observations.append(
                (
                    f"Bid/ask is "
                    f"{etf_analytics.bid:.4f} / "
                    f"{etf_analytics.ask:.4f}"
                    + (
                        f" "
                        f"({etf_analytics.bid_ask_spread_bps:.2f} bp)."
                        if etf_analytics.bid_ask_spread_bps
                        is not None
                        else "."
                    )
                )
            )

        market_observations.append(
            (
                f"Basket pricing coverage is "
                f"{coverage_percent:.2f}% "
                f"({etf_analytics.priced_constituent_count}/"
                f"{etf_analytics.constituent_count} constituents)."
            )
        )

        market_observations.append(
            (
                f"Weighted basket yield is "
                f"{etf_analytics.weighted_yield_to_maturity * 100:.2f}%, "
                f"G-spread "
                f"{etf_analytics.weighted_g_spread_bps:.1f} bp, "
                f"and modified duration "
                f"{etf_analytics.weighted_modified_duration:.2f}."
            )
        )

    #
    # Summarize strongest relative-value signals.
    #
    for item in relative_value[:5]:
        benchmark = (
            item.peer_median_spread_bps
            if item.peer_median_spread_bps
            is not None
            else item.peer_average_spread_bps
        )

        z_text = (
            f", z-score {item.spread_z_score:+.2f}"
            if item.spread_z_score
            is not None
            else ""
        )

        market_observations.append(
            (
                f"Instrument {item.instrument_id} "
                f"trades at {item.spread_bps:.1f} bp "
                f"versus a {benchmark:.1f} bp peer "
                f"benchmark ({item.spread_difference_bps:+.1f} bp"
                f"{z_text}) across {item.peer_count} peers; "
                f"Mercator classifies it "
                f"{item.classification.lower()} "
                f"with {item.confidence.lower()} confidence."
            )
        )

    #
    # Fall back to general pricing observations when
    # relative-value analysis was not requested.
    #
    if (
        not market_observations
        and prices
    ):
        for item in prices[:5]:
            market_observations.append(
                (
                    f"Instrument {item.instrument_id}: "
                    f"price {item.clean_price:.2f}, "
                    f"yield "
                    f"{item.yield_to_maturity * 100:.2f}%, "
                    f"G-spread {item.g_spread_bps:.1f} bp, "
                    f"duration {item.modified_duration:.2f}."
                )
            )

    evidence_summary: list[str] = []

    citations: list[str] = []

    for item in evidence[:5]:
        evidence_summary.append(
            item.text
        )

        citations.append(
            item.citation_label
        )

    #
    # Research is optional.
    #
    # A security-master / market-data answer should still
    # be usable even when no SEC research exists.
    #
    if not evidence_summary:
        evidence_summary.append(
            (
                "No issuer research evidence was available "
                "for this request; the analysis is based on "
                "Mercator market and security-master data."
            )
        )

    risks: list[str] = []

    if quality is not None:
        for issue in quality.issues[:5]:
            risks.append(
                (
                    "Data quality "
                    f"{issue.severity.lower()}: "
                    f"{issue.message}"
                )
            )

    plan = state.get(
        "plan"
    )

    risk = state.get(
        "risk"
    )

    if risk is not None:
        risks.append(
            (
                f"Portfolio DV01 is "
                f"{risk.total_dv01:,.2f} and "
                f"CS01 is {risk.total_cs01:,.2f} "
                f"for {risk.instrument_count} instruments "
                "at the configured notional."
            )
        )

        if risk.portfolio_key_rate_dv01:
            largest_key_rate = max(
                risk.portfolio_key_rate_dv01,
                key=lambda item:
                    abs(
                        item.key_rate_dv01
                    ),
            )

            risks.append(
                (
                    f"The largest key-rate exposure is "
                    f"{largest_key_rate.tenor} with "
                    f"DV01 "
                    f"{largest_key_rate.key_rate_dv01:,.2f}."
                )
            )

    elif (
        plan is not None
        and plan.needs_risk
    ):
        risks.append(
            "Risk analytics were requested but unavailable."
        )

    hedge = state.get(
        "hedge"
    )

    if hedge is not None:
        for treasury in hedge.treasury_hedges[:3]:
            risks.append(
                (
                    f"Hedge recommendation: "
                    f"{treasury.tenor} Treasury "
                    f"notional "
                    f"{treasury.recommended_notional:,.0f} "
                    f"to offset key-rate DV01 "
                    f"{treasury.portfolio_key_rate_dv01:,.2f}."
                )
            )

        if hedge.credit_hedge is not None:
            credit = hedge.credit_hedge

            risks.append(
                (
                    f"Credit hedge recommendation: "
                    f"{credit.hedge_instrument} "
                    f"notional "
                    f"{credit.recommended_notional:,.0f} "
                    f"for portfolio CS01 "
                    f"{credit.portfolio_cs01:,.2f}."
                )
            )

        risks.append(
            (
                f"Residual risk after the recommended hedge "
                f"is DV01 {hedge.residual_dv01:,.2f} "
                f"and CS01 {hedge.residual_cs01:,.2f}."
            )
        )

    stress = state.get(
        "stress"
    )

    if stress is not None:
        pnl_percent = (
            stress.total_pnl
            / stress.total_market_value
            * 100.0
            if stress.total_market_value
            else 0.0
        )

        risks.append(
            (
                f"Stress-test P&L is "
                f"{stress.total_pnl:,.2f} "
                f"({pnl_percent:.2f}% of market value), "
                f"including Treasury P&L "
                f"{stress.total_treasury_pnl:,.2f} "
                f"and credit P&L "
                f"{stress.total_credit_pnl:,.2f}."
            )
        )

        if stress.instruments:
            worst = min(
                stress.instruments,
                key=lambda item:
                    item.total_pnl,
            )

            worst_percent = (
                worst.total_pnl
                / worst.market_value
                * 100.0
                if worst.market_value
                else 0.0
            )

            risks.append(
                (
                    f"Instrument {worst.instrument_id} "
                    f"has the largest stressed loss at "
                    f"{worst.total_pnl:,.2f} "
                    f"({worst_percent:.2f}% "
                    "of its market value)."
                )
            )

    #
    # Basic market-data-derived risk observations.
    #
    if (
        prices
        and etf_analytics is None
    ):
        longest = max(
            prices,
            key=lambda item:
                item.modified_duration,
        )

        widest = max(
            prices,
            key=lambda item:
                item.g_spread_bps,
        )

        risks.append(
            (
                f"Instrument {longest.instrument_id} "
                f"has the highest modified duration "
                f"among the retrieved securities "
                f"({longest.modified_duration:.2f}), "
                "indicating greater rate sensitivity."
            )
        )

        risks.append(
            (
                f"Instrument {widest.instrument_id} "
                f"has the widest G-spread "
                f"({widest.g_spread_bps:.1f} bp), "
                "which may indicate greater credit "
                "or liquidity compensation."
            )
        )

    if etf_analytics is not None:
        premium_text = (
            f"{etf_analytics.premium_discount_percent:+.3f}%"
            if etf_analytics.premium_discount_percent
            is not None
            else "unavailable"
        )

        summary = (
            f"{etf_analytics.fund_name} has "
            f"{etf_analytics.priced_weight * 100:.2f}% "
            f"basket pricing coverage and trades at "
            f"a premium/discount of {premium_text}. "
            f"Weighted duration is "
            f"{etf_analytics.weighted_modified_duration:.2f} "
            f"with G-spread "
            f"{etf_analytics.weighted_g_spread_bps:.1f} bp."
        )

    elif price_attribution:
        matched = sum(
            1
            for item in price_attribution
            if item.rate_change_bps
            is not None
        )

        summary = (
            f"Mercator produced deterministic "
            f"price-move attribution for "
            f"{len(price_attribution)} "
            f"instrument"
            f"{'s' if len(price_attribution) != 1 else ''}. "
            f"{matched} attribution"
            f"{'s' if matched != 1 else ''} "
            f"matched stored curve-event provenance."
        )

    elif relative_value:
        widest_rv = max(
            relative_value,
            key=lambda item:
                item.spread_difference_bps,
        )

        summary = (
            f"Mercator identified "
            f"{len(relative_value)} priced securities "
            f"for {issuer_name}. "
            f"Instrument {widest_rv.instrument_id} "
            f"shows the strongest positive relative-value "
            f"signal at "
            f"{widest_rv.spread_difference_bps:+.1f} bp "
            f"versus its peer benchmark and is classified "
            f"{widest_rv.classification.lower()}."
        )

    elif prices:
        summary = (
            f"Mercator retrieved current pricing for "
            f"{len(prices)} securities associated with "
            f"{issuer_name}."
        )

    else:
        summary = (
            f"Mercator could not retrieve current market "
            f"observations for {issuer_name}."
        )

    if (
        quality is not None
        and quality.status == "DEGRADED"
    ):
        summary = (
            "Data quality is degraded; "
            + summary
        )

    elif (
        quality is not None
        and quality.status == "BLOCKED"
    ):
        summary = (
            "Data quality blocked sensitive "
            "analytics; "
            + summary
        )

    brief = ClientBrief(
        issuer_name=issuer_name,

        question=
            request.question,

        summary=
            summary,

        market_observations=
            market_observations,

        evidence_summary=
            evidence_summary,

        risks=
            risks,

        citations=
            citations,
    )

    return {
        "brief": brief,

        "diagnostics": {
            **state.get(
                "diagnostics",
                {},
            ),

            "brief": {
                "status":
                    "completed",

                "issuer":
                    issuer_name,

                "market_observations":
                    len(
                        market_observations
                    ),

                "evidence_items":
                    len(
                        evidence
                    ),

                "risk_items":
                    len(
                        risks
                    ),
            },
        },
    }
