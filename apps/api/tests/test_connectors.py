"""Unit tests for connectors (Base, GitHub, Webhook, Slack, Docs, ToolTrace)."""

import json
import unittest.mock as mock
import pytest

from packages.connectors.base_connector import IngestPayload
from packages.connectors.github_connector import GitHubConnector, GitHubMemory
from packages.connectors.webhook_connector import WebhookConnector, WebhookEvent
from packages.connectors.slack_connector import SlackMemory
from packages.connectors.docs_connector import DocsMemory
from packages.connectors.tool_trace_connector import ToolTraceEvent


def test_ingest_payload_serialization():
    payload = IngestPayload(
        content="Test content",
        source_type="slack",
        source_id="C123/12345.67",
        actor="alice",
        metadata={"channel": "C123"},
        tags=["chat", "ops"],
    )
    d = payload.to_dict()
    assert d["content"] == "Test content"
    assert d["source_type"] == "slack"
    assert d["source_id"] == "C123/12345.67"
    assert d["actor"] == "alice"
    assert "ops" in d["tags"]


def test_github_memory_to_payload():
    gh = GitHubMemory(
        repo="org/repo",
        item_type="issue",
        item_id=42,
        title="Bug in parser",
        body="Found a bug in the regex parser.",
        author="octocat",
        url="https://github.com/org/repo/issues/42",
        extra_tags=["bug", "security"],
    )
    payload = gh.to_ingest_payload()
    assert payload.source_type == "github"
    assert payload.source_id == "org/repo#42"
    assert payload.actor == "octocat"
    assert "[org/repo] Bug in parser" in payload.content
    assert "Found a bug in the regex parser." in payload.content
    assert "bug" in payload.tags
    assert "github" in payload.tags


def test_github_connector_fetch_issues():
    connector = GitHubConnector(token="fake-token")
    mock_data = [
        {
            "number": 101,
            "title": "Fix critical leak",
            "body": "Patch is ready.",
            "user": {"login": "developer1"},
            "html_url": "https://github.com/org/repo/issues/101",
            "labels": [{"name": "security"}],
        }
    ]

    with mock.patch.object(connector, "_request", return_value=mock_data):
        memories = connector.fetch_issues(repo="org/repo")
        assert len(memories) == 1
        assert memories[0].item_id == 101
        assert memories[0].author == "developer1"

        payloads = connector.fetch_memories(repo="org/repo")
        assert len(payloads) == 1
        assert payloads[0].actor == "developer1"
        assert "security" in payloads[0].tags


def test_webhook_connector_signature_verification():
    secret = "my-secret-key"
    connector = WebhookConnector(secret=secret)
    body = b'{"text": "Production alert triggered", "sender": "pagerduty"}'

    # Compute valid signature
    import hmac
    import hashlib
    sig = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()

    assert connector.verify_signature(body, sig) is True
    assert connector.verify_signature(body, f"sha256={sig}") is True
    assert connector.verify_signature(body, "invalid_sig") is False


def test_webhook_connector_parse_payload():
    connector = WebhookConnector()
    payload = {
        "text": "User updated billing address to 123 Main St",
        "sender": "stripe_webhook",
        "id": "evt_998877",
    }
    event = connector.parse_payload(payload, event_type="billing")
    assert event.event_type == "billing"
    assert event.sender == "stripe_webhook"
    assert "123 Main St" in event.content

    ingest = event.to_ingest_payload()
    assert ingest.source_type == "webhook:billing"
    assert ingest.source_id == "evt_998877"
    assert "webhook" in ingest.tags


def test_slack_memory_payload():
    sm = SlackMemory(channel="C01", user="U02", text="Hello team", ts="123.456")
    p = sm.to_ingest_payload()
    assert p["content"] == "Hello team"
    assert p["source_type"] == "slack"
    assert p["actor"] == "U02"


def test_docs_memory_payload():
    dm = DocsMemory(doc_id="doc123", title="Project Plan", content="Phase 1: Design")
    p = dm.to_ingest_payload()
    assert "Project Plan" in p["content"]
    assert p["source_type"] == "docs"
    assert p["source_id"] == "doc123"


def test_tool_trace_memory_payload():
    ttm = ToolTraceEvent(
        tool_name="bash_exec",
        input_args={"cmd": "ls -la"},
        output="file1 file2",
        actor="agent_smith",
    )
    p = ttm.to_ingest_payload()
    assert p["source_type"] == "tool_trace"
    assert p["actor"] == "agent_smith"
