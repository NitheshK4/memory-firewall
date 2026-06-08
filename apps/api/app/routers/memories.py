from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from apps.api.app.auth import require_api_key
from apps.api.app.deps import ServiceContainer, get_container
from apps.api.app.models.api import MemoryWriteRequest, MemoryWriteResponse, StoredMemory
from apps.api.app.models.verdict import MemoryStatus

router = APIRouter(prefix="/memories", tags=["memories"])


class MemoryListResponse(BaseModel):
    """Paginated list of stored memories with total count metadata."""

    total: int
    offset: int
    limit: int
    items: list[StoredMemory]


@router.post("", response_model=MemoryWriteResponse)
def write_memory(
    request: MemoryWriteRequest,
    _auth: None = Depends(require_api_key),
    container: ServiceContainer = Depends(get_container),
) -> MemoryWriteResponse:
    return container.write_firewall.run(request)


@router.get("", response_model=MemoryListResponse)
def list_memories(
    status: MemoryStatus | None = None,
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of records to return."),
    offset: int = Query(default=0, ge=0, description="Number of records to skip before returning results."),
    _auth: None = Depends(require_api_key),
    container: ServiceContainer = Depends(get_container),
) -> MemoryListResponse:
    """List memories with optional status filter and pagination.

    Returns an envelope containing ``total`` (count before pagination),
    ``offset``, ``limit``, and ``items`` (the page of records).
    """
    all_memories = container.repository.list_memories(status=status)
    total = len(all_memories)
    page = all_memories[offset : offset + limit]
    return MemoryListResponse(total=total, offset=offset, limit=limit, items=page)


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

