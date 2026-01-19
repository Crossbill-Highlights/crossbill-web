"""Utility functions for the backend."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.exceptions import XPointParseError

if TYPE_CHECKING:
    from typing import Self

# Regex pattern for parsing XPath segments like "div", "div[1]", "p[15]"
_XPATH_SEGMENT_PATTERN = re.compile(r"([a-zA-Z][a-zA-Z0-9_-]*)(?:\[(\d+)\])?$")


# Regex pattern for parsing xpoint strings
# Format: /body/DocFragment[N]/body/.../text()[N].offset
# Or: /body/DocFragment[N]/body/... (element boundary, defaults to offset 0)
# DocFragment, text node index, and text()/offset are optional
_XPOINT_PATTERN = re.compile(
    r"^"
    r"(?:/body/DocFragment\[(\d+)\])?"  # Optional DocFragment[N] - group 1
    r"(/body(?:/[^/.\s()]+)*)"  # XPath: /body followed by /element segments (no dots/parens)
    r"(?:/text\(\)(?:\[(\d+)\])?"  # Optional: text() with optional [N] - group 3
    r"\.(\d+))?"  # Optional: .offset - group 4
    r"$"
)


@dataclass(frozen=True)
class ParsedXPoint:
    """Parsed representation of a KOReader xpoint string.

    XPoints are position references used by KOReader to mark locations in EPUB documents.
    Formats:
    - /body/DocFragment[12]/body/div/p[88]/text().223 (full format with offset)
    - /body/DocFragment[14]/body/a (element boundary, offset defaults to 0)

    Attributes:
        doc_fragment_index: 1-based index into EPUB spine (None if not present)
        xpath: XPath to the element (without text() selector)
        text_node_index: 1-based index of text node within element (default 1)
        char_offset: 0-based character offset within text node (default 0)
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
        - /body/DocFragment[14]/body/a (element boundary, defaults to offset 0)

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
        # When /text().offset is omitted, default to offset 0 (element boundary)
        char_offset = int(offset_str) if offset_str else 0

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


def _parse_xpath_segments(xpath: str) -> list[tuple[str, int]]:
    """Parse an XPath string into a list of (element_name, index) tuples.

    Args:
        xpath: XPath string like "/body/div[2]/section[1]/article/p[15]"

    Returns:
        List of tuples like [("body", 1), ("div", 2), ("section", 1), ("article", 1), ("p", 15)]
        Elements without explicit index default to 1.
    """
    # Split by "/" and filter out empty strings
    parts = [p for p in xpath.split("/") if p]
    segments: list[tuple[str, int]] = []

    for part in parts:
        match = _XPATH_SEGMENT_PATTERN.match(part)
        if match:
            element_name = match.group(1)
            index = int(match.group(2)) if match.group(2) else 1
            segments.append((element_name, index))
        else:
            # Fallback: treat as element with index 1
            segments.append((part, 1))

    return segments


def compare_xpoints(xpoint1: str, xpoint2: str) -> int:
    """Compare two xpoint strings for ordering.

    This function parses both xpoints and compares them component by component
    to determine their relative order in the document.

    Args:
        xpoint1: First xpoint string
        xpoint2: Second xpoint string

    Returns:
        -1 if xpoint1 < xpoint2 (xpoint1 comes before xpoint2)
         0 if xpoint1 == xpoint2 (same position)
         1 if xpoint1 > xpoint2 (xpoint1 comes after xpoint2)

    Raises:
        XPointParseError: If either xpoint string is invalid
    """
    parsed1 = ParsedXPoint.parse(xpoint1)
    parsed2 = ParsedXPoint.parse(xpoint2)

    return compare_parsed_xpoints(parsed1, parsed2)


def compare_parsed_xpoints(parsed1: ParsedXPoint, parsed2: ParsedXPoint) -> int:
    """Compare two ParsedXPoint objects for ordering.

    Comparison order:
    1. doc_fragment_index (None treated as 1)
    2. XPath segments (element name, then index for each segment)
    3. text_node_index
    4. char_offset

    Args:
        parsed1: First parsed xpoint
        parsed2: Second parsed xpoint

    Returns:
        -1 if parsed1 < parsed2 (parsed1 comes before parsed2)
         0 if parsed1 == parsed2 (same position)
         1 if parsed1 > parsed2 (parsed1 comes after parsed2)
    """
    # Compare doc_fragment_index (None treated as 1)
    frag1 = parsed1.doc_fragment_index if parsed1.doc_fragment_index is not None else 1
    frag2 = parsed2.doc_fragment_index if parsed2.doc_fragment_index is not None else 1

    if frag1 != frag2:
        return -1 if frag1 < frag2 else 1

    # Compare XPath segments
    segments1 = _parse_xpath_segments(parsed1.xpath)
    segments2 = _parse_xpath_segments(parsed2.xpath)

    # Compare segment by segment
    for seg1, seg2 in zip(segments1, segments2):
        name1, idx1 = seg1
        name2, idx2 = seg2

        # First compare element names (alphabetically)
        if name1 != name2:
            return -1 if name1 < name2 else 1

        # Then compare indices
        if idx1 != idx2:
            return -1 if idx1 < idx2 else 1

    # If one xpath has more segments, the shorter one comes first
    if len(segments1) != len(segments2):
        return -1 if len(segments1) < len(segments2) else 1

    # Compare text_node_index
    if parsed1.text_node_index != parsed2.text_node_index:
        return -1 if parsed1.text_node_index < parsed2.text_node_index else 1

    # Compare char_offset
    if parsed1.char_offset != parsed2.char_offset:
        return -1 if parsed1.char_offset < parsed2.char_offset else 1

    return 0


def is_xpoint_in_range(
    xpoint: str, range_start: str, range_end: str, *, inclusive: bool = True
) -> bool:
    """Check if an xpoint falls within a given range.

    Args:
        xpoint: The xpoint to check
        range_start: The start of the range
        range_end: The end of the range
        inclusive: If True, range includes start and end points (default True)

    Returns:
        True if xpoint is within the range, False otherwise

    Raises:
        XPointParseError: If any xpoint string is invalid
    """
    cmp_start = compare_xpoints(xpoint, range_start)
    cmp_end = compare_xpoints(xpoint, range_end)

    if inclusive:
        return cmp_start >= 0 and cmp_end <= 0
    else:
        return cmp_start > 0 and cmp_end < 0


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
