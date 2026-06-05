from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class PolicyScope(StrEnum):
    GLOBAL = "global"
    SOURCE_TYPE = "source_type"
    ACTOR = "actor"
    CLAIM_TYPE = "claim_type"


class PolicyAction(StrEnum):
    BLOCK = "block"
    QUARANTINE = "quarantine"
    LOW_TRUST = "low_trust"
    ALLOW = "allow"
    REQUIRE_REVIEW = "require_review"


class PolicyRule(BaseModel):
    rule_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str = ""
    scope: PolicyScope = PolicyScope.GLOBAL
    scope_value: str | None = None  # e.g. "email" when scope=SOURCE_TYPE
    condition_flags: list[str] = Field(default_factory=list)
    min_risk_score: float | None = None  # trigger if risk >= this value
    action: PolicyAction = PolicyAction.QUARANTINE
    priority: int = Field(default=100, ge=0)
    enabled: bool = True


class PolicyEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    memory_id: str
    rule_id: str
    rule_name: str
    action_taken: PolicyAction
    triggered_flags: list[str] = Field(default_factory=list)
    risk_score: float
