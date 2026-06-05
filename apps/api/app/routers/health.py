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
