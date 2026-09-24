"""Base connector interface and models for Memory Firewall."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class IngestPayload:
    """Standardized ingest payload structure for Memory Firewall."""
    content: str
    source_type: str
    source_id: str
    actor: str
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "actor": self.actor,
            "metadata": self.metadata,
            "tags": self.tags,
        }


class BaseConnector(ABC):
    """Abstract base class for all memory connectors."""

    @abstractmethod
    def fetch_memories(self, *args: Any, **kwargs: Any) -> list[IngestPayload]:
        """Fetch records from the upstream source and convert them to IngestPayloads."""
        raise NotImplementedError
