from __future__ import annotations

from fastapi import (
    FastAPI,
    HTTPException,
)

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from mercator_agent.graph import graph

from mercator_agent.state.models import (
    AgentQueryResponse,
    AgentRequest,
    ClientBrief,
)


app = FastAPI(
    title="Mercator Agent Runtime",
    version="0.2.0",
)


#
# Local Workbench access.
#
app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://127.0.0.1:8005",
        "http://localhost:8005",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],

    allow_credentials=True,

    allow_methods=[
        "GET",
        "POST",
        "OPTIONS",
    ],

    allow_headers=[
        "*",
    ],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
    }


def run_agent(
    request: AgentRequest,
) -> dict:
    return graph.invoke(
        {
            "request": request,
            "errors": [],
        }
    )


#
# Existing compatibility endpoint.
#
@app.post(
    "/analyze",
    response_model=ClientBrief,
)
def analyze(
    request: AgentRequest,
) -> ClientBrief:
    result = run_agent(
        request
    )

    brief = result.get(
        "brief"
    )

    if brief is None:
        raise HTTPException(
            status_code=422,
            detail={
                "message":
                    "Agent could not produce a brief",

                "errors":
                    result.get(
                        "errors",
                        [],
                    ),
            },
        )

    return brief


#
# Full Workbench endpoint.
#
@app.post(
    "/agent/query",
    response_model=AgentQueryResponse,
)
def agent_query(
    request: AgentRequest,
) -> AgentQueryResponse:
    result = run_agent(
        request
    )

    return AgentQueryResponse(
        brief=
            result.get(
                "brief"
            ),

        plan=
            result.get(
                "plan"
            ),

        security=
            result.get(
                "security"
            ),

        prices=
            result.get(
                "prices",
                [],
            ),

        quality=
            result.get(
                "quality"
            ),

        price_attribution=
            result.get(
                "price_attribution",
                [],
            ),

        relative_value=
            result.get(
                "relative_value",
                [],
            ),

        risk=
            result.get(
                "risk"
            ),

        hedge=
            result.get(
                "hedge"
            ),

        stress=
            result.get(
                "stress"
            ),

        etf_analytics=
            result.get(
                "etf_analytics"
            ),

        evidence=
            result.get(
                "evidence",
                [],
            ),

        diagnostics=
            result.get(
                "diagnostics",
                {},
            ),

        errors=
            result.get(
                "errors",
                [],
            ),
    )
