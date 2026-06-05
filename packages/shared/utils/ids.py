"""ID generation utilities for Memory Firewall."""

from __future__ import annotations

import uuid


def new_uuid() -> str:
    """Return a new random UUID4 as a lower-case hex string."""
    return str(uuid.uuid4())


def short_id(prefix: str = "", length: int = 8) -> str:
    """Return a short random ID optionally prefixed by *prefix*.

    Example: ``short_id("mem") → "mem-a3f2c1d9"``
    """
    hex_part = uuid.uuid4().hex[:length]
    return f"{prefix}-{hex_part}" if prefix else hex_part


def memory_id() -> str:
    """Canonical ID for a new memory item."""
    return new_uuid()


def claim_id() -> str:
    """Canonical ID for a new claim."""
    return new_uuid()


def event_id() -> str:
    """Canonical ID for a policy or audit event."""
    return new_uuid()
