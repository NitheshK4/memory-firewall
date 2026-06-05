from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class ClaimType(StrEnum):
    FACT = "fact"
    PREFERENCE = "preference"
    INSTRUCTION = "instruction"
    POLICY = "policy"
    IDENTITY = "identity"


class MemoryClaim(BaseModel):
    claim_id: str = Field(default_factory=lambda: str(uuid4()))
    claim_type: ClaimType
    text: str
    subject: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.65)

