from __future__ import annotations

from apps.api.app.db.memory_repository import InMemoryMemoryRepository
from apps.api.app.models.api import MemoryWriteRequest, MemoryWriteResponse
from apps.api.app.services.claim_extractor import ClaimExtractor
from apps.api.app.services.contradiction_service import ContradictionService
from apps.api.app.services.policy_engine import PolicyEngine
from apps.api.app.services.provenance_service import ProvenanceService
from apps.api.app.services.quarantine_service import QuarantineService
from apps.api.app.services.risk_service import RiskService


class IngestService:
    """Orchestrates the full write pipeline for a single memory item.

    This is a thin coordinator that wires together individual services
    without duplicating the LangGraph state-machine logic in write_firewall.
    It is intended for direct programmatic use (e.g. connectors, seeds)
    rather than HTTP requests, which go through the firewall graph.
    """

    def __init__(
        self,
        repository: InMemoryMemoryRepository,
        claim_extractor: ClaimExtractor,
        provenance_service: ProvenanceService,
        contradiction_service: ContradictionService,
        risk_service: RiskService,
        policy_engine: PolicyEngine,
        quarantine_service: QuarantineService,
    ) -> None:
        self.repository = repository
        self.claim_extractor = claim_extractor
        self.provenance_service = provenance_service
        self.contradiction_service = contradiction_service
        self.risk_service = risk_service
        self.policy_engine = policy_engine
        self.quarantine_service = quarantine_service

    def ingest(self, request: MemoryWriteRequest) -> MemoryWriteResponse:
        """Run end-to-end ingest and return the stored memory with its verdict."""
        from apps.api.app.graphs.write_firewall import WriteFirewall

        firewall = WriteFirewall(
            repository=self.repository,
            claim_extractor=self.claim_extractor,
            provenance_service=self.provenance_service,
            contradiction_service=self.contradiction_service,
            risk_service=self.risk_service,
            policy_engine=self.policy_engine,
        )
        response = firewall.run(request)

        # Post-process: send quarantined memories to quarantine store
        from apps.api.app.models.verdict import VerdictAction

        if response.verdict.action == VerdictAction.QUARANTINE:
            self.quarantine_service.quarantine(response.memory)

        return response
