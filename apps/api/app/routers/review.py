from fastapi import APIRouter, Depends, HTTPException

from apps.api.app.auth import require_api_key
from apps.api.app.deps import ServiceContainer, get_container
from apps.api.app.models.api import ReviewDecision, StoredMemory

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/quarantine", response_model=list[StoredMemory])
def list_quarantine(
    _auth: None = Depends(require_api_key),
    container: ServiceContainer = Depends(get_container),
) -> list[StoredMemory]:
    return container.quarantine_service.list_quarantined()


@router.post("/{memory_id}/decision", response_model=StoredMemory)
def apply_review(
    memory_id: str,
    decision: ReviewDecision,
    _auth: None = Depends(require_api_key),
    container: ServiceContainer = Depends(get_container),
) -> StoredMemory:
    """Apply a human review decision to a quarantined memory.

    Records the decision in the audit log regardless of outcome so the full
    review history is always available via ``GET /api/v1/audit``.
    """
    memory = container.quarantine_service.apply_decision(memory_id, decision)
    if memory is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    if container.audit_service:
        container.audit_service.log_review(memory_id, decision)
    return memory


