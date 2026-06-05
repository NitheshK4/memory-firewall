from enum import StrEnum

from pydantic import BaseModel, Field


class VerdictAction(StrEnum):
    ALLOW = "allow"
    LOW_TRUST = "low_trust"
    QUARANTINE = "quarantine"
    BLOCK = "block"


class MemoryStatus(StrEnum):
    ALLOWED = "allowed"
    LOW_TRUST = "low_trust"
    QUARANTINED = "quarantined"
    BLOCKED = "blocked"


class RiskAssessment(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    flags: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class MemoryVerdict(BaseModel):
    action: VerdictAction
    trust_score: float = Field(ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)

