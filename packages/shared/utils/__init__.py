"""Shared utilities for Memory Firewall."""

from packages.shared.utils.hashing import (
    content_fingerprint,
    sha256_hex,
    short_hash,
)
from packages.shared.utils.ids import (
    claim_id,
    event_id,
    memory_id,
    new_uuid,
    short_id,
)
from packages.shared.utils.sanitise import (
    normalise_unicode,
    sanitise_content,
    strip_control_chars,
    truncate,
)
from packages.shared.utils.similarity import (
    fuzzy_match,
    jaccard_similarity,
    levenshtein_distance,
    normalized_levenshtein,
    token_overlap_ratio,
)
from packages.shared.utils.timestamps import (
    from_iso,
    utcnow,
    utcnow_iso,
)

__all__ = [
    "content_fingerprint",
    "sha256_hex",
    "short_hash",
    "claim_id",
    "event_id",
    "memory_id",
    "new_uuid",
    "short_id",
    "normalise_unicode",
    "sanitise_content",
    "strip_control_chars",
    "truncate",
    "fuzzy_match",
    "jaccard_similarity",
    "levenshtein_distance",
    "normalized_levenshtein",
    "token_overlap_ratio",
    "from_iso",
    "utcnow",
    "utcnow_iso",
]
