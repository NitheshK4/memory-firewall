"""Unit tests for Prometheus metrics registry and /metrics endpoint."""

from fastapi.testclient import TestClient
import pytest

from apps.api.app.main import app
from apps.api.app.telemetry.metrics import MetricsRegistry, metrics


@pytest.fixture(autouse=True)
def reset_metrics():
    metrics.reset()
    yield
    metrics.reset()


def test_metrics_registry_counters_and_gauges():
    reg = MetricsRegistry()
    reg.inc_counter("test_counter", 2.0, labels={"env": "prod"})
    reg.inc_counter("test_counter", 3.0, labels={"env": "prod"})
    assert reg.get_counter("test_counter", labels={"env": "prod"}) == 5.0

    reg.set_gauge("test_gauge", 42.0, labels={"service": "api"})
    assert reg.get_gauge("test_gauge", labels={"service": "api"}) == 42.0

    prom_text = reg.generate_prometheus_text()
    assert 'test_counter{env="prod"} 5.0' in prom_text
    assert 'test_gauge{service="api"} 42.0' in prom_text


def test_metrics_endpoint():
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "memory_firewall_writes_total" in response.text
    assert response.headers["content-type"].startswith("text/plain")


def test_metrics_updated_on_write():
    client = TestClient(app)
    payload = {
        "content": "User prefers dark theme",
        "source_type": "user",
        "source_id": "test_src",
        "actor": "alice",
    }
    client.post("/api/v1/memories", json=payload)
    resp = client.get("/metrics")
    assert 'memory_firewall_writes_total{action="allow"} 1.0' in resp.text
