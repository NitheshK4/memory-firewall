from apps.api.app.db.memory_repository import InMemoryMemoryRepository
from apps.api.app.models.api import ReviewDecision, StoredMemory


class QuarantineService:
    def __init__(self, repository: InMemoryMemoryRepository) -> None:
        self.repository = repository

    def list_quarantined(self) -> list[StoredMemory]:
        return self.repository.list_quarantined()

    def apply_decision(self, memory_id: str, decision: ReviewDecision) -> StoredMemory | None:
        return self.repository.apply_review(memory_id, decision)

