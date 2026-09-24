from fastapi import APIRouter, Depends

from apps.api.app.auth import require_api_key
from apps.api.app.deps import ServiceContainer, get_container
from apps.api.app.models.api import RetrievalRequest, RetrievalResponse

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


from apps.api.app.telemetry.metrics import metrics


@router.post("/query", response_model=RetrievalResponse)
def query_memories(
    request: RetrievalRequest,
    _auth: None = Depends(require_api_key),
    container: ServiceContainer = Depends(get_container),
) -> RetrievalResponse:
    res = container.read_firewall.run(request)
    metrics.inc_counter("memory_firewall_retrievals_total", labels={"actor": request.actor})
    return res

