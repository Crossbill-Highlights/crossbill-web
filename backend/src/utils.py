"""Utility functions for the backend."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.exceptions import XPointParseError

if TYPE_CHECKING:
    from typing import Self


# Regex pattern for parsing xpoint strings
# Format: /body/DocFragment[N]/body/.../text()[N].offset
# DocFragment and text node index are optional
_XPOINT_PATTERN = re.compile(
    r"^"
    r"(?:/body/DocFragment\[(\d+)\])?"  # Optional DocFragment[N] - group 1
    r"(/body/.+?)"  # XPath to element - group 2
    r"/text\(\)(?:\[(\d+)\])?"  # text() with optional [N] - group 3
    r"\.(\d+)"  # .offset - group 4
    r"$"
)


@dataclass(frozen=True)
class ParsedXPoint:
    """Parsed representation of a KOReader xpoint string.

    XPoints are position references used by KOReader to mark locations in EPUB documents.
    Format: /body/DocFragment[12]/body/div/p[88]/text().223

    Attributes:
        doc_fragment_index: 1-based index into EPUB spine (None if not present)
        xpath: XPath to the element (without text() selector)
        text_node_index: 1-based index of text node within element (default 1)
        char_offset: 0-based character offset within text node
    """

    doc_fragment_index: int | None
    xpath: str
    text_node_index: int
    char_offset: int

    @classmethod
    def parse(cls, xpoint: str) -> Self:
        """Parse an xpoint string into components.

        Formats supported:
        - /body/DocFragment[12]/body/div/p[88]/text().223
        - /body/div[1]/p[5]/text()[1].0
        - /body/div/p/text().42

        Args:
            xpoint: The xpoint string to parse

        Returns:
            ParsedXPoint with extracted components

        Raises:
            XPointParseError: If the format is invalid
        """
        match = _XPOINT_PATTERN.match(xpoint)
        if not match:
            raise XPointParseError(xpoint, "does not match expected xpoint format")

        doc_fragment_str, xpath, text_node_str, offset_str = match.groups()

        doc_fragment_index = int(doc_fragment_str) if doc_fragment_str else None
        text_node_index = int(text_node_str) if text_node_str else 1
        char_offset = int(offset_str)

        if doc_fragment_index is not None and doc_fragment_index < 1:
            raise XPointParseError(xpoint, "DocFragment index must be >= 1")

        if text_node_index < 1:
            raise XPointParseError(xpoint, "text node index must be >= 1")

        if char_offset < 0:
            raise XPointParseError(xpoint, "character offset must be >= 0")

        return cls(
            doc_fragment_index=doc_fragment_index,
            xpath=xpath,
            text_node_index=text_node_index,
            char_offset=char_offset,
        )


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


def compute_reading_session_hash(
    book_title: str,
    book_author: str | None,
    start_time: str,
    device_id: str | None,
) -> str:
    """
    Compute a unique hash for a reading session for deduplication.

    This hash is used to prevent duplicate reading sessions from being uploaded.
    A session is considered unique based on the book (title+author), start time,
    and device. This allows the same session start time from different devices.

    Args:
        book_title: The title of the book
        book_author: The author of the book (can be None)
        start_time: ISO format timestamp of session start
        device_id: Device identifier (can be None)

    Returns:
        A 64-character hex string (SHA-256 hash)
    """
    # Normalize inputs
    normalized_title = book_title.strip()
    normalized_author = (book_author or "").strip()
    normalized_device = (device_id or "").strip()

    # Create a consistent string representation for hashing
    hash_input = f"{normalized_title}|{normalized_author}|{start_time}|{normalized_device}"

    # Compute SHA-256 hash and return as hex string (64 chars)
    return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
