from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field


class AuthorityLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ProvenanceRecord(BaseModel):
    source_type: str
    source_id: str | None = None
    actor: str
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    authority_level: AuthorityLevel = AuthorityLevel.MEDIUM
    authority_score: float = Field(ge=0.0, le=1.0, default=0.6)
    metadata: dict[str, str] = Field(default_factory=dict)

