"""Prometheus metrics endpoint router."""

from fastapi import APIRouter, Response
from apps.api.app.telemetry.metrics import metrics

router = APIRouter(tags=["telemetry"])


@router.get("/metrics", response_class=Response)
@router.get("/api/v1/metrics", response_class=Response)
def get_prometheus_metrics() -> Response:
    """Expose Prometheus formatted application metrics."""
    body = metrics.generate_prometheus_text()
    return Response(content=body, media_type="text/plain; version=0.0.4; charset=utf-8")
