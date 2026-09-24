"""Unit tests for Memory Firewall Python SDK Client."""

import io
import json
import urllib.error
import unittest.mock as mock
import pytest

from packages.client import MemoryFirewallClient, MemoryFirewallClientError


class FakeResponse:
    def __init__(self, data: dict, status: int = 200):
        self.data = json.dumps(data).encode("utf-8")
        self.status = status

    def read(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def test_client_health():
    client = MemoryFirewallClient(base_url="http://mock-api:8000")
    with mock.patch("urllib.request.urlopen", return_value=FakeResponse({"status": "ok", "version": "0.2.0"})):
        res = client.health()
        assert res["status"] == "ok"
        assert res["version"] == "0.2.0"


def test_client_write_memory():
    client = MemoryFirewallClient(base_url="http://mock-api:8000")
    expected_response = {
        "id": "mem-123",
        "action": "allow",
        "trust_score": 0.95,
        "claims": [],
        "reasons": [],
    }
    with mock.patch("urllib.request.urlopen", return_value=FakeResponse(expected_response)):
        res = client.write_memory(
            content="User prefers light theme",
            source_type="user",
            actor="alice",
            tags=["ui", "preferences"],
        )
        assert res["id"] == "mem-123"
        assert res["action"] == "allow"


def test_client_retrieve_memories():
    client = MemoryFirewallClient(base_url="http://mock-api:8000")
    expected_response = [
        {"id": "mem-123", "content": "User prefers light theme", "trust_score": 0.95}
    ]
    with mock.patch("urllib.request.urlopen", return_value=FakeResponse(expected_response)):
        res = client.retrieve_memories(query="theme preference", actor="alice")
        assert len(res) == 1
        assert res[0]["id"] == "mem-123"


def test_client_error_handling():
    client = MemoryFirewallClient(base_url="http://mock-api:8000")
    error_fp = io.BytesIO(json.dumps({"detail": "Memory not found"}).encode("utf-8"))
    http_error = urllib.error.HTTPError(
        url="http://mock-api:8000/api/v1/memories/bad-id",
        code=404,
        msg="Not Found",
        hdrs={},
        fp=error_fp,
    )

    with mock.patch("urllib.request.urlopen", side_effect=http_error):
        with pytest.raises(MemoryFirewallClientError) as exc_info:
            client.get_memory("bad-id")
        assert exc_info.value.status_code == 404
        assert "Memory not found" in exc_info.value.message


def test_client_context_manager():
    with MemoryFirewallClient(base_url="http://mock-api:8000") as client:
        assert client.base_url == "http://mock-api:8000"
