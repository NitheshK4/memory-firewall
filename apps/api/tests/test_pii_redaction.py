import pytest
from apps.api.app.config import Settings
from apps.api.app.db.memory_repository import InMemoryMemoryRepository
from apps.api.app.graphs.write_firewall import WriteFirewall
from apps.api.app.models.api import MemoryWriteRequest
from apps.api.app.services.audit_service import AuditService
from apps.api.app.services.claim_extractor import ClaimExtractor
from apps.api.app.services.contradiction_service import ContradictionService
from apps.api.app.services.policy_engine import PolicyEngine
from apps.api.app.services.provenance_service import ProvenanceService
from apps.api.app.services.risk_service import RiskService
from packages.shared.utils.sanitise import redact_pii


def test_redact_pii_utility() -> None:
    """Test the redact_pii utility function directly on various types of PII."""
    # Test email redaction
    text = "Contact me at alice.smith@example.co.uk for details."
    redacted, types = redact_pii(text)
    assert redacted == "Contact me at [EMAIL_REDACTED] for details."
    assert "email" in types

    # Test phone redaction
    text = "Call me at +1-555-234-5678 or 555 123 4567."
    redacted, types = redact_pii(text)
    assert "[PHONE_REDACTED]" in redacted
    assert "phone" in types

    # Test secret redaction prefix style
    text = "The openai key is sk-A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6"
    redacted, types = redact_pii(text)
    assert redacted == "The openai key is [SECRET_REDACTED]"
    assert "secret" in types

    # Test secret redaction assignment style
    text = "api_key = 'abcdef1234567890abcdef1234567890'"
    redacted, types = redact_pii(text)
    assert redacted == "api_key = '[SECRET_REDACTED]'"
    assert "secret" in types

    # Test combined redaction
    text = "Email bob@gmail.com or call 555-555-5555. API token is token-xyz1234567890123"
    redacted, types = redact_pii(text)
    assert "[EMAIL_REDACTED]" in redacted
    assert "[PHONE_REDACTED]" in redacted
    assert "[SECRET_REDACTED]" in redacted
    assert set(types) == {"email", "phone", "secret"}


def build_test_firewall(enable_redaction: bool, audit_service: AuditService) -> WriteFirewall:
    settings = Settings(enable_pii_redaction=enable_redaction)
    repository = InMemoryMemoryRepository()
    return WriteFirewall(
        repository=repository,
        claim_extractor=ClaimExtractor(settings),
        provenance_service=ProvenanceService(),
        contradiction_service=ContradictionService(),
        risk_service=RiskService(settings),
        policy_engine=PolicyEngine(),
        audit_service=audit_service,
        settings=settings,
    )


def test_write_firewall_redacts_pii_and_audits() -> None:
    """Test that WriteFirewall redacts PII when enabled, and logs to AuditService."""
    audit_svc = AuditService()
    firewall = build_test_firewall(enable_redaction=True, audit_service=audit_svc)

    request = MemoryWriteRequest(
        content="User data: contact support@company.com or 555-123-4567. Key: sk-abcdef12345678901234",
        source_type="human",
        actor="ops_lead",
    )

    response = firewall.run(request)

    # Content stored in repository must be redacted
    assert "[EMAIL_REDACTED]" in response.memory.raw_content
    assert "[PHONE_REDACTED]" in response.memory.raw_content
    assert "[SECRET_REDACTED]" in response.memory.raw_content
    assert "support@company.com" not in response.memory.raw_content

    # Audit log must contain the redaction event
    logs = audit_svc.get_log(memory_id=response.memory.memory_id)
    redaction_entries = [entry for entry in logs if entry["event"] == "pii_redacted"]
    assert len(redaction_entries) == 1
    detail = redaction_entries[0]["detail"]
    assert "types=" in detail
    assert "email" in detail
    assert "phone" in detail
    assert "secret" in detail


def test_write_firewall_does_not_redact_when_disabled() -> None:
    """Test that WriteFirewall does not redact PII when disabled, and does not audit."""
    audit_svc = AuditService()
    firewall = build_test_firewall(enable_redaction=False, audit_service=audit_svc)

    raw_text = "User data: contact support@company.com or 555-123-4567."
    request = MemoryWriteRequest(
        content=raw_text,
        source_type="human",
        actor="ops_lead",
    )

    response = firewall.run(request)

    # Content must remain unredacted
    assert response.memory.raw_content == raw_text

    # Audit log must NOT contain redaction entries
    logs = audit_svc.get_log(memory_id=response.memory.memory_id)
    redaction_entries = [entry for entry in logs if entry["event"] == "pii_redacted"]
    assert len(redaction_entries) == 0
