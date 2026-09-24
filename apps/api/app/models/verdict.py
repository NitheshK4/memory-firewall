"""Verdict models for the Memory Firewall decision pipeline.

This module defines the action enums, status enums, and Pydantic models
used to represent risk assessments and final verdicts produced by the
firewall engine for every memory read/write operation.
"""

from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field


class VerdictAction(StrEnum):
    """Possible actions the firewall can take on a memory operation."""

    ALLOW = "allow"
    LOW_TRUST = "low_trust"
    QUARANTINE = "quarantine"
    BLOCK = "block"


class MemoryStatus(StrEnum):
    """Persisted status of a memory record after firewall evaluation."""

    ALLOWED = "allowed"
    LOW_TRUST = "low_trust"
    QUARANTINED = "quarantined"
    BLOCKED = "blocked"


class RiskAssessment(BaseModel):
    """Detailed risk breakdown produced by the firewall engine.

    Attributes:
        score: Normalised risk score in [0.0, 1.0]. Higher = riskier.
        flags: Short identifiers for triggered risk heuristics.
        reasons: Human-readable explanations for each flag.
        contradiction_count: Number of existing memories that contradict
            this write, used to boost the overall risk score.
        confidence: Model confidence in the assessment, in [0.0, 1.0].
    """

    score: float = Field(ge=0.0, le=1.0, description="Normalised risk score.")
    flags: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    contradiction_count: int = Field(
        default=0,
        description="Number of existing memories that contradict this write.",
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence of the risk model in its own assessment.",
    )


class MemoryVerdict(BaseModel):
    """Final actionable verdict returned by the firewall for a memory op.

    Attributes:
        action: The action the system should take.
        trust_score: Aggregated trust score for this memory, in [0.0, 1.0].
        reasons: Human-readable justifications for the chosen action.
        assessment: Optional full risk assessment that led to this verdict.
    """

    action: VerdictAction
    trust_score: float = Field(ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)
    assessment: Optional[RiskAssessment] = Field(
        default=None,
        description="Full risk assessment that produced this verdict.",
    )

