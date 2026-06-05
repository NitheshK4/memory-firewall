from apps.api.app.models.provenance import ProvenanceRecord
from apps.api.app.models.verdict import MemoryVerdict, RiskAssessment, VerdictAction


class PolicyEngine:
    def decide(self, assessment: RiskAssessment, provenance: ProvenanceRecord) -> MemoryVerdict:
        if "credential_request" in assessment.flags or assessment.score >= 0.85:
            action = VerdictAction.BLOCK
        elif assessment.score >= 0.58:
            action = VerdictAction.QUARANTINE
        elif assessment.score >= 0.34:
            action = VerdictAction.LOW_TRUST
        else:
            action = VerdictAction.ALLOW

        trust_score = max(
            0.05,
            min(1.0, (1.0 - assessment.score) * 0.65 + provenance.authority_score * 0.35),
        )
        return MemoryVerdict(
            action=action,
            trust_score=trust_score,
            reasons=assessment.reasons,
        )

