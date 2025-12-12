"""Utility functions for the backend."""

import hashlib


def compute_highlight_hash(text: str, book_title: str, book_author: str | None) -> str:
    """
    Compute a unique hash for a highlight based on its content and book metadata.

    This hash is used for deduplication during highlight uploads. The hash is computed
    from the highlight text, book title, and author (if present). This allows the
    highlight text or book metadata to be edited later without breaking deduplication.

    Args:
        text: The highlight text content
        book_title: The title of the book
        book_author: The author of the book (can be None)

    Returns:
        A 64-character hex string (SHA-256 hash truncated to 256 bits)
    """
    # Normalize inputs: strip whitespace and use empty string for None author
    normalized_text = text.strip()
    normalized_title = book_title.strip()
    normalized_author = (book_author or "").strip()

    # Create a consistent string representation for hashing
    # Using pipe as separator since it's unlikely to appear in content
    hash_input = f"{normalized_text}|{normalized_title}|{normalized_author}"

    # Compute SHA-256 hash and return as hex string (64 chars)
    return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
