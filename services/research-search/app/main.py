from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, HTTPException

from .hybrid_search import HybridSearchService
from .models import (
    SearchRequest,
    SearchResponse,
)
from .repository import ResearchRepository
from .semantic_index import SemanticIndex


repository = ResearchRepository()
semantic_index = SemanticIndex()

search_service = HybridSearchService(
    repository,
    semantic_index,
)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:
    del app

    try:
        semantic_index.load()
    except FileNotFoundError:
        print(
            "Semantic index not found. "
            "Run build_semantic_index.py."
        )

    yield


app = FastAPI(
    title="Mercator Research Search",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
    }


@app.post(
    "/search",
    response_model=SearchResponse,
)
def search(
    request: SearchRequest,
) -> SearchResponse:
    try:
        results = search_service.search(
            query=request.query,
            cik=request.cik,
            forms=request.forms,
            limit=request.limit,
        )
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail=(
                "Semantic index is unavailable. "
                "Build the index first."
            ),
        ) from error

    return SearchResponse(
        query=request.query,
        mode="hybrid_rrf",
        result_count=len(results),
        results=results,
    )
