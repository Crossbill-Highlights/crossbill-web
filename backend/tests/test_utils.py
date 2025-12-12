"""Tests for utility functions."""

import pytest

from src.utils import compute_highlight_hash


class TestComputeHighlightHash:
    """Test suite for compute_highlight_hash function."""

    def test_basic_hash_generation(self) -> None:
        """Test that hash is generated correctly."""
        hash_result = compute_highlight_hash(
            text="Test highlight text",
            book_title="Test Book",
            book_author="Test Author",
        )

        # Should be a 64-character hex string (SHA-256)
        assert len(hash_result) == 64
        assert all(c in "0123456789abcdef" for c in hash_result)

    def test_same_inputs_produce_same_hash(self) -> None:
        """Test that identical inputs produce identical hashes."""
        hash1 = compute_highlight_hash(
            text="Test highlight",
            book_title="My Book",
            book_author="John Doe",
        )
        hash2 = compute_highlight_hash(
            text="Test highlight",
            book_title="My Book",
            book_author="John Doe",
        )

        assert hash1 == hash2

    def test_different_text_produces_different_hash(self) -> None:
        """Test that different text produces different hash."""
        hash1 = compute_highlight_hash(
            text="First highlight",
            book_title="My Book",
            book_author="John Doe",
        )
        hash2 = compute_highlight_hash(
            text="Second highlight",
            book_title="My Book",
            book_author="John Doe",
        )

        assert hash1 != hash2

    def test_different_book_title_produces_different_hash(self) -> None:
        """Test that different book title produces different hash."""
        hash1 = compute_highlight_hash(
            text="Same highlight",
            book_title="Book One",
            book_author="John Doe",
        )
        hash2 = compute_highlight_hash(
            text="Same highlight",
            book_title="Book Two",
            book_author="John Doe",
        )

        assert hash1 != hash2

    def test_different_author_produces_different_hash(self) -> None:
        """Test that different author produces different hash."""
        hash1 = compute_highlight_hash(
            text="Same highlight",
            book_title="Same Book",
            book_author="Author One",
        )
        hash2 = compute_highlight_hash(
            text="Same highlight",
            book_title="Same Book",
            book_author="Author Two",
        )

        assert hash1 != hash2

    def test_none_author_handled_correctly(self) -> None:
        """Test that None author is handled consistently."""
        hash1 = compute_highlight_hash(
            text="Test highlight",
            book_title="My Book",
            book_author=None,
        )
        hash2 = compute_highlight_hash(
            text="Test highlight",
            book_title="My Book",
            book_author=None,
        )

        assert hash1 == hash2

    def test_none_author_different_from_empty_string(self) -> None:
        """Test that None and empty string author produce same hash (both normalize to empty)."""
        hash_none = compute_highlight_hash(
            text="Test highlight",
            book_title="My Book",
            book_author=None,
        )
        hash_empty = compute_highlight_hash(
            text="Test highlight",
            book_title="My Book",
            book_author="",
        )

        # Both None and empty string should normalize to empty, producing same hash
        assert hash_none == hash_empty

    def test_whitespace_normalization(self) -> None:
        """Test that leading/trailing whitespace is stripped."""
        hash1 = compute_highlight_hash(
            text="  Test highlight  ",
            book_title="  My Book  ",
            book_author="  John Doe  ",
        )
        hash2 = compute_highlight_hash(
            text="Test highlight",
            book_title="My Book",
            book_author="John Doe",
        )

        assert hash1 == hash2

    def test_internal_whitespace_preserved(self) -> None:
        """Test that internal whitespace is preserved."""
        hash1 = compute_highlight_hash(
            text="Test  highlight",  # Two spaces
            book_title="My Book",
            book_author="John Doe",
        )
        hash2 = compute_highlight_hash(
            text="Test highlight",  # One space
            book_title="My Book",
            book_author="John Doe",
        )

        assert hash1 != hash2

    def test_unicode_text_handled(self) -> None:
        """Test that unicode text is handled correctly."""
        hash_result = compute_highlight_hash(
            text="日本語のハイライト",
            book_title="本のタイトル",
            book_author="著者名",
        )

        assert len(hash_result) == 64

    def test_special_characters_in_text(self) -> None:
        """Test that special characters don't break hashing."""
        hash_result = compute_highlight_hash(
            text="Test with special chars: |{}[]<>!@#$%^&*()",
            book_title="Book | With | Pipes",
            book_author="Author <Special>",
        )

        assert len(hash_result) == 64
