from __future__ import annotations

from mercator_agent.state.models import (
    AgentState,
)

from mercator_agent.tools.quality import (
    assess_market_quality,
)


def assess_quality_node(
    state: AgentState,
) -> AgentState:
    prices = state.get(
        "prices",
        [],
    )

    quality = assess_market_quality(
        prices
    )

    return {
        "quality": quality,

        "diagnostics": {
            **state.get(
                "diagnostics",
                {},
            ),

            "quality": {
                "status":
                    quality.status,

                "score":
                    quality.score,

                "issues":
                    len(
                        quality.issues
                    ),

                "blocking_issues":
                    sum(
                        1
                        for issue
                        in quality.issues
                        if issue.severity
                        == "BLOCKING"
                    ),
            },
        },
    }
