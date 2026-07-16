from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CreditSignal:
    signal_type: str
    signal_value: str
    confidence_score: float
    evidence_text: str
    extraction_method: str


SIGNAL_RULES: dict[
    str,
    list[tuple[str, re.Pattern[str]]],
] = {
    "liquidity": [
        (
            "liquidity_pressure",
            re.compile(
                r"\b("
                r"liquidity constraints|"
                r"limited liquidity|"
                r"cash shortfall|"
                r"liquidity risk"
                r")\b",
                re.IGNORECASE,
            ),
        ),
        (
            "strong_liquidity",
            re.compile(
                r"\b("
                r"substantial liquidity|"
                r"ample liquidity|"
                r"strong cash position|"
                r"sufficient liquidity"
                r")\b",
                re.IGNORECASE,
            ),
        ),
    ],
    "debt": [
        (
            "debt_increase",
            re.compile(
                r"\b("
                r"debt increased|"
                r"additional indebtedness|"
                r"higher borrowings|"
                r"increase in borrowings"
                r")\b",
                re.IGNORECASE,
            ),
        ),
        (
            "debt_reduction",
            re.compile(
                r"\b("
                r"debt reduction|"
                r"repaid debt|"
                r"reduced borrowings|"
                r"lower indebtedness"
                r")\b",
                re.IGNORECASE,
            ),
        ),
    ],
    "refinancing": [
        (
            "refinancing_risk",
            re.compile(
                r"\b("
                r"refinancing risk|"
                r"unable to refinance|"
                r"refinance.*unfavorable|"
                r"maturing debt"
                r")\b",
                re.IGNORECASE,
            ),
        ),
    ],
    "interest_rates": [
        (
            "rate_sensitivity",
            re.compile(
                r"\b("
                r"interest rate risk|"
                r"higher interest rates|"
                r"variable-rate debt|"
                r"interest expense may increase"
                r")\b",
                re.IGNORECASE,
            ),
        ),
    ],
    "regulation": [
        (
            "regulatory_risk",
            re.compile(
                r"\b("
                r"regulatory risk|"
                r"regulatory requirements|"
                r"government investigation|"
                r"regulatory proceedings"
                r")\b",
                re.IGNORECASE,
            ),
        ),
    ],
    "operations": [
        (
            "supply_chain_risk",
            re.compile(
                r"\b("
                r"supply chain disruption|"
                r"supplier concentration|"
                r"component shortages|"
                r"manufacturing disruption"
                r")\b",
                re.IGNORECASE,
            ),
        ),
        (
            "cybersecurity_risk",
            re.compile(
                r"\b("
                r"cybersecurity incident|"
                r"cyber attack|"
                r"data breach|"
                r"information security risk"
                r")\b",
                re.IGNORECASE,
            ),
        ),
    ],
}


def evidence_window(
    text: str,
    start: int,
    end: int,
    *,
    radius: int = 220,
) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)

    return text[left:right].strip()


def extract_credit_signals(
    text: str,
) -> list[CreditSignal]:
    signals: list[CreditSignal] = []
    seen: set[tuple[str, str]] = set()

    for signal_type, rules in SIGNAL_RULES.items():
        for signal_value, pattern in rules:
            match = pattern.search(text)

            if match is None:
                continue

            key = (
                signal_type,
                signal_value,
            )

            if key in seen:
                continue

            seen.add(key)

            signals.append(
                CreditSignal(
                    signal_type=signal_type,
                    signal_value=signal_value,
                    confidence_score=0.85,
                    evidence_text=evidence_window(
                        text,
                        match.start(),
                        match.end(),
                    ),
                    extraction_method=(
                        "deterministic-rules-v1"
                    ),
                )
            )

    return signals
