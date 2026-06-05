from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from apps.api.app.models.api import ReviewDecision, StoredMemory
from apps.api.app.models.verdict import VerdictAction


class AuditEntry:
    """Immutable record of a single auditable event in the firewall."""

    __slots__ = ("entry_id", "memory_id", "event", "actor", "detail", "occurred_at")

    def __init__(
        self,
        memory_id: str,
        event: str,
        actor: str = "system",
        detail: str = "",
    ) -> None:
        self.entry_id: str = str(uuid4())
        self.memory_id: str = memory_id
        self.event: str = event
        self.actor: str = actor
        self.detail: str = detail
        self.occurred_at: datetime = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "memory_id": self.memory_id,
            "event": self.event,
            "actor": self.actor,
            "detail": self.detail,
            "occurred_at": self.occurred_at.isoformat(),
        }


class AuditService:
    """In-memory audit log for firewall events.

    Records every significant action (write, verdict, review, quarantine)
    keyed by memory_id for quick retrieval.
    """

    def __init__(self) -> None:
        self._log: list[AuditEntry] = []

    # ------------------------------------------------------------------ #
    # Recording helpers
    # ------------------------------------------------------------------ #

    def log_write(self, memory: StoredMemory) -> None:
        self._append(
            memory.memory_id,
            event="memory_written",
            actor=memory.provenance.actor,
            detail=f"status={memory.status} trust={memory.trust_score:.2f}",
        )

    def log_verdict(self, memory_id: str, action: VerdictAction, actor: str = "firewall") -> None:
        self._append(memory_id, event=f"verdict:{action}", actor=actor)

    def log_review(self, memory_id: str, decision: ReviewDecision) -> None:
        self._append(
            memory_id,
            event=f"review:{decision.action}",
            actor=decision.reviewer,
            detail=f"edited={decision.edited_content is not None}",
        )

    def log_quarantine(self, memory_id: str) -> None:
        self._append(memory_id, event="quarantined", actor="quarantine_service")

    def log_retrieval(self, memory_id: str, actor: str, suppressed: bool = False) -> None:
        event = "retrieval_suppressed" if suppressed else "retrieval_served"
        self._append(memory_id, event=event, actor=actor)

    # ------------------------------------------------------------------ #
    # Query helpers
    # ------------------------------------------------------------------ #

    def get_log(self, memory_id: str | None = None) -> list[dict]:
        entries = self._log if memory_id is None else [e for e in self._log if e.memory_id == memory_id]
        return [e.to_dict() for e in entries]

    def _append(self, memory_id: str, *, event: str, actor: str = "system", detail: str = "") -> None:
        self._log.append(AuditEntry(memory_id=memory_id, event=event, actor=actor, detail=detail))
