from fastapi import APIRouter, Depends

from apps.api.app.auth import require_api_key
from apps.api.app.deps import ServiceContainer, get_container
from apps.api.app.models.api import MemoryWriteRequest, MemoryWriteResponse, StoredMemory
from apps.api.app.models.verdict import MemoryStatus

router = APIRouter(prefix="/memories", tags=["memories"])


@router.post("", response_model=MemoryWriteResponse)
def write_memory(
    request: MemoryWriteRequest,
    _auth: None = Depends(require_api_key),
    container: ServiceContainer = Depends(get_container),
) -> MemoryWriteResponse:
    return container.write_firewall.run(request)


@router.get("", response_model=list[StoredMemory])
def list_memories(
    status: MemoryStatus | None = None,
    _auth: None = Depends(require_api_key),
    container: ServiceContainer = Depends(get_container),
) -> list[StoredMemory]:
    return container.repository.list_memories(status=status)

