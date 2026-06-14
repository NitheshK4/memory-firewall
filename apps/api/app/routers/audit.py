from fastapi import APIRouter, Depends, Query

from apps.api.app.auth import require_api_key
from apps.api.app.deps import ServiceContainer, get_container

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/", summary="List audit log entries")
def list_audit(
    memory_id: str | None = Query(default=None, description="Filter entries for a specific memory"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of entries to return"),
    _auth: None = Depends(require_api_key),
    container: ServiceContainer = Depends(get_container),
) -> list[dict]:
    """Return the immutable audit trail for all firewall events.

    Optionally filter by ``memory_id`` to see the full lifecycle of a single
    memory item (write → verdict → quarantine → review decision).

    Results are ordered newest-first and capped at *limit* entries.
    """
    entries = container.audit_service.get_log(memory_id=memory_id)
    # Newest-first
    entries = list(reversed(entries))
    return entries[:limit]


@router.get("/actors", summary="Actor write-activity statistics")
def actor_stats(
    _auth: None = Depends(require_api_key),
    container: ServiceContainer = Depends(get_container),
) -> dict[str, dict]:
    """Return per-actor write counts, last-write timestamp, and burst flag.

    Useful for building dashboards that surface which actors are producing
    the most memory-write traffic or are currently bursting.
    """
    return container.audit_service.get_actor_stats()


@router.get("/stats", summary="Aggregate event-type counts from the audit log")
def event_stats(
    _auth: None = Depends(require_api_key),
    container: ServiceContainer = Depends(get_container),
) -> dict[str, int]:
    """Return a count of each distinct event type across the entire audit log.

    Useful for building dashboards that surface firewall throughput, verdict
    distribution, retrieval activity, and dedup suppression rates at a glance.

    Example response::

        {
            "memory_written": 42,
            "verdict:allow": 30,
            "verdict:quarantine": 8,
            "retrieval_served": 120,
            "retrieval_suppressed": 15,
            "dedup_skipped": 5
        }
    """
    return container.audit_service.get_event_stats()
