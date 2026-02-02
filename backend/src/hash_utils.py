"""Utility functions for the backend."""

from __future__ import annotations

import hashlib


def compute_reading_session_hash_v2(
    book_id: int,
    user_id: int,
    start_time: str,
    device_id: str | None,
) -> str:
    """
    Compute a unique hash for a reading session using IDs instead of metadata.

    This version is more stable as book title/author can change, while IDs cannot.
    A session is considered unique based on book_id, user_id, start time, and device.

    Args:
        book_id: The database ID of the book
        user_id: The database ID of the user
        start_time: ISO format timestamp of session start
        device_id: Device identifier (can be None)

    Returns:
        A 64-character hex string (SHA-256 hash)
    """
    # Normalize device_id
    normalized_device = (device_id or "").strip()

    # Create a consistent string representation for hashing
    hash_input = f"{book_id}|{user_id}|{start_time}|{normalized_device}"

    # Compute SHA-256 hash and return as hex string (64 chars)
    return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
