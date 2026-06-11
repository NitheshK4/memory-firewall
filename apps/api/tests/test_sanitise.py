"""Unit tests for packages.shared.utils.sanitise."""

from __future__ import annotations

import pytest

from packages.shared.utils.sanitise import (
    DEFAULT_MAX_CONTENT_LENGTH,
    normalise_unicode,
    sanitise_content,
    strip_control_chars,
    truncate,
)


class TestStripControlChars:
    """strip_control_chars should remove C0/C1 control bytes but keep whitespace."""

    def test_null_bytes_removed(self) -> None:
        assert strip_control_chars("hello\x00world") == "helloworld"

    def test_bel_removed(self) -> None:
        assert strip_control_chars("ring\x07bell") == "ringbell"

    def test_tab_preserved(self) -> None:
        assert strip_control_chars("col1\tcol2") == "col1\tcol2"

    def test_newline_preserved(self) -> None:
        assert strip_control_chars("line1\nline2") == "line1\nline2"

    def test_carriage_return_preserved(self) -> None:
        assert strip_control_chars("a\rb") == "a\rb"

    def test_c1_block_removed(self) -> None:
        # \x80–\x9f are C1 control characters
        assert strip_control_chars("a\x80b\x9fc") == "abc"

    def test_clean_string_unchanged(self) -> None:
        text = "The quick brown fox jumps over the lazy dog."
        assert strip_control_chars(text) == text

    def test_empty_string(self) -> None:
        assert strip_control_chars("") == ""

    def test_multiple_control_chars(self) -> None:
        assert strip_control_chars("\x01\x02\x03hello\x1f") == "hello"


class TestNormaliseUnicode:
    """normalise_unicode should NFC-compose decomposed Unicode sequences."""

    def test_nfc_already_composed_unchanged(self) -> None:
        # "é" as a single pre-composed character (U+00E9)
        composed = "\u00e9"
        assert normalise_unicode(composed) == composed

    def test_decomposed_becomes_composed(self) -> None:
        # "é" as "e" + combining acute (U+0065 + U+0301) → U+00E9
        decomposed = "e\u0301"
        composed = "\u00e9"
        assert normalise_unicode(decomposed) == composed

    def test_ascii_unchanged(self) -> None:
        text = "hello world"
        assert normalise_unicode(text) == text

    def test_empty_string(self) -> None:
        assert normalise_unicode("") == ""

    def test_mixed_composed_and_ascii(self) -> None:
        result = normalise_unicode("caf\u0065\u0301")
        assert result == "caf\u00e9"


class TestTruncate:
    """truncate should cap length and add a visible suffix."""

    def test_short_text_unchanged(self) -> None:
        text = "hello"
        assert truncate(text, max_length=100) == text

    def test_exactly_at_limit_unchanged(self) -> None:
        text = "a" * 100
        assert truncate(text, max_length=100) == text

    def test_exceeding_text_is_truncated(self) -> None:
        text = "a" * 200
        result = truncate(text, max_length=100)
        assert len(result) == 100

    def test_truncated_text_ends_with_suffix(self) -> None:
        text = "a" * 200
        result = truncate(text, max_length=100)
        assert result.endswith(" … [truncated]")

    def test_default_limit_applied(self) -> None:
        text = "x" * (DEFAULT_MAX_CONTENT_LENGTH + 500)
        result = truncate(text)
        assert len(result) == DEFAULT_MAX_CONTENT_LENGTH

    def test_empty_string(self) -> None:
        assert truncate("", max_length=10) == ""


class TestSanitiseContent:
    """sanitise_content should apply the full pipeline end-to-end."""

    def test_strips_control_chars(self) -> None:
        result = sanitise_content("hello\x00world")
        assert "\x00" not in result
        assert "hello" in result

    def test_normalises_unicode(self) -> None:
        result = sanitise_content("caf\u0065\u0301")
        assert result == "caf\u00e9"

    def test_collapses_excessive_blank_lines(self) -> None:
        text = "paragraph1\n\n\n\n\nparagraph2"
        result = sanitise_content(text)
        # More than 2 consecutive newlines should be collapsed to exactly 2
        assert "\n\n\n" not in result
        assert "paragraph1" in result
        assert "paragraph2" in result

    def test_two_blank_lines_preserved(self) -> None:
        text = "a\n\nb"
        assert sanitise_content(text) == text

    def test_truncates_overlong_content(self) -> None:
        text = "z" * (DEFAULT_MAX_CONTENT_LENGTH + 1000)
        result = sanitise_content(text)
        assert len(result) == DEFAULT_MAX_CONTENT_LENGTH

    def test_clean_short_text_unchanged(self) -> None:
        text = "This is a perfectly clean memory entry."
        assert sanitise_content(text) == text

    def test_empty_string(self) -> None:
        assert sanitise_content("") == ""

    def test_combined_attack_vector(self) -> None:
        """Null byte injection + decomposed Unicode + excess blanks."""
        text = "Admin\x00 says:\n\n\n\npassword is caf\u0065\u0301"
        result = sanitise_content(text)
        assert "\x00" not in result
        assert "\n\n\n" not in result
        assert "caf\u00e9" in result
