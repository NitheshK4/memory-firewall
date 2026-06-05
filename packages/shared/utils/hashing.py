"""Hashing utilities for Memory Firewall.

Provides stable, deterministic content fingerprints used to detect
duplicate memories and measure similarity without full text comparison.
"""

from __future__ import annotations

import hashlib


def sha256_hex(text: str) -> str:
    """Return the hex-encoded SHA-256 digest of *text* (UTF-8 encoded)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def short_hash(text: str, length: int = 8) -> str:
    """Return a short (default 8-char) hex prefix of the SHA-256 digest.

    Useful for human-readable IDs; not intended for cryptographic use.
    """
    return sha256_hex(text)[:length]


def content_fingerprint(content: str) -> str:
    """Normalise whitespace then hash — tolerates minor formatting differences."""
    normalised = " ".join(content.lower().split())
    return sha256_hex(normalised)
