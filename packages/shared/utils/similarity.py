"""Text similarity and fuzzy string matching utilities for Memory Firewall."""

from __future__ import annotations

import re


def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute the Wagner-Fischer edit distance between two strings."""
    if s1 == s2:
        return 0
    if not s1:
        return len(s2)
    if not s2:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1] + [0] * len(s2)
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row[j + 1] = min(insertions, deletions, substitutions)
        previous_row = current_row

    return previous_row[len(s2)]


def normalized_levenshtein(s1: str, s2: str) -> float:
    """Compute normalized Levenshtein similarity in [0.0, 1.0]."""
    if not s1 and not s2:
        return 1.0
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    dist = levenshtein_distance(s1, s2)
    return max(0.0, min(1.0, 1.0 - (dist / max_len)))


def jaccard_similarity(s1: str, s2: str, n_gram: int = 3) -> float:
    """Compute character n-gram Jaccard similarity in [0.0, 1.0]."""
    s1_norm = s1.strip().lower()
    s2_norm = s2.strip().lower()

    if s1_norm == s2_norm:
        return 1.0
    if len(s1_norm) < n_gram or len(s2_norm) < n_gram:
        return 1.0 if s1_norm == s2_norm else 0.0

    grams1 = {s1_norm[i : i + n_gram] for i in range(len(s1_norm) - n_gram + 1)}
    grams2 = {s2_norm[i : i + n_gram] for i in range(len(s2_norm) - n_gram + 1)}

    intersection = len(grams1 & grams2)
    union = len(grams1 | grams2)
    return intersection / union if union > 0 else 0.0


def token_overlap_ratio(s1: str, s2: str) -> float:
    """Compute token-level overlap ratio between two strings."""
    tokens1 = set(re.findall(r"\w+", s1.lower()))
    tokens2 = set(re.findall(r"\w+", s2.lower()))

    if not tokens1 and not tokens2:
        return 1.0
    if not tokens1 or not tokens2:
        return 0.0

    overlap = len(tokens1 & tokens2)
    return (2.0 * overlap) / (len(tokens1) + len(tokens2))


def fuzzy_match(s1: str, s2: str, threshold: float = 0.8) -> bool:
    """Determine if two strings are fuzzy duplicates based on composite metrics."""
    if s1.strip().lower() == s2.strip().lower():
        return True

    lev = normalized_levenshtein(s1, s2)
    if lev >= threshold:
        return True

    tok = token_overlap_ratio(s1, s2)
    if tok >= threshold:
        return True

    jac = jaccard_similarity(s1, s2)
    if jac >= threshold:
        return True

    composite = (lev * 0.4) + (tok * 0.4) + (jac * 0.2)
    return composite >= threshold
