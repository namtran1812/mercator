from __future__ import annotations

import os
from pathlib import Path

POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    "postgresql://mercator:mercator@localhost:5432/mercator",
)

EMBEDDING_MODEL = os.getenv(
    "MERCATOR_EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)

INDEX_DIRECTORY = Path(
    os.getenv(
        "MERCATOR_SEARCH_INDEX_DIRECTORY",
        "artifacts/search-index",
    )
)

FAISS_INDEX_PATH = INDEX_DIRECTORY / "sec_chunks.faiss"
FAISS_METADATA_PATH = INDEX_DIRECTORY / "sec_chunks.json"
