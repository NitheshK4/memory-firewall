from __future__ import annotations

from apps.api.app.db.memory_repository import InMemoryMemoryRepository
from apps.api.app.models.api import ReviewDecision, StoredMemory
from apps.api.app.models.verdict import MemoryStatus


class QuarantineService:
    def __init__(
        self,
        repository: InMemoryMemoryRepository,
        audit_service=None,  # AuditService | None — avoid circular import
    ) -> None:
        self.repository = repository
        self._audit = audit_service

    def quarantine(self, memory: StoredMemory) -> None:
        """Mark *memory* as quarantined in the repository and record the event."""
        # Update status in store if not already quarantined
        if memory.status != MemoryStatus.QUARANTINED:
            memory.status = MemoryStatus.QUARANTINED
            self.repository.save(memory)
        if self._audit:
            self._audit.log_quarantine(memory.memory_id)

    def list_quarantined(self) -> list[StoredMemory]:
        return self.repository.list_quarantined()

    def apply_decision(self, memory_id: str, decision: ReviewDecision) -> StoredMemory | None:
        return self.repository.apply_review(memory_id, decision)
