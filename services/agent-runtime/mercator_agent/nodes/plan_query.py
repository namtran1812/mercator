from __future__ import annotations

from mercator_agent.llm import (
    LLMClient,
)

from mercator_agent.state.models import (
    AgentPlan,
    AgentState,
)


SYSTEM_PROMPT = """
You are the planning layer for Mercator,
a fixed-income research and trading analytics system.

Your only task is to determine which Mercator
capabilities are required for the user's request.

Available capabilities:

research
- SEC filings
- indexed market research
- issuer fundamentals
- credit developments

prices
- clean price
- dirty price
- yield
- G-spread
- duration
- data-quality information

price_attribution
- explain observed bond price moves
- match price changes to curve events
- duration / convexity attribution
- residual price movement

relative_value
- peer comparisons
- cheap/rich analysis
- spread differences
- relative-value opportunities

risk
- DV01
- CS01
- key-rate exposure
- portfolio risk

stress
- rate shocks
- spread shocks
- scenario analysis
- stress testing

hedge
- Treasury hedge recommendations
- credit hedge recommendations

etf_analytics
- ETF NAV
- bid / ask / mid
- premium / discount
- basket coverage
- weighted yield
- weighted spread
- weighted duration

Rules:

1. If the user says cheap, rich, expensive,
relative value, peer comparison, mispriced,
or attractive, relative_value is required.

2. If the user asks about risk, exposure,
DV01, CS01, duration risk, or key-rate risk,
risk is required.

3. If the user asks for stress testing,
a shock, selloff, scenario, or "what if",
stress is required.

4. Stress analysis also requires risk.

5. If the user asks for a hedge, hedging,
or neutralization, hedge is required.

6. Hedge analysis also requires risk.

7. If the user mentions ETF, fund, NAV,
basket, premium, or discount,
etf_analytics is required.

8. Pricing, yield, spreads, relative value,
security comparison, and ETF analysis
generally require prices.

9. Research is useful for issuer fundamentals,
filings, catalysts, explanations, credit events,
and questions asking why.

10. If an issuer is clearly named,
extract it.

11. Never return the string "unknown"
for issuer. Use null instead.

Do not perform calculations yourself.
Return only structured JSON.
"""


def _contains_any(
    text: str,
    terms: tuple[str, ...],
) -> bool:
    return any(
        term in text
        for term in terms
    )


def _is_price_attribution_request(
    text: str,
) -> bool:
    """
    Identify explicit security price-move explanation
    requests without confusing them with issuer-credit
    or general research questions.
    """

    explanation_terms = (
        "why",
        "explain",
        "what drove",
        "what caused",
        "driver",
        "drivers",
    )

    movement_terms = (
        "move",
        "moved",
        "movement",
        "change",
        "changed",
        "rose",
        "fell",
        "rallied",
        "sold off",
        "selloff",
        "widen",
        "widened",
        "tighten",
        "tightened",
        "drove",
    )

    security_terms = (
        "instrument",
        "bond",
        "security",
        "price",
    )

    return (
        _contains_any(
            text,
            explanation_terms,
        )
        and _contains_any(
            text,
            movement_terms,
        )
        and _contains_any(
            text,
            security_terms,
        )
    )


def apply_guardrails(
    plan: AgentPlan,
    question: str,
) -> AgentPlan:
    """
    Enforce obvious deterministic routing rules.

    A small local model is useful for understanding
    intent, but basic domain rules should not depend
    entirely on model output.
    """

    text = question.lower()

    relative_value_terms = (
        "cheap",
        "rich",
        "expensive",
        "relative value",
        "relative-value",
        "mispriced",
        "peer",
        "peers",
        "attractive",
        "undervalued",
        "overvalued",
    )

    risk_terms = (
        "risk",
        "risky",
        "dv01",
        "cs01",
        "exposure",
        "duration risk",
        "key rate",
        "key-rate",
    )

    stress_terms = (
        "stress",
        "scenario",
        "shock",
        "selloff",
        "sell-off",
        "what if",
        "what happens if",
    )

    hedge_terms = (
        "hedge",
        "hedging",
        "neutralize",
        "neutralise",
        "offset risk",
    )

    etf_terms = (
        "etf",
        "fund",
        "nav",
        "basket",
        "premium",
        "discount",
    )

    research_terms = (
        "why",
        "filing",
        "filings",
        "fundamental",
        "fundamentals",
        "catalyst",
        "catalysts",
        "research",
        "credit event",
        "issuer risk",
        "explain",
    )

    pricing_terms = (
        "price",
        "pricing",
        "yield",
        "spread",
        "g-spread",
        "duration",
        "bond",
        "security",
        "instrument",
    )

    if _contains_any(
        text,
        relative_value_terms,
    ):
        plan.needs_relative_value = True
        plan.needs_prices = True

    if _contains_any(
        text,
        risk_terms,
    ):
        plan.needs_risk = True

    if _contains_any(
        text,
        stress_terms,
    ):
        plan.needs_stress = True
        plan.needs_risk = True

    if _contains_any(
        text,
        hedge_terms,
    ):
        plan.needs_hedge = True
        plan.needs_risk = True

    if _contains_any(
        text,
        etf_terms,
    ):
        plan.needs_etf_analytics = True
        plan.needs_prices = True

    if _contains_any(
        text,
        research_terms,
    ):
        plan.needs_research = True

    if _contains_any(
        text,
        pricing_terms,
    ):
        plan.needs_prices = True

    if _is_price_attribution_request(
        text
    ):
        plan.needs_price_attribution = True
        plan.needs_prices = True

        #
        # A price move may also have issuer-specific
        # evidence. Research retrieval remains optional
        # downstream if no issuer can be resolved.
        #
        plan.needs_research = True

    return plan


def normalize_issuer(
    issuer: str | None,
) -> str | None:
    if issuer is None:
        return None

    cleaned = issuer.strip()

    if not cleaned:
        return None

    if cleaned.lower() in {
        "unknown",
        "none",
        "null",
        "n/a",
        "na",
    }:
        return None

    return cleaned



def build_fast_plan(
    question: str,
) -> AgentPlan | None:
    """
    Route obvious fixed-income requests without
    invoking the local LLM.

    This is intentionally conservative. Ambiguous
    requests still fall through to Ollama.
    """

    text = question.lower()

    relative_value_terms = (
        "cheap",
        "rich",
        "expensive",
        "relative value",
        "relative-value",
        "mispriced",
        "undervalued",
        "overvalued",
    )

    risk_terms = (
        "risk",
        "risky",
        "dv01",
        "cs01",
        "key rate",
        "key-rate",
        "exposure",
    )

    stress_terms = (
        "stress",
        "shock",
        "selloff",
        "sell-off",
        "scenario",
    )

    hedge_terms = (
        "hedge",
        "hedging",
        "neutralize",
        "neutralise",
    )

    etf_terms = (
        "etf",
        "nav",
        "basket",
        "premium",
        "discount",
    )

    research_terms = (
        "why",
        "filing",
        "filings",
        "fundamental",
        "fundamentals",
        "catalyst",
        "catalysts",
        "research",
        "credit event",
        "credit risk",
        "credit quality",
        "default risk",
        "issuer risk",
        "explain",
    )

    pricing_terms = (
        "price",
        "pricing",
        "yield",
        "g-spread",
        "spread",
    )

    has_relative_value = _contains_any(
        text,
        relative_value_terms,
    )

    has_risk = _contains_any(
        text,
        risk_terms,
    )

    has_stress = _contains_any(
        text,
        stress_terms,
    )

    has_hedge = _contains_any(
        text,
        hedge_terms,
    )

    has_etf = _contains_any(
        text,
        etf_terms,
    )

    has_research = _contains_any(
        text,
        research_terms,
    )

    has_pricing = _contains_any(
        text,
        pricing_terms,
    )

    has_price_attribution = (
        _is_price_attribution_request(
            text
        )
    )

    #
    # These signals are sufficiently explicit that
    # there is little value in asking the LLM to
    # rediscover the route.
    #
    fast_path = any(
        (
            has_relative_value,
            has_risk,
            has_stress,
            has_hedge,
            has_etf,
            has_price_attribution,
        )
    )

    #
    # Explicit numeric price/yield requests are also
    # deterministic.
    #
    if (
        has_pricing
        and any(
            character.isdigit()
            for character in text
        )
    ):
        fast_path = True

    if not fast_path:
        return None

    needs_risk = (
        has_risk
        or has_stress
        or has_hedge
    )

    needs_prices = (
        has_pricing
        or has_relative_value
        or has_risk
        or has_stress
        or has_hedge
        or has_etf
        or has_price_attribution
    )

    if has_stress:
        intent = "stress"

    elif has_hedge:
        intent = "hedge"

    elif has_etf:
        intent = "etf_analytics"

    elif has_relative_value:
        intent = "relative_value"

    elif has_price_attribution:
        intent = "price_attribution"

    elif has_risk:
        intent = "risk"

    else:
        intent = "pricing"

    plan = AgentPlan(
        intent=intent,
        issuer=None,

        needs_research=
            (
                has_research
                or has_price_attribution
            ),

        needs_prices=
            needs_prices,

        needs_price_attribution=
            has_price_attribution,

        needs_relative_value=
            has_relative_value,

        needs_risk=
            needs_risk,

        needs_stress=
            has_stress,

        needs_hedge=
            has_hedge,

        needs_etf_analytics=
            has_etf,
    )

    #
    # Reuse the existing domain guardrails so the
    # fast and LLM paths obey the same rules.
    #
    return apply_guardrails(
        plan,
        question,
    )

def plan_query_node(
    state: AgentState,
) -> AgentState:
    request = state["request"]

    fast_plan = build_fast_plan(
        request.question
    )

    if fast_plan is not None:
        return {
            "plan":
                fast_plan,

            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),

                "planner": {
                    "provider":
                        "deterministic",

                    "intent":
                        fast_plan.intent,

                    "issuer":
                        fast_plan.issuer,

                    "fast_path":
                        True,

                    "routing": {
                        "research":
                            fast_plan.needs_research,

                        "prices":
                            fast_plan.needs_prices,

                        "price_attribution":
                            fast_plan.needs_price_attribution,

                        "relative_value":
                            fast_plan.needs_relative_value,

                        "risk":
                            fast_plan.needs_risk,

                        "stress":
                            fast_plan.needs_stress,

                        "hedge":
                            fast_plan.needs_hedge,

                        "etf_analytics":
                            fast_plan.needs_etf_analytics,
                    },
                },
            },
        }

    client = LLMClient()

    try:
        payload = client.generate_json(
            system_prompt=
                SYSTEM_PROMPT,

            user_prompt=f"""
User question:
{request.question}

Issuer explicitly supplied by caller:
{request.issuer}

Known instrument IDs:
{request.instrument_ids}

Return exactly these fields:

intent
issuer
needs_research
needs_prices
needs_price_attribution
needs_relative_value
needs_risk
needs_stress
needs_hedge
needs_etf_analytics
""",

            think=False,
        )

        plan = (
            AgentPlan
            .model_validate(
                payload
            )
        )

        #
        # Caller-provided structured data wins
        # over model extraction.
        #
        if request.issuer:
            plan.issuer = (
                request.issuer
            )

        plan.issuer = (
            normalize_issuer(
                plan.issuer
            )
        )

        #
        # Deterministic corrections.
        #
        plan = apply_guardrails(
            plan,
            request.question,
        )

        state["plan"] = plan

        diagnostics = (
            state.setdefault(
                "diagnostics",
                {},
            )
        )

        diagnostics[
            "planner"
        ] = {
            "provider":
                client.provider,

            "model":
                client.model,

            "intent":
                plan.intent,

            "issuer":
                plan.issuer,

            "routing": {
                "research":
                    plan.needs_research,

                "prices":
                    plan.needs_prices,

                "price_attribution":
                    plan.needs_price_attribution,

                "relative_value":
                    plan.needs_relative_value,

                "risk":
                    plan.needs_risk,

                "stress":
                    plan.needs_stress,

                "hedge":
                    plan.needs_hedge,

                "etf_analytics":
                    plan.needs_etf_analytics,
            },
        }

    except Exception as error:
        #
        # Safe fallback:
        # preserve useful Mercator behavior
        # if Ollama is unavailable or malformed.
        #
        plan = AgentPlan(
            intent=(
                "general_fixed_income_analysis"
            ),

            issuer=request.issuer,

            needs_research=True,
            needs_prices=True,
            needs_price_attribution=False,

            needs_relative_value=False,
            needs_risk=False,
            needs_stress=False,
            needs_hedge=False,
            needs_etf_analytics=False,
        )

        plan = apply_guardrails(
            plan,
            request.question,
        )

        state["plan"] = plan

        errors = (
            state.setdefault(
                "errors",
                [],
            )
        )

        errors.append(
            "LLM planning fallback: "
            f"{error}"
        )

        diagnostics = (
            state.setdefault(
                "diagnostics",
                {},
            )
        )

        diagnostics[
            "planner"
        ] = {
            "provider":
                client.provider,

            "model":
                client.model,

            "fallback":
                True,

            "error":
                str(error),
        }

    return state
