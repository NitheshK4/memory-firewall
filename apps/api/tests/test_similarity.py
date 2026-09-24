"""Unit tests for text similarity and fuzzy matching utilities."""

import pytest
from packages.shared.utils.similarity import (
    levenshtein_distance,
    normalized_levenshtein,
    jaccard_similarity,
    token_overlap_ratio,
    fuzzy_match,
)


def test_levenshtein_distance_exact_match():
    assert levenshtein_distance("hello", "hello") == 0
    assert levenshtein_distance("", "") == 0


def test_levenshtein_distance_insertions_deletions():
    assert levenshtein_distance("cat", "cats") == 1
    assert levenshtein_distance("kitten", "sitting") == 3
    assert levenshtein_distance("", "test") == 4
    assert levenshtein_distance("test", "") == 4


def test_normalized_levenshtein():
    assert normalized_levenshtein("hello", "hello") == 1.0
    assert normalized_levenshtein("", "") == 1.0
    sim = normalized_levenshtein("kitten", "sitting")
    assert 0.5 < sim < 1.0


def test_jaccard_similarity():
    assert jaccard_similarity("The quick brown fox", "The quick brown fox") == 1.0
    assert jaccard_similarity("abcd", "wxyz") == 0.0
    # Overlapping text
    sim = jaccard_similarity("Memory firewall security policy", "Memory firewall security guardrail")
    assert 0.4 < sim < 1.0


def test_token_overlap_ratio():
    assert token_overlap_ratio("user email is test@example.com", "user email is test@example.com") == 1.0
    assert token_overlap_ratio("apple banana", "orange grape") == 0.0
    ratio = token_overlap_ratio("database host is 127.0.0.1", "database host is remote.db")
    assert ratio > 0.5


def test_fuzzy_match():
    assert fuzzy_match("User preferred dark theme", "User preferred dark theme") is True
    assert fuzzy_match("Deploying to production server", "Deploying to staging server", threshold=0.7) is True
    assert fuzzy_match("Completely unrelated topic here", "Quantum mechanics principles", threshold=0.6) is False
