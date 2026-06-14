from dataclasses import dataclass
from functools import lru_cache

from apps.api.app.config import Settings, get_settings
from apps.api.app.db.memory_repository import InMemoryMemoryRepository
from apps.api.app.db.vector import build_vector_store
from apps.api.app.graphs.read_firewall import ReadFirewall
from apps.api.app.graphs.write_firewall import WriteFirewall
from apps.api.app.services.audit_service import AuditService
from apps.api.app.services.claim_extractor import ClaimExtractor
from apps.api.app.services.contradiction_service import ContradictionService
from apps.api.app.services.policy_engine import PolicyEngine
from apps.api.app.services.provenance_service import ProvenanceService
from apps.api.app.services.quarantine_service import QuarantineService
from apps.api.app.services.retrieval_service import RetrievalService
from apps.api.app.services.risk_service import RiskService


@dataclass
class ServiceContainer:
    settings: Settings
    repository: InMemoryMemoryRepository
    write_firewall: WriteFirewall
    read_firewall: ReadFirewall
    quarantine_service: QuarantineService
    audit_service: AuditService


@lru_cache
def get_container() -> ServiceContainer:
    settings = get_settings()

    # Build vector store — real embeddings when USE_OPENAI=true, keyword otherwise
    vector_store = build_vector_store(settings)

    # Build audit_service first so the repository can log dedup-skip events
    audit_service = AuditService(
        burst_window_seconds=settings.burst_window_seconds,
        burst_max_writes=settings.burst_max_writes,
    )
    repository = InMemoryMemoryRepository(vector_store=vector_store, audit_service=audit_service)

    claim_extractor = ClaimExtractor(settings)
    provenance_service = ProvenanceService()
    contradiction_service = ContradictionService()
    risk_service = RiskService(settings=settings)   # pass settings for LLM scoring
    policy_engine = PolicyEngine()
    retrieval_service = RetrievalService(repository, audit_service=audit_service)
    quarantine_service = QuarantineService(repository, audit_service=audit_service)

    write_firewall = WriteFirewall(
        repository=repository,
        claim_extractor=claim_extractor,
        provenance_service=provenance_service,
        contradiction_service=contradiction_service,
        risk_service=risk_service,
        policy_engine=policy_engine,
        audit_service=audit_service,
    )
    read_firewall = ReadFirewall(retrieval_service)
    return ServiceContainer(
        settings=settings,
        repository=repository,
        write_firewall=write_firewall,
        read_firewall=read_firewall,
        quarantine_service=quarantine_service,
        audit_service=audit_service,
    )


