"""Webhook connector — ingests structured event payloads with signature verification."""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from typing import Any, Callable

from packages.connectors.base_connector import BaseConnector, IngestPayload


@dataclass
class WebhookEvent:
    event_type: str
    sender: str
    content: str
    event_id: str
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    def to_ingest_payload(self) -> IngestPayload:
        tags = ["webhook", self.event_type, *self.tags]
        return IngestPayload(
            content=self.content,
            source_type=f"webhook:{self.event_type}",
            source_id=self.event_id,
            actor=self.sender,
            metadata=self.metadata,
            tags=tags,
        )


class WebhookConnector(BaseConnector):
    """Parses and validates generic inbound webhooks into memory ingest payloads."""

    def __init__(self, secret: str | None = None) -> None:
        self._secret = secret

    def verify_signature(self, raw_body: bytes, signature_header: str, algorithm: str = "sha256") -> bool:
        """Verify HMAC signature of incoming webhook payload."""
        if not self._secret:
            return True
        if not signature_header:
            return False

        # Handle header formats like "sha256=abc..." or bare hex
        expected_prefix = f"{algorithm}="
        sig_to_check = signature_header
        if signature_header.startswith(expected_prefix):
            sig_to_check = signature_header[len(expected_prefix):]

        hash_func = getattr(hashlib, algorithm, hashlib.sha256)
        mac = hmac.new(self._secret.encode("utf-8"), raw_body, hash_func)
        computed_sig = mac.hexdigest()

        return hmac.compare_digest(computed_sig.lower(), sig_to_check.lower())

    def parse_payload(
        self,
        payload_data: dict[str, Any] | str,
        content_key: str = "text",
        sender_key: str = "sender",
        event_type: str = "generic",
        event_id_key: str = "id",
    ) -> WebhookEvent:
        """Extract a WebhookEvent from a JSON dictionary or string."""
        if isinstance(payload_data, str):
            data = json.loads(payload_data)
        else:
            data = payload_data

        content = str(data.get(content_key, data.get("content", data.get("message", ""))))
        sender = str(data.get(sender_key, data.get("actor", data.get("user", "webhook_client"))))
        event_id = str(data.get(event_id_key, data.get("event_id", hashlib.md5(content.encode("utf-8")).hexdigest()[:12])))

        return WebhookEvent(
            event_type=event_type,
            sender=sender,
            content=content,
            event_id=event_id,
            metadata=data,
            tags=[event_type],
        )

    def fetch_memories(self, payloads: list[dict[str, Any]], **kwargs: Any) -> list[IngestPayload]:
        """Convert a list of raw payloads into IngestPayload instances."""
        events = [self.parse_payload(p, **kwargs) for p in payloads]
        return [ev.to_ingest_payload() for ev in events]
