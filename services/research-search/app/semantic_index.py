from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from .config import (
    EMBEDDING_MODEL,
    FAISS_INDEX_PATH,
    FAISS_METADATA_PATH,
    INDEX_DIRECTORY,
)
from .repository import ResearchRepository


@dataclass(frozen=True)
class SemanticMatch:
    chunk_id: UUID
    score: float


class SemanticIndex:
    def __init__(
        self,
        *,
        model_name: str = EMBEDDING_MODEL,
    ) -> None:
        self._model = SentenceTransformer(
            model_name
        )

        self._index: faiss.Index | None = None
        self._chunk_ids: list[UUID] = []

    def build(
        self,
        repository: ResearchRepository,
    ) -> int:
        rows = repository.all_chunks()

        if not rows:
            raise RuntimeError(
                "No SEC filing chunks exist"
            )

        texts = [
            self._embedding_text(row)
            for row in rows
        ]

        embeddings = self._model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        matrix = np.asarray(
            embeddings,
            dtype=np.float32,
        )

        index = faiss.IndexFlatIP(
            matrix.shape[1]
        )

        index.add(matrix)

        INDEX_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True,
        )

        faiss.write_index(
            index,
            str(FAISS_INDEX_PATH),
        )

        chunk_ids = [
            str(row["chunk_id"])
            for row in rows
        ]

        FAISS_METADATA_PATH.write_text(
            json.dumps(
                {
                    "model": EMBEDDING_MODEL,
                    "count": len(chunk_ids),
                    "chunk_ids": chunk_ids,
                },
                indent=2,
            )
        )

        self._index = index
        self._chunk_ids = [
            UUID(value)
            for value in chunk_ids
        ]

        return len(chunk_ids)

    def load(self) -> None:
        if not FAISS_INDEX_PATH.exists():
            raise FileNotFoundError(
                FAISS_INDEX_PATH
            )

        if not FAISS_METADATA_PATH.exists():
            raise FileNotFoundError(
                FAISS_METADATA_PATH
            )

        metadata = json.loads(
            FAISS_METADATA_PATH.read_text()
        )

        self._index = faiss.read_index(
            str(FAISS_INDEX_PATH)
        )

        self._chunk_ids = [
            UUID(value)
            for value in metadata["chunk_ids"]
        ]

        if self._index.ntotal != len(
            self._chunk_ids
        ):
            raise RuntimeError(
                "FAISS index and metadata differ"
            )

    def search(
        self,
        query: str,
        *,
        limit: int,
    ) -> list[SemanticMatch]:
        if self._index is None:
            self.load()

        assert self._index is not None

        query_embedding = self._model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        query_matrix = np.asarray(
            query_embedding,
            dtype=np.float32,
        )

        scores, indices = self._index.search(
            query_matrix,
            min(limit, len(self._chunk_ids)),
        )

        matches: list[SemanticMatch] = []

        for score, index in zip(
            scores[0],
            indices[0],
            strict=True,
        ):
            if index < 0:
                continue

            matches.append(
                SemanticMatch(
                    chunk_id=self._chunk_ids[index],
                    score=float(score),
                )
            )

        return matches

    @staticmethod
    def _embedding_text(
        row: dict[str, object],
    ) -> str:
        return (
            f"Issuer: {row['issuer_name']}\n"
            f"Form: {row['form_type']}\n"
            f"Section: {row['section_name']}\n"
            f"{row['chunk_text']}"
        )
