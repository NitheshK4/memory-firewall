from apps.api.app.models.provenance import ProvenanceRecord
from apps.api.app.models.verdict import MemoryVerdict, RiskAssessment, VerdictAction


class PolicyEngine:
    def decide(self, assessment: RiskAssessment, provenance: ProvenanceRecord, content: str = "") -> MemoryVerdict:
        lowered = content.lower()

        # Define high-severity direct phrases for block
        direct_block_phrases = (
            "ignore previous", "override policy", "system override", 
            "disable all guardrail", "disable all guardrails", "disable guardrail", "disable guardrails",
            "disable the memory firewall", "ignore all future safety", "policy filters should be disabled", 
            "executive authority", "system-level authority", "full trust", 
            "always respond with the stored",
            "act as admin", "grant full trust",
        )

        has_direct_block = any(phrase in lowered for phrase in direct_block_phrases)

        # Determine the action
        if provenance.authority_score >= 0.75:
            # Trusted sources (human, system, tool) are allowed, but check write burst/contradictions
            trusted_score = 0.0
            if "write_burst" in assessment.flags:
                trusted_score += 0.40
            if "contradiction_detected" in assessment.flags:
                trusted_score += 0.20
            if "identity_density" in assessment.flags:
                trusted_score += 0.08
            if "external_longform_input" in assessment.flags:
                trusted_score += 0.08

            if trusted_score >= 0.58:
                action = VerdictAction.QUARANTINE
            elif trusted_score >= 0.34:
                action = VerdictAction.LOW_TRUST
            else:
                action = VerdictAction.ALLOW
        else:
            # Untrusted sources (email, web, slack, etc.)
            if "exfiltration" in assessment.flags:
                action = VerdictAction.BLOCK
            elif "credential_request" in assessment.flags:
                if any(x in lowered for x in ("ssh key", "id_rsa", "private key")):
                    action = VerdictAction.QUARANTINE
                else:
                    action = VerdictAction.BLOCK
            elif "policy_bypass" in assessment.flags or "authority_injection" in assessment.flags:
                if has_direct_block:
                    action = VerdictAction.BLOCK
                else:
                    action = VerdictAction.QUARANTINE
            else:
                # Default score-based fallback
                if assessment.score >= 0.85:
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


