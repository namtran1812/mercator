from __future__ import annotations

import re

from mercator_agent.state.models import (
    AgentState,
    SecurityResolution,
)

from mercator_agent.tools.reference_data import (
    get_instrument_profiles,
    resolve_securities,
)


def _extract_numeric_instrument_ids(
    question: str,
) -> list[int]:
    patterns = (
        r"\binstrument\s+#?(\d+)\b",
        r"\bbond\s+#?(\d+)\b",
        r"\betf\s+#?(\d+)\b",
    )

    values: list[int] = []

    for pattern in patterns:
        matches = re.findall(
            pattern,
            question,
            flags=re.IGNORECASE,
        )

        for match in matches:
            value = int(
                match
            )

            if value > 0:
                values.append(
                    value
                )

    return list(
        dict.fromkeys(
            values
        )
    )


def _candidate_query(
    state: AgentState,
) -> str | None:
    request = state[
        "request"
    ]

    plan = state.get(
        "plan"
    )

    #
    # Explicit caller-supplied issuer wins.
    #
    if request.issuer:
        return request.issuer.strip()

    #
    # Planner extraction is second.
    #
    if (
        plan is not None
        and plan.issuer
    ):
        return plan.issuer.strip()

    question = (
        request.question
        .strip()
    )

    #
    # Extract text immediately before
    # bond / bonds / ETF / fund.
    #
    match = re.search(
        r"([A-Za-z][A-Za-z0-9&.\- ]{0,60}?)"
        r"\s+(?:bond|bonds|etf|fund)\b",
        question,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    candidate = (
        match.group(1)
        .strip()
    )

    removable_prefixes = {
        "find",
        "show",
        "compare",
        "analyze",
        "analyse",
        "get",
        "give",
        "list",
        "screen",
        "rank",
        "identify",

        "cheap",
        "rich",
        "expensive",
        "attractive",
        "mispriced",
        "undervalued",
        "overvalued",

        "the",
        "some",
        "all",
        "best",
        "most",
    }

    words = candidate.split()

    while (
        words
        and words[0].lower()
        in removable_prefixes
    ):
        words.pop(0)

    if not words:
        return None

    candidate = " ".join(
        words
    ).strip()

    return (
        candidate
        if candidate
        else None
    )


def _infer_instrument_type(
    question: str,
) -> str | None:
    text = question.lower()

    if (
        "etf" in text
        or "fund" in text
        or "nav" in text
    ):
        return (
            "FIXED_INCOME_ETF"
        )

    if (
        "bond" in text
        or "corporate bond" in text
    ):
        return (
            "CORPORATE_BOND"
        )

    return None


def resolve_security_node(
    state: AgentState,
) -> AgentState:
    request = state[
        "request"
    ]

    plan = state.get(
        "plan"
    )

    #
    # --------------------------------------------------------
    # 1. Explicit caller-provided instrument IDs
    # --------------------------------------------------------
    #
    if request.instrument_ids:
        instrument_ids = list(
            request.instrument_ids
        )

        instrument_type = (
            _infer_instrument_type(
                request.question
            )
        )

        issuer_name = (
            request.issuer
        )

        profile_count = 0

        try:
            profiles = (
                get_instrument_profiles(
                    instrument_ids
                )
            )

            profile_count = len(
                profiles
            )

            if profiles:
                if issuer_name is None:
                    issuers = list(
                        dict.fromkeys(
                            profile.issuer_name
                            for profile
                            in profiles
                            if profile.issuer_name
                        )
                    )

                    if len(issuers) == 1:
                        issuer_name = (
                            issuers[0]
                        )

                if instrument_type is None:
                    types = list(
                        dict.fromkeys(
                            profile.instrument_type
                            for profile
                            in profiles
                            if profile.instrument_type
                        )
                    )

                    if len(types) == 1:
                        instrument_type = (
                            types[0]
                        )

        except Exception as error:
            #
            # Caller-provided IDs remain usable even if
            # metadata hydration is temporarily unavailable.
            #
            hydration_error = str(
                error
            )

        else:
            hydration_error = None

        security = SecurityResolution(
            query=
                "caller_provided",

            instrument_ids=
                instrument_ids,

            instrument_type=
                instrument_type,

            issuer_name=
                issuer_name,

            result_count=
                len(
                    instrument_ids
                ),
        )

        diagnostics = {
            **state.get(
                "diagnostics",
                {},
            ),

            "security_resolution": {
                "status":
                    "caller_provided",

                "instrument_ids":
                    security.instrument_ids,

                "instrument_type":
                    security.instrument_type,

                "issuer_name":
                    security.issuer_name,

                "profiles_hydrated":
                    profile_count,
            },
        }

        if hydration_error is not None:
            diagnostics[
                "security_resolution"
            ][
                "hydration_error"
            ] = hydration_error

        return {
            "security":
                security,

            "diagnostics":
                diagnostics,
        }

    #
    # --------------------------------------------------------
    # 2. Numeric IDs embedded in natural language
    #
    # "instrument 42"
    # "bond 42"
    # "ETF 9501"
    # --------------------------------------------------------
    #
    numeric_ids = (
        _extract_numeric_instrument_ids(
            request.question
        )
    )

    if numeric_ids:
        security = SecurityResolution(
            query=
                "numeric_extraction",

            instrument_ids=
                numeric_ids,

            instrument_type=
                _infer_instrument_type(
                    request.question
                ),

            issuer_name=
                request.issuer,

            result_count=
                len(
                    numeric_ids
                ),
        )

        return {
            "security":
                security,

            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),

                "security_resolution": {
                    "status":
                        "numeric_extraction",

                    "instrument_ids":
                        security.instrument_ids,

                    "instrument_type":
                        security.instrument_type,
                },
            },
        }

    #
    # --------------------------------------------------------
    # 3. Search the Reference Data security master
    # --------------------------------------------------------
    #
    query = _candidate_query(
        state
    )

    if query is None:
        return {
            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),

                "security_resolution": {
                    "status":
                        "skipped",

                    "reason":
                        "no_security_query",
                },
            },
        }

    instrument_type = (
        _infer_instrument_type(
            request.question
        )
    )

    #
    # Planner explicitly requesting ETF analytics
    # takes precedence.
    #
    if (
        plan is not None
        and plan.needs_etf_analytics
    ):
        instrument_type = (
            "FIXED_INCOME_ETF"
        )

    try:
        security = resolve_securities(
            query,
            instrument_type=
                instrument_type,
            limit=50,
        )

        if not isinstance(
            security,
            SecurityResolution,
        ):
            security = (
                SecurityResolution
                .model_validate(
                    security
                )
            )

        if not security.instrument_ids:
            return {
                "security":
                    security,

                "diagnostics": {
                    **state.get(
                        "diagnostics",
                        {},
                    ),

                    "security_resolution": {
                        "status":
                            "not_found",

                        "query":
                            query,

                        "instrument_type":
                            instrument_type,
                    },
                },
            }

        return {
            "security":
                security,

            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),

                "security_resolution": {
                    "status":
                        "resolved",

                    "query":
                        query,

                    "instrument_type":
                        security.instrument_type,

                    "result_count":
                        security.result_count,

                    "instrument_ids":
                        security.instrument_ids,
                },
            },
        }

    except Exception as error:
        return {
            "errors": [
                *state.get(
                    "errors",
                    [],
                ),

                (
                    "Security resolution failed: "
                    f"{error}"
                ),
            ],

            "diagnostics": {
                **state.get(
                    "diagnostics",
                    {},
                ),

                "security_resolution": {
                    "status":
                        "failed",

                    "query":
                        query,

                    "error":
                        str(error),
                },
            },
        }
