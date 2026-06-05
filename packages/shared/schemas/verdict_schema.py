"""Shared Pydantic schema for MemoryVerdict — importable by connectors and evals."""

from enum import StrEnum

from pydantic import BaseModel, Field


class VerdictAction(StrEnum):
    ALLOW = "allow"
    LOW_TRUST = "low_trust"
    QUARANTINE = "quarantine"
    BLOCK = "block"


class VerdictSchema(BaseModel):
    action: VerdictAction
    trust_score: float = Field(ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)
