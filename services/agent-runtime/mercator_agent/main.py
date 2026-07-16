from __future__ import annotations

from fastapi import FastAPI, HTTPException

from mercator_agent.graph import graph
from mercator_agent.state.models import (
    AgentRequest,
    ClientBrief,
)


app = FastAPI(
    title="Mercator Agent Runtime",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
    }


@app.post(
    "/analyze",
    response_model=ClientBrief,
)
def analyze(
    request: AgentRequest,
) -> ClientBrief:
    result = graph.invoke(
        {
            "request": request,
            "errors": [],
        }
    )

    brief = result.get("brief")

    if brief is None:
        raise HTTPException(
            status_code=422,
            detail={
                "message": (
                    "Agent could not produce a brief"
                ),
                "errors": result.get(
                    "errors",
                    [],
                ),
            },
        )

    return brief
