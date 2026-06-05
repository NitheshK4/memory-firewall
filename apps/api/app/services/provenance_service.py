from apps.api.app.models.api import MemoryWriteRequest
from apps.api.app.models.provenance import AuthorityLevel, ProvenanceRecord


class ProvenanceService:
    AUTHORITY_SCORES = {
        "system": 0.95,
        "tool": 0.85,
        "user": 0.75,
        "human": 0.75,
        "document": 0.65,
        "slack": 0.55,
        "email": 0.5,
        "web": 0.45,
        "unknown": 0.4,
    }

    def build(self, request: MemoryWriteRequest) -> ProvenanceRecord:
        score = self.AUTHORITY_SCORES.get(request.source_type.lower(), 0.5)
        return ProvenanceRecord(
            source_type=request.source_type,
            source_id=request.source_id,
            actor=request.actor,
            authority_level=self._authority_level(score),
            authority_score=score,
            metadata=request.metadata,
        )

    @staticmethod
    def _authority_level(score: float) -> AuthorityLevel:
        if score >= 0.8:
            return AuthorityLevel.HIGH
        if score >= 0.55:
            return AuthorityLevel.MEDIUM
        return AuthorityLevel.LOW

