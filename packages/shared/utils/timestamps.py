"""Timestamp utilities for Memory Firewall."""

from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def utcnow_iso() -> str:
    """Return the current UTC datetime as an ISO-8601 string."""
    return utcnow().isoformat()


def from_iso(ts: str) -> datetime:
    """Parse an ISO-8601 string into a timezone-aware datetime.

    Attaches UTC if no timezone info is present.
    """
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
