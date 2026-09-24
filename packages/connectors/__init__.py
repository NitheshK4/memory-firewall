"""Memory Firewall connectors package."""

from packages.connectors.base_connector import BaseConnector, IngestPayload
from packages.connectors.docs_connector import DocsConnector, DocsMemory
from packages.connectors.email_connector import EmailConnector, EmailMemory
from packages.connectors.github_connector import GitHubConnector, GitHubMemory
from packages.connectors.slack_connector import SlackConnector, SlackMemory
from packages.connectors.tool_trace_connector import ToolTraceConnector, ToolTraceEvent
from packages.connectors.webhook_connector import WebhookConnector, WebhookEvent

__all__ = [
    "BaseConnector",
    "IngestPayload",
    "DocsConnector",
    "DocsMemory",
    "EmailConnector",
    "EmailMemory",
    "GitHubConnector",
    "GitHubMemory",
    "SlackConnector",
    "SlackMemory",
    "ToolTraceConnector",
    "ToolTraceEvent",
    "WebhookConnector",
    "WebhookEvent",
]
