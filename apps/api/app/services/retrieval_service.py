from apps.api.app.db.memory_repository import InMemoryMemoryRepository
from apps.api.app.models.api import RetrievalRequest, RetrievalResponse, RetrievalResult, StoredMemory
from apps.api.app.models.verdict import MemoryStatus


class RetrievalService:
    def __init__(self, repository: InMemoryMemoryRepository) -> None:
        self.repository = repository

    def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        candidates = self.repository.query(request.query, limit=request.max_results * 3)
        results: list[RetrievalResult] = []
        for memory, similarity in candidates:
            if memory.status in {MemoryStatus.BLOCKED, MemoryStatus.QUARANTINED}:
                continue
            results.append(
                self._build_result(memory, similarity)
            )
            if len(results) >= request.max_results:
                break

        return RetrievalResponse(query=request.query, results=results)

    @staticmethod
    def _build_result(memory: StoredMemory, similarity: float) -> RetrievalResult:
        reasons = [
            f"similarity:{similarity:.2f}",
            f"trust:{memory.trust_score:.2f}",
            f"status:{memory.status.value}",
        ]
        if memory.flags:
            reasons.append(f"flags:{', '.join(memory.flags[:3])}")

        return RetrievalResult(
            memory_id=memory.memory_id,
            raw_content=memory.raw_content,
            claims=memory.claims,
            trust_score=memory.trust_score,
            status=memory.status,
            reasons=reasons,
        )

