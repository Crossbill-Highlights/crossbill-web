"""
ContentHash value object for deduplication.

Used to detect duplicate highlights and reading sessions.
"""

import hashlib
from dataclasses import dataclass
from typing import Self

_CONTENT_HASH_LENGTH = 64


@dataclass(frozen=True)
class ContentHash:
    """
    SHA-256 hash for content deduplication.

    Used to identify duplicate highlights and reading sessions
    without comparing full text content.
    """

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("ContentHash cannot be empty")

        # Validate it's a valid hex string (SHA-256 is 64 chars)
        if len(self.value) != _CONTENT_HASH_LENGTH:
            raise ValueError("ContentHash must be 64 character hex string (SHA-256)")

        try:
            int(self.value, 16)
        except ValueError as err:
            raise ValueError("ContentHash must be valid hexadecimal string") from err

    @classmethod
    def compute(cls, content: str) -> Self:
        """
        Compute ContentHash from string content.

        Args:
            content: Text content to hash

        Returns:
            ContentHash instance with computed hash
        """
        if not content:
            raise ValueError("Cannot compute hash of empty content")

        hash_value = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return cls(hash_value)

    @classmethod
    def compute_from_parts(cls, *parts: str) -> Self:
        """
        Compute ContentHash from multiple string parts.

        Useful for hashing composite content (e.g., highlight text + note).

        Args:
            *parts: String parts to concatenate and hash

        Returns:
            ContentHash instance
        """
        combined = "|".join(parts)
        return cls.compute(combined)
