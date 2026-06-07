from fastapi import APIRouter, Depends, HTTPException, Query

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


@router.get("/{memory_id}", response_model=StoredMemory)
def get_memory(
    memory_id: str,
    _auth: None = Depends(require_api_key),
    container: ServiceContainer = Depends(get_container),
) -> StoredMemory:
    """Fetch a single memory record by its ID."""
    memory = container.repository.get(memory_id)
    if memory is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


@router.delete("/{memory_id}", status_code=200, response_model=StoredMemory)
def delete_memory(
    memory_id: str,
    actor: str = Query(default="api", description="Identity of the caller performing the deletion"),
    _auth: None = Depends(require_api_key),
    container: ServiceContainer = Depends(get_container),
) -> StoredMemory:
    """Soft-block a memory by ID.

    The record is retained in the store (preserving the audit trail) but its
    status is set to ``blocked`` and it is removed from the vector index so it
    will never be returned by retrieval queries again.

    Returns the updated memory object so callers can confirm the new status.
    """
    memory = container.repository.block(memory_id, actor=actor)
    if memory is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    if container.audit_service:
        container.audit_service.log_verdict(
            memory_id,
            action="block",  # type: ignore[arg-type]
            actor=actor,
        )
    return memory

