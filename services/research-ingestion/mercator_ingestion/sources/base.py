from __future__ import annotations

from typing import Protocol

from mercator_ingestion.models.document import (
    DocumentReference,
    RawDocument,
)


class ResearchSource(Protocol):
    async def discover(
        self,
        maximum_pages: int | None = None,
    ) -> list[DocumentReference]:
        ...

    async def fetch(
        self,
        reference: DocumentReference,
    ) -> RawDocument:
        ...
