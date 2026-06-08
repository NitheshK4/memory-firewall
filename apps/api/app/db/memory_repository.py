from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone

from apps.api.app.db.vector import InMemoryVectorStore, VectorDocument
from apps.api.app.models.api import ReviewAction, ReviewDecision, StoredMemory
from apps.api.app.models.verdict import MemoryStatus


class InMemoryMemoryRepository:
    """In-memory memory store with optional semantic vector search.

    Pass a ``vector_store`` built by ``build_vector_store(settings)`` to
    enable real ``text-embedding-3-small`` similarity search.  Defaults to
    the keyword-overlap fallback.
    """

    def __init__(self, vector_store: InMemoryVectorStore | None = None) -> None:
        self._memories: dict[str, StoredMemory] = {}
        self._vector_store = vector_store or InMemoryVectorStore()

    def save(self, memory: StoredMemory) -> StoredMemory:
        stored = memory.model_copy(deep=True)
        self._memories[stored.memory_id] = stored
        # Index in vector store (skip blocked memories)
        if stored.status != MemoryStatus.BLOCKED:
            self._vector_store.add(
                VectorDocument(doc_id=stored.memory_id, text=stored.raw_content)
            )
        return stored.model_copy(deep=True)

    def get(self, memory_id: str) -> StoredMemory | None:
        memory = self._memories.get(memory_id)
        return memory.model_copy(deep=True) if memory else None

    def list_memories(self, status: MemoryStatus | None = None) -> list[StoredMemory]:
        items: Iterable[StoredMemory] = self._memories.values()
        if status is not None:
            items = (memory for memory in items if memory.status == status)
        return sorted(
            (memory.model_copy(deep=True) for memory in items),
            key=lambda memory: memory.created_at,
            reverse=True,
        )

    def list_quarantined(self) -> list[StoredMemory]:
        return self.list_memories(MemoryStatus.QUARANTINED)

    def query(self, query_text: str, limit: int = 5) -> list[tuple[StoredMemory, float]]:
        """Return the most similar memories, ranked by semantic or keyword similarity."""
        hits = self._vector_store.similarity_search(query_text, top_k=limit * 2)
        scored: list[tuple[StoredMemory, float]] = []
        for doc, sim_score in hits:
            memory = self._memories.get(doc.doc_id)
            if memory is None or memory.status == MemoryStatus.BLOCKED:
                continue
            # Blend similarity score with trust score
            combined = sim_score * 0.85 + memory.trust_score * 0.15
            scored.append((memory.model_copy(deep=True), min(combined, 1.0)))

        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:limit]

    def apply_review(self, memory_id: str, decision: ReviewDecision) -> StoredMemory | None:
        memory = self._memories.get(memory_id)
        if memory is None:
            return None

        if decision.action == ReviewAction.APPROVE:
            memory.status = MemoryStatus.ALLOWED
            memory.flags = [flag for flag in memory.flags if flag != "quarantined"]
            memory.flags.append(f"approved_by:{decision.reviewer}")
            memory.updated_at = datetime.now(timezone.utc)
            # Re-index now that it's approved
            self._vector_store.add(VectorDocument(doc_id=memory.memory_id, text=memory.raw_content))
        elif decision.action == ReviewAction.REJECT:
            memory.status = MemoryStatus.BLOCKED
            memory.flags.append(f"rejected_by:{decision.reviewer}")
            memory.updated_at = datetime.now(timezone.utc)
            self._vector_store.delete(memory.memory_id)
        elif decision.action == ReviewAction.EDIT:
            if decision.edited_content:
                memory.raw_content = decision.edited_content
            memory.status = MemoryStatus.ALLOWED
            memory.flags.append(f"edited_by:{decision.reviewer}")
            memory.updated_at = datetime.now(timezone.utc)
            self._vector_store.add(VectorDocument(doc_id=memory.memory_id, text=memory.raw_content))

        self._memories[memory_id] = memory
        return memory.model_copy(deep=True)

    def block(self, memory_id: str, actor: str = "api") -> StoredMemory | None:
        """Soft-delete a memory by marking it BLOCKED and removing it from the vector index.

        The record is retained in the store so the audit trail and review
        decisions remain intact; it simply stops appearing in retrievals.

        Returns the updated :class:`StoredMemory`, or ``None`` if not found.
        """
        memory = self._memories.get(memory_id)
        if memory is None:
            return None
        memory.status = MemoryStatus.BLOCKED
        memory.flags.append(f"blocked_by:{actor}")
        memory.updated_at = datetime.now(timezone.utc)
        self._vector_store.delete(memory_id)
        self._memories[memory_id] = memory
        return memory.model_copy(deep=True)


