"""Slack connector — ingests memories from Slack channel messages via the Web API."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass
class SlackMemory:
    channel: str
    user: str
    text: str
    ts: str

    def to_ingest_payload(self) -> dict:
        return {
            "content": self.text,
            "source_type": "slack",
            "source_id": f"{self.channel}/{self.ts}",
            "actor": self.user,
            "metadata": {"channel": self.channel, "ts": self.ts},
        }


class SlackConnector:
    """Fetch recent messages from a Slack channel and yield ingest payloads.

    Requires the ``slack_sdk`` package and a bot token with
    ``channels:history`` scope.
    """

    def __init__(self, token: str | None = None) -> None:
        try:
            from slack_sdk import WebClient  # type: ignore[import]
        except ImportError as exc:
            raise ImportError("Install slack-sdk: pip install slack-sdk") from exc
        self._client = WebClient(token=token or os.environ["SLACK_BOT_TOKEN"])

    def fetch_recent(self, channel_id: str, limit: int = 50) -> list[SlackMemory]:
        response = self._client.conversations_history(channel=channel_id, limit=limit)
        messages: list[SlackMemory] = []
        for msg in response.get("messages", []):
            text = msg.get("text", "").strip()
            if not text or msg.get("subtype"):  # skip system messages
                continue
            messages.append(
                SlackMemory(
                    channel=channel_id,
                    user=msg.get("user", "unknown"),
                    text=text,
                    ts=msg.get("ts", ""),
                )
            )
        return messages
