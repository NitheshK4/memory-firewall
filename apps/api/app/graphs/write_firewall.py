from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from apps.api.app.config import Settings, get_settings
from apps.api.app.db.memory_repository import InMemoryMemoryRepository
from apps.api.app.models.api import MemoryWriteRequest, MemoryWriteResponse, StoredMemory
from apps.api.app.models.claim import MemoryClaim
from apps.api.app.models.provenance import ProvenanceRecord
from apps.api.app.models.verdict import MemoryStatus, MemoryVerdict, RiskAssessment, VerdictAction
from apps.api.app.services.audit_service import AuditService
from apps.api.app.services.claim_extractor import ClaimExtractor
from apps.api.app.services.contradiction_service import ContradictionService
from apps.api.app.services.policy_engine import PolicyEngine
from apps.api.app.services.provenance_service import ProvenanceService
from apps.api.app.services.risk_service import RiskService
from packages.shared.utils.sanitise import redact_pii


class WriteState(TypedDict, total=False):
    request: MemoryWriteRequest
    provenance: ProvenanceRecord
    claims: list[MemoryClaim]
    similar_memories: list[StoredMemory]
    contradictions: list[str]
    risk: RiskAssessment
    verdict: MemoryVerdict
    stored_memory: StoredMemory
    redacted_types: list[str]


class WriteFirewall:
    def __init__(
        self,
        repository: InMemoryMemoryRepository,
        claim_extractor: ClaimExtractor,
        provenance_service: ProvenanceService,
        contradiction_service: ContradictionService,
        risk_service: RiskService,
        policy_engine: PolicyEngine,
        audit_service: AuditService | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.repository = repository
        self.claim_extractor = claim_extractor
        self.provenance_service = provenance_service
        self.contradiction_service = contradiction_service
        self.risk_service = risk_service
        self.policy_engine = policy_engine
        self.audit_service = audit_service
        self.settings = settings or get_settings()
        self.graph = self._compile()

    def run(self, request: MemoryWriteRequest) -> MemoryWriteResponse:
        result = self.graph.invoke({"request": request})
        return MemoryWriteResponse(
            memory=result["stored_memory"],
            verdict=result["verdict"],
        )

    def _compile(self):
        graph = StateGraph(WriteState)
        graph.add_node("redact_pii", self.redact_pii_node)
        graph.add_node("attach_provenance", self.attach_provenance)
        graph.add_node("extract_claims", self.extract_claims)
        graph.add_node("search_similar", self.search_similar)
        graph.add_node("check_contradictions", self.check_contradictions)
        graph.add_node("score_risk", self.score_risk)
        graph.add_node("decide_policy", self.decide_policy)
        graph.add_node("persist", self.persist)
        
        graph.add_edge(START, "redact_pii")
        graph.add_edge("redact_pii", "attach_provenance")
        graph.add_edge("attach_provenance", "extract_claims")
        graph.add_edge("extract_claims", "search_similar")
        graph.add_edge("search_similar", "check_contradictions")
        graph.add_edge("check_contradictions", "score_risk")
        graph.add_edge("score_risk", "decide_policy")
        graph.add_edge("decide_policy", "persist")
        graph.add_edge("persist", END)
        return graph.compile()

    def redact_pii_node(self, state: WriteState) -> WriteState:
        request = state["request"]
        if self.settings.enable_pii_redaction:
            redacted_content, redacted_types = redact_pii(request.content)
            if redacted_types:
                new_request = request.model_copy(update={"content": redacted_content})
                return {"request": new_request, "redacted_types": redacted_types}
        return {"request": request, "redacted_types": []}

    def attach_provenance(self, state: WriteState) -> WriteState:
        return {"provenance": self.provenance_service.build(state["request"])}

    def extract_claims(self, state: WriteState) -> WriteState:
        return {"claims": self.claim_extractor.extract(state["request"].content)}

    def search_similar(self, state: WriteState) -> WriteState:
        similar = [memory for memory, _ in self.repository.query(state["request"].content, limit=6)]
        return {"similar_memories": similar}

    def check_contradictions(self, state: WriteState) -> WriteState:
        contradictions = self.contradiction_service.analyze(
            state["claims"],
            state.get("similar_memories", []),
        )
        return {"contradictions": contradictions}

    def score_risk(self, state: WriteState) -> WriteState:
        is_burst = False
        if self.audit_service and state["request"].actor:
            is_burst = self.audit_service.check_burst_write(state["request"].actor)

        assessment = self.risk_service.assess(
            content=state["request"].content,
            claims=state["claims"],
            provenance=state["provenance"],
            contradictions=state.get("contradictions", []),
            is_burst=is_burst,
        )
        return {"risk": assessment}

    def decide_policy(self, state: WriteState) -> WriteState:
        return {"verdict": self.policy_engine.decide(state["risk"], state["provenance"], state["request"].content)}

    def persist(self, state: WriteState) -> WriteState:
        status = {
            VerdictAction.ALLOW: MemoryStatus.ALLOWED,
            VerdictAction.LOW_TRUST: MemoryStatus.LOW_TRUST,
            VerdictAction.QUARANTINE: MemoryStatus.QUARANTINED,
            VerdictAction.BLOCK: MemoryStatus.BLOCKED,
        }[state["verdict"].action]

        stored = StoredMemory(
            raw_content=state["request"].content,
            claims=state["claims"],
            provenance=state["provenance"],
            status=status,
            trust_score=state["verdict"].trust_score,
            contradictions=state.get("contradictions", []),
            flags=state["risk"].flags,
            tags=state["request"].tags,
        )
        saved = self.repository.save(stored)

        if self.audit_service:
            self.audit_service.log_write(saved)
            self.audit_service.log_verdict(
                saved.memory_id,
                action=state["verdict"].action,
            )
            redacted_types = state.get("redacted_types", [])
            if redacted_types:
                self.audit_service.log_redaction(
                    saved.memory_id,
                    actor=saved.provenance.actor,
                    redacted_types=redacted_types,
                )

        return {"stored_memory": saved}


