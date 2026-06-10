from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from apps.api.app.models.api import ReviewDecision, StoredMemory
from apps.api.app.models.verdict import VerdictAction

# Default burst-detection thresholds (can be overridden on construction).
_DEFAULT_BURST_WINDOW_SECONDS = 60
_DEFAULT_BURST_MAX_WRITES = 10


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

    Also tracks write activity per actor so callers can detect burst-write
    patterns that may indicate a memory-flooding or poisoning attempt.
    """

    def __init__(
        self,
        burst_window_seconds: int = _DEFAULT_BURST_WINDOW_SECONDS,
        burst_max_writes: int = _DEFAULT_BURST_MAX_WRITES,
    ) -> None:
        self._log: list[AuditEntry] = []
        self._burst_window = timedelta(seconds=burst_window_seconds)
        self._burst_max_writes = burst_max_writes

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

    def log_deletion(self, memory_id: str, actor: str, reason: str = "") -> None:
        """Record a soft-delete (block) event so the full lifecycle is auditable."""
        self._append(
            memory_id,
            event="memory_deleted",
            actor=actor,
            detail=reason,
        )

    # ------------------------------------------------------------------ #
    # Burst detection
    # ------------------------------------------------------------------ #

    def check_burst_write(self, actor: str) -> bool:
        """Return True if *actor* has exceeded the burst write threshold.

        Counts ``memory_written`` events attributed to *actor* within the
        configured rolling window.  Callers should treat a ``True`` return
        as a signal to increase risk scoring or quarantine the incoming write.
        """
        now = datetime.now(timezone.utc)
        cutoff = now - self._burst_window
        recent_writes = [
            entry
            for entry in self._log
            if entry.actor == actor
            and entry.event == "memory_written"
            and entry.occurred_at >= cutoff
        ]
        return len(recent_writes) >= self._burst_max_writes

    def burst_write_count(self, actor: str) -> int:
        """Return the number of memory writes by *actor* in the current window."""
        now = datetime.now(timezone.utc)
        cutoff = now - self._burst_window
        return sum(
            1
            for entry in self._log
            if entry.actor == actor
            and entry.event == "memory_written"
            and entry.occurred_at >= cutoff
        )

    # ------------------------------------------------------------------ #
    # Query helpers
    # ------------------------------------------------------------------ #

    def get_log(self, memory_id: str | None = None) -> list[dict]:
        entries = self._log if memory_id is None else [e for e in self._log if e.memory_id == memory_id]
        return [e.to_dict() for e in entries]

    def _append(self, memory_id: str, *, event: str, actor: str = "system", detail: str = "") -> None:
        self._log.append(AuditEntry(memory_id=memory_id, event=event, actor=actor, detail=detail))
