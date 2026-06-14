from fastapi import APIRouter, Depends

from apps.api.app.deps import ServiceContainer, get_container
from apps.api.app.models.verdict import MemoryStatus

router = APIRouter(tags=["health"])


@router.get("/health")
def health(
    container: ServiceContainer = Depends(get_container),
) -> dict[str, object]:
    memories = container.repository.list_memories()
    status_breakdown = {
        status.value: 0
        for status in MemoryStatus
    }
    for memory in memories:
        status_breakdown[memory.status.value] += 1

    return {
        "status": "ok",
        "service": container.settings.app_name,
        "memory_count": len(memories),
        "quarantine_count": len(container.repository.list_quarantined()),
        "status_breakdown": status_breakdown,
    }


@router.get("/health/detailed", summary="Per-component liveness and statistics")
def health_detailed(
    container: ServiceContainer = Depends(get_container),
) -> dict[str, object]:
    """Return a per-component health report.

    Components reported:

    * **repository** — live memory count broken down by status.
    * **audit_log** — total audit entries and event-type distribution.
    * **vector_store** — always ``ok``; placeholder for future store health.
    """
    memories = container.repository.list_memories()
    status_breakdown = {s.value: 0 for s in MemoryStatus}
    for memory in memories:
        status_breakdown[memory.status.value] += 1

    audit_entries = container.audit_service.get_log()
    event_stats = container.audit_service.get_event_stats()

    return {
        "status": "ok",
        "components": {
            "repository": {
                "status": "ok",
                "memory_count": len(memories),
                "status_breakdown": status_breakdown,
            },
            "audit_log": {
                "status": "ok",
                "entry_count": len(audit_entries),
                "event_stats": event_stats,
            },
            "vector_store": {
                "status": "ok",
            },
        },
    }
