from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field

from apps.api.app.models.claim import MemoryClaim
from apps.api.app.models.provenance import ProvenanceRecord
from apps.api.app.models.verdict import MemoryStatus, MemoryVerdict


class MemoryWriteRequest(BaseModel):
    content: str = Field(min_length=1)
    source_type: str = Field(default="unknown")
    source_id: str | None = None
    actor: str = Field(default="unknown")
    metadata: dict[str, str] = Field(default_factory=dict)


class StoredMemory(BaseModel):
    memory_id: str = Field(default_factory=lambda: str(uuid4()))
    raw_content: str
    claims: list[MemoryClaim] = Field(default_factory=list)
    provenance: ProvenanceRecord
    status: MemoryStatus = MemoryStatus.ALLOWED
    trust_score: float = Field(ge=0.0, le=1.0, default=0.5)
    contradictions: list[str] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MemoryWriteResponse(BaseModel):
    memory: StoredMemory
    verdict: MemoryVerdict


class RetrievalRequest(BaseModel):
    query: str = Field(min_length=1)
    actor: str = Field(default="unknown")
    max_results: int = Field(default=5, ge=1, le=20)
    min_trust_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Exclude results whose trust_score is below this threshold (0 = no filter).",
    )


class RetrievalResult(BaseModel):
    memory_id: str
    raw_content: str
    claims: list[MemoryClaim]
    trust_score: float
    status: MemoryStatus
    reasons: list[str] = Field(default_factory=list)


class RetrievalResponse(BaseModel):
    query: str
    results: list[RetrievalResult] = Field(default_factory=list)


class ReviewAction(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    EDIT = "edit"


class ReviewDecision(BaseModel):
    action: ReviewAction
    reviewer: str = Field(default="reviewer")
    edited_content: str | None = None

