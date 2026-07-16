from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReferenceObservation(BaseModel):
    observation_id: UUID
    instrument_id: int
    field_name: str
    field_value: str
    source_name: str
    source_priority: int
    trust_score: float
    valid_from: datetime
    valid_to: datetime | None = None


class ReconciliationResult(BaseModel):
    instrument_id: int
    field_name: str
    selected_value: str
    selected_source: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    contributing_observations: list[UUID]
