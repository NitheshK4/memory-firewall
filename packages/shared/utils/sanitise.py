"""Content sanitisation utilities for Memory Firewall.

Provides lightweight helpers to normalise and gate raw input text before it
is processed by services such as ClaimExtractor and RiskService.  Keeping
these functions in the shared package makes them available to connectors,
ingest pipelines, and API routers alike.
"""

from __future__ import annotations

import re
import unicodedata

# Maximum characters accepted from a single raw memory write.
# Content exceeding this limit is truncated with a visible marker.
DEFAULT_MAX_CONTENT_LENGTH: int = 8_000

# Regex for C0/C1 control characters except common whitespace (\\t \\n \\r).
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")


def strip_control_chars(text: str) -> str:
    """Remove ASCII/Latin-1 control characters that are not normal whitespace.

    Null bytes (\\x00), BEL, BS, VT, FF, and the full C1 block (\\x80-\\x9f)
    can cause issues in JSON serialisation, embedding models, and log parsers.
    Ordinary tab (\\t), newline (\\n), and carriage-return (\\r) are preserved.
    """
    return _CONTROL_CHAR_RE.sub("", text)


def normalise_unicode(text: str) -> str:
    """Apply NFC normalisation so visually identical strings hash identically.

    This prevents trivial fingerprint bypasses where an attacker sends the
    same content using different Unicode encodings (e.g. composed vs
    decomposed accents).
    """
    return unicodedata.normalize("NFC", text)


def truncate(text: str, max_length: int = DEFAULT_MAX_CONTENT_LENGTH) -> str:
    """Truncate *text* to at most *max_length* characters.

    A visible ``… [truncated]`` suffix is appended so downstream consumers
    know the content was shortened.
    """
    if len(text) <= max_length:
        return text
    suffix = " … [truncated]"
    return text[: max_length - len(suffix)] + suffix


def sanitise_content(
    text: str,
    max_length: int = DEFAULT_MAX_CONTENT_LENGTH,
) -> str:
    """Apply the full sanitisation pipeline to raw memory content.

    Steps (in order):
    1. Strip C0/C1 control characters.
    2. NFC-normalise Unicode.
    3. Collapse runs of more than two consecutive blank lines.
    4. Truncate to *max_length* characters.
    """
    text = strip_control_chars(text)
    text = normalise_unicode(text)
    # Collapse excessive blank lines (> 2 consecutive)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = truncate(text, max_length)
    return text
