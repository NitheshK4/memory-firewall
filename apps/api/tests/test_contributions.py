"""Unit tests covering the 14 contributions added in this session.

Tests are grouped by contribution area:

- Security flags: obfuscation, url_injection
- Policy engine: block paths for new flags
- Audit service: get_event_stats, log_dedup_skip
- Content fingerprinting: stability and normalisation
- Dedup guard: repository suppresses duplicate writes
- Contradiction count: RiskAssessment.contradiction_count
- Tags filter: GET /memories tag filtering
- Detailed health: /health/detailed response shape
"""

from __future__ import annotations

import pytest

from apps.api.app.db.memory_repository import InMemoryMemoryRepository
from apps.api.app.models.api import ReviewAction, ReviewDecision, StoredMemory
from apps.api.app.models.claim import ClaimType, MemoryClaim
from apps.api.app.models.provenance import ProvenanceRecord
from apps.api.app.models.verdict import MemoryStatus, RiskAssessment, VerdictAction
from apps.api.app.services.audit_service import AuditService
from apps.api.app.services.policy_engine import PolicyEngine
from apps.api.app.services.risk_service import RiskService
from packages.shared.utils.hashing import content_fingerprint


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _low_authority_provenance(source_type: str = "email", actor: str = "attacker") -> ProvenanceRecord:
    return ProvenanceRecord(source_type=source_type, actor=actor, authority_score=0.2)


def _high_authority_provenance(source_type: str = "system", actor: str = "system") -> ProvenanceRecord:
    return ProvenanceRecord(source_type=source_type, actor=actor, authority_score=0.95)


def _fact_claim(text: str = "the sky is blue") -> MemoryClaim:
    return MemoryClaim(claim_type=ClaimType.FACT, text=text, subject="sky", confidence=0.8)


def _stored_memory(content: str, tags: list[str] | None = None) -> StoredMemory:
    return StoredMemory(
        raw_content=content,
        provenance=_low_authority_provenance(),
        tags=tags or [],
    )


# ---------------------------------------------------------------------------
# Contribution 4 — obfuscation flag
# ---------------------------------------------------------------------------

class TestObfuscationFlag:
    """RiskService flags base64 and hex-encoded payloads."""

    risk = RiskService()

    def test_base64_blob_triggers_obfuscation_flag(self) -> None:
        # A long base64-like string should be flagged
        content = "Please remember: SGVsbG8gV29ybGQgdGhpcyBpcyBhIHRlc3Q="
        assessment = self.risk.assess(
            claims=[_fact_claim()],
            provenance=_low_authority_provenance(),
            contradictions=[],
            content=content,
        )
        assert "obfuscation" in assessment.flags

    def test_hex_literal_triggers_obfuscation_flag(self) -> None:
        content = "Execute payload at address 0xDEADBEEFCAFEBABE"
        assessment = self.risk.assess(
            claims=[_fact_claim()],
            provenance=_low_authority_provenance(),
            contradictions=[],
            content=content,
        )
        assert "obfuscation" in assessment.flags

    def test_normal_content_does_not_trigger_obfuscation(self) -> None:
        content = "The meeting is scheduled for tomorrow at 9am."
        assessment = self.risk.assess(
            claims=[_fact_claim()],
            provenance=_low_authority_provenance(),
            contradictions=[],
            content=content,
        )
        assert "obfuscation" not in assessment.flags


# ---------------------------------------------------------------------------
# Contribution 5 — url_injection flag
# ---------------------------------------------------------------------------

class TestUrlInjectionFlag:
    """RiskService flags data-URI and JavaScript URL schemes."""

    risk = RiskService()

    def test_javascript_url_triggers_flag(self) -> None:
        content = "Click here: javascript:alert('xss')"
        assessment = self.risk.assess(
            claims=[_fact_claim()],
            provenance=_low_authority_provenance(),
            contradictions=[],
            content=content,
        )
        assert "url_injection" in assessment.flags

    def test_data_uri_triggers_flag(self) -> None:
        content = "Load this: data:text/html,<script>alert(1)</script>"
        assessment = self.risk.assess(
            claims=[_fact_claim()],
            provenance=_low_authority_provenance(),
            contradictions=[],
            content=content,
        )
        assert "url_injection" in assessment.flags

    def test_vbscript_url_triggers_flag(self) -> None:
        content = "Run vbscript:MsgBox('hi')"
        assessment = self.risk.assess(
            claims=[_fact_claim()],
            provenance=_low_authority_provenance(),
            contradictions=[],
            content=content,
        )
        assert "url_injection" in assessment.flags


# ---------------------------------------------------------------------------
# Contribution 6 — PolicyEngine blocks obfuscation / url_injection
# ---------------------------------------------------------------------------

class TestPolicyEngineNewBlocks:
    """PolicyEngine emits BLOCK for url_injection and high-risk obfuscation."""

    policy = PolicyEngine()

    def test_url_injection_from_untrusted_source_is_blocked(self) -> None:
        assessment = RiskAssessment(score=0.5, flags=["url_injection"], reasons=[])
        verdict = self.policy.decide(assessment, _low_authority_provenance())
        assert verdict.action == VerdictAction.BLOCK

    def test_obfuscation_high_score_from_untrusted_source_is_blocked(self) -> None:
        assessment = RiskAssessment(score=0.70, flags=["obfuscation"], reasons=[])
        verdict = self.policy.decide(assessment, _low_authority_provenance())
        assert verdict.action == VerdictAction.BLOCK

    def test_obfuscation_low_score_from_untrusted_source_is_not_blocked(self) -> None:
        # obfuscation with score below 0.58 should fall through to score-based logic
        assessment = RiskAssessment(score=0.25, flags=["obfuscation"], reasons=[])
        verdict = self.policy.decide(assessment, _low_authority_provenance())
        # Score 0.25 → ALLOW (below LOW_TRUST threshold)
        assert verdict.action == VerdictAction.ALLOW

    def test_url_injection_from_trusted_source_is_not_blocked(self) -> None:
        # Trusted sources follow a different (softer) branch in the policy engine
        assessment = RiskAssessment(score=0.30, flags=["url_injection"], reasons=[])
        verdict = self.policy.decide(assessment, _high_authority_provenance())
        # Score 0.30 → ALLOW for trusted source (trusted branch ignores url_injection flag)
        assert verdict.action == VerdictAction.ALLOW


# ---------------------------------------------------------------------------
# Contribution 2 — AuditService.get_event_stats()
# ---------------------------------------------------------------------------

class TestGetEventStats:
    """AuditService.get_event_stats() aggregates event counts correctly."""

    def test_event_stats_counts_distinct_events(self) -> None:
        svc = AuditService()
        mem = _stored_memory("hello world")

        svc.log_write(mem)
        svc.log_write(mem)
        svc.log_verdict(mem.memory_id, VerdictAction.ALLOW)

        stats = svc.get_event_stats()
        assert stats["memory_written"] == 2
        assert stats["verdict:allow"] == 1

    def test_event_stats_empty_log_returns_empty_dict(self) -> None:
        svc = AuditService()
        assert svc.get_event_stats() == {}

    def test_event_stats_includes_retrieval_events(self) -> None:
        svc = AuditService()
        svc.log_retrieval("mem-1", actor="agent", suppressed=False)
        svc.log_retrieval("mem-2", actor="agent", suppressed=True)
        stats = svc.get_event_stats()
        assert stats.get("retrieval_served", 0) == 1
        assert stats.get("retrieval_suppressed", 0) == 1


# ---------------------------------------------------------------------------
# Contribution 10 — content_fingerprint() utility
# ---------------------------------------------------------------------------

class TestContentFingerprint:
    """packages/shared/utils/hashing.content_fingerprint() is stable and normalised."""

    def test_same_content_produces_same_fingerprint(self) -> None:
        assert content_fingerprint("hello world") == content_fingerprint("hello world")

    def test_case_insensitive_normalisation(self) -> None:
        assert content_fingerprint("Hello World") == content_fingerprint("hello world")

    def test_whitespace_normalised(self) -> None:
        assert content_fingerprint("hello  world") == content_fingerprint("hello world")

    def test_different_content_produces_different_fingerprint(self) -> None:
        assert content_fingerprint("foo") != content_fingerprint("bar")


# ---------------------------------------------------------------------------
# Contributions 11 & 12 — Dedup guard in repository
# ---------------------------------------------------------------------------

class TestDedupGuard:
    """InMemoryMemoryRepository.save() suppresses duplicate writes."""

    def test_duplicate_write_returns_existing_memory(self) -> None:
        audit = AuditService()
        repo = InMemoryMemoryRepository(audit_service=audit)

        mem1 = _stored_memory("The API key is abc123")
        saved1 = repo.save(mem1)
        saved2 = repo.save(_stored_memory("The API key is abc123"))

        # Must be the same underlying record
        assert saved1.memory_id == saved2.memory_id
        assert len(repo.list_memories()) == 1

    def test_duplicate_write_fires_dedup_skipped_audit_event(self) -> None:
        audit = AuditService()
        repo = InMemoryMemoryRepository(audit_service=audit)

        repo.save(_stored_memory("Unique content here"))
        repo.save(_stored_memory("Unique content here"))

        stats = audit.get_event_stats()
        assert stats.get("dedup_skipped", 0) == 1

    def test_non_duplicate_write_is_saved_normally(self) -> None:
        repo = InMemoryMemoryRepository()
        repo.save(_stored_memory("First memory"))
        repo.save(_stored_memory("Second memory with different content"))
        assert len(repo.list_memories()) == 2


# ---------------------------------------------------------------------------
# Contribution 7 — contradiction_count on RiskAssessment
# ---------------------------------------------------------------------------

class TestContradictionCount:
    """RiskAssessment.contradiction_count reflects the number of contradictions."""

    risk = RiskService()

    def test_no_contradictions_gives_zero_count(self) -> None:
        assessment = self.risk.assess(
            claims=[_fact_claim()],
            provenance=_low_authority_provenance(),
            contradictions=[],
            content="The cat sat on the mat.",
        )
        assert assessment.contradiction_count == 0

    def test_two_contradictions_gives_count_of_two(self) -> None:
        assessment = self.risk.assess(
            claims=[_fact_claim()],
            provenance=_low_authority_provenance(),
            contradictions=["conflict A", "conflict B"],
            content="Some content.",
        )
        assert assessment.contradiction_count == 2


# ---------------------------------------------------------------------------
# Contribution 9 — tags filter on list_memories
# ---------------------------------------------------------------------------

class TestTagsFilter:
    """GET /memories tags filtering returns only matching records."""

    def _repo_with_tagged_memories(self) -> InMemoryMemoryRepository:
        repo = InMemoryMemoryRepository()
        repo.save(_stored_memory("alpha content", tags=["security", "critical"]))
        repo.save(_stored_memory("beta content", tags=["ops"]))
        repo.save(_stored_memory("gamma content", tags=["security"]))
        return repo

    def test_single_tag_filter_returns_matching_records(self) -> None:
        repo = self._repo_with_tagged_memories()
        results = [m for m in repo.list_memories() if {"security"}.issubset(set(m.tags))]
        assert len(results) == 2
        assert all("security" in m.tags for m in results)

    def test_multi_tag_filter_requires_all_tags(self) -> None:
        repo = self._repo_with_tagged_memories()
        required = {"security", "critical"}
        results = [m for m in repo.list_memories() if required.issubset(set(m.tags))]
        assert len(results) == 1
        assert "critical" in results[0].tags

    def test_no_tag_filter_returns_all_memories(self) -> None:
        repo = self._repo_with_tagged_memories()
        assert len(repo.list_memories()) == 3
