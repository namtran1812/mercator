from __future__ import annotations

from collections import defaultdict
from typing import Any
from uuid import UUID

from .models import SearchResult
from .repository import ResearchRepository
from .semantic_index import SemanticIndex


class HybridSearchService:
    def __init__(
        self,
        repository: ResearchRepository,
        semantic_index: SemanticIndex,
    ) -> None:
        self._repository = repository
        self._semantic_index = semantic_index

    def search(
        self,
        *,
        query: str,
        cik: str | None,
        forms: list[str] | None,
        limit: int,
    ) -> list[SearchResult]:
        candidate_limit = max(
            limit * 4,
            20,
        )

        lexical_rows = (
            self._repository.lexical_search(
                query=query,
                cik=cik,
                forms=forms,
                limit=candidate_limit,
            )
        )

        semantic_matches = (
            self._semantic_index.search(
                query,
                limit=candidate_limit * 2,
            )
        )

        semantic_ids = [
            match.chunk_id
            for match in semantic_matches
        ]

        semantic_rows = (
            self._repository.chunks_by_ids(
                semantic_ids
            )
        )

        if cik:
            normalized_cik = cik.zfill(10)

            semantic_rows = {
                chunk_id: row
                for chunk_id, row in semantic_rows.items()
                if row["cik"] == normalized_cik
            }

        if forms:
            allowed_forms = set(forms)

            semantic_rows = {
                chunk_id: row
                for chunk_id, row in semantic_rows.items()
                if row["form_type"] in allowed_forms
            }

        fused_scores: dict[UUID, float] = (
            defaultdict(float)
        )

        lexical_scores: dict[UUID, float] = {}
        semantic_scores: dict[UUID, float] = {}
        rows_by_id: dict[UUID, dict[str, Any]] = {}

        reciprocal_rank_constant = 60.0

        for rank, row in enumerate(
            lexical_rows,
            start=1,
        ):
            chunk_id = row["chunk_id"]

            fused_scores[chunk_id] += (
                1.0 /
                (
                    reciprocal_rank_constant
                    + rank
                )
            )

            lexical_scores[chunk_id] = float(
                row["lexical_rank"]
            )

            rows_by_id[chunk_id] = row

        semantic_rank = 0

        for match in semantic_matches:
            row = semantic_rows.get(
                match.chunk_id
            )

            if row is None:
                continue

            semantic_rank += 1

            fused_scores[match.chunk_id] += (
                1.0 /
                (
                    reciprocal_rank_constant
                    + semantic_rank
                )
            )

            semantic_scores[match.chunk_id] = (
                match.score
            )

            rows_by_id[match.chunk_id] = row

        ranked_ids = sorted(
            fused_scores,
            key=lambda chunk_id: fused_scores[
                chunk_id
            ],
            reverse=True,
        )[:limit]

        results: list[SearchResult] = []

        for chunk_id in ranked_ids:
            row = rows_by_id[chunk_id]

            citation_label = (
                f"{row['issuer_name']} "
                f"{row['form_type']} "
                f"{row['filing_date']} "
                f"§{row['section_name'] or 'unknown'} "
                f"chunk {row['chunk_index']}"
            )

            results.append(
                SearchResult(
                    chunk_id=chunk_id,
                    cik=row["cik"],
                    issuer_name=row["issuer_name"],
                    form_type=row["form_type"],
                    filing_date=row["filing_date"],
                    accession_number=(
                        row["accession_number"]
                    ),
                    section_name=(
                        row["section_name"]
                    ),
                    chunk_index=(
                        row["chunk_index"]
                    ),
                    chunk_text=row["chunk_text"],
                    filing_url=row["filing_url"],
                    index_url=row["index_url"],
                    lexical_rank=lexical_scores.get(
                        chunk_id,
                        0.0,
                    ),
                    semantic_score=semantic_scores.get(
                        chunk_id,
                        0.0,
                    ),
                    fused_score=fused_scores[
                        chunk_id
                    ],
                    citation_label=(
                        citation_label
                    ),
                )
            )

        return results
