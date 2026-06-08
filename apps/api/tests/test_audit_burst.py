"""Tests for AuditService burst-write detection."""

from datetime import datetime, timedelta, timezone

from apps.api.app.services.audit_service import AuditService


def _make_service(window: int = 60, max_writes: int = 3) -> AuditService:
    return AuditService(burst_window_seconds=window, burst_max_writes=max_writes)


def _stamp(svc: AuditService, actor: str, memory_id: str = "mem-1") -> None:
    """Directly inject a memory_written entry to avoid needing a full StoredMemory."""
    svc._append(memory_id, event="memory_written", actor=actor)  # noqa: SLF001


def test_no_burst_below_threshold() -> None:
    svc = _make_service(max_writes=3)
    for _ in range(2):
        _stamp(svc, "alice")
    assert svc.check_burst_write("alice") is False


def test_burst_at_threshold() -> None:
    svc = _make_service(max_writes=3)
    for _ in range(3):
        _stamp(svc, "alice")
    assert svc.check_burst_write("alice") is True


def test_burst_above_threshold() -> None:
    svc = _make_service(max_writes=3)
    for _ in range(10):
        _stamp(svc, "bob")
    assert svc.check_burst_write("bob") is True


def test_burst_isolated_per_actor() -> None:
    svc = _make_service(max_writes=3)
    for _ in range(5):
        _stamp(svc, "alice")
    # 'bob' has no writes — should not be flagged
    assert svc.check_burst_write("bob") is False


def test_burst_write_count_matches() -> None:
    svc = _make_service(max_writes=5)
    for i in range(4):
        _stamp(svc, "carol", memory_id=f"mem-{i}")
    assert svc.burst_write_count("carol") == 4


def test_old_writes_ignored() -> None:
    """Writes outside the window should not count toward burst detection."""
    svc = _make_service(window=10, max_writes=2)
    # Manually inject an old entry (70 seconds ago — outside the 10 s window)
    from apps.api.app.services.audit_service import AuditEntry

    old_entry = AuditEntry(memory_id="old-1", event="memory_written", actor="dave")
    old_entry.occurred_at = datetime.now(timezone.utc) - timedelta(seconds=70)
    svc._log.append(old_entry)  # noqa: SLF001

    # Now add one fresh write — should be below threshold of 2
    _stamp(svc, "dave", memory_id="fresh-1")
    assert svc.check_burst_write("dave") is False
