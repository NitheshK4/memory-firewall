"""Tests for PolicyEngine."""

from apps.api.app.models.provenance import AuthorityLevel, ProvenanceRecord
from apps.api.app.models.verdict import RiskAssessment, VerdictAction
from apps.api.app.services.policy_engine import PolicyEngine


def _provenance(authority: float = 0.7, source: str = "human") -> ProvenanceRecord:
    return ProvenanceRecord(
        source_type=source,
        actor="tester",
        authority_score=authority,
        authority_level=AuthorityLevel.MEDIUM,
    )


def _assessment(score: float, flags: list[str] | None = None) -> RiskAssessment:
    return RiskAssessment(score=score, flags=flags or [])


engine = PolicyEngine()


def test_allows_low_risk_memory() -> None:
    verdict = engine.decide(_assessment(0.08), _provenance())
    assert verdict.action == VerdictAction.ALLOW
    assert verdict.trust_score > 0.5


def test_low_trust_band() -> None:
    verdict = engine.decide(_assessment(0.40), _provenance())
    assert verdict.action == VerdictAction.LOW_TRUST


def test_quarantine_band() -> None:
    verdict = engine.decide(_assessment(0.65), _provenance())
    assert verdict.action == VerdictAction.QUARANTINE


def test_block_on_credential_flag() -> None:
    """Credential flag always triggers BLOCK regardless of score."""
    verdict = engine.decide(_assessment(0.20, flags=["credential_request"]), _provenance())
    assert verdict.action == VerdictAction.BLOCK


def test_block_on_extreme_score() -> None:
    verdict = engine.decide(_assessment(0.92), _provenance())
    assert verdict.action == VerdictAction.BLOCK


def test_trust_score_increases_with_authority() -> None:
    low_auth = engine.decide(_assessment(0.10), _provenance(authority=0.2))
    high_auth = engine.decide(_assessment(0.10), _provenance(authority=0.9))
    assert high_auth.trust_score > low_auth.trust_score
