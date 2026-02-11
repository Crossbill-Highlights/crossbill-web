"""PositionIndex - resolves xpoint strings to Position values."""

from __future__ import annotations

import re

from src.domain.common.value_objects.position import Position
from src.domain.common.value_objects.xpoint import XPoint

# Matches an xpath segment like "body", "div", "p[2]" - captures tag name
# and optional bracket index.
_SEGMENT_RE = re.compile(r"^([a-zA-Z][a-zA-Z0-9_-]*)(\[\d+\])?$")


def _normalize_xpath(xpath: str) -> str:
    """Normalize an xpath by adding explicit [1] indices where omitted.

    lxml always produces explicit indices (e.g. /body/p[1]/span[1])
    while KOReader xpoints may omit [1] (e.g. /body/p/span).
    This function ensures both forms map to the same key.

    Args:
        xpath: XPath like "/body/div/p" or "/body/div[1]/p[2]"

    Returns:
        Normalized xpath like "/body/div[1]/p[1]" or "/body/div[1]/p[2]"
    """
    if not xpath:
        return xpath

    parts = xpath.split("/")
    normalized: list[str] = []
    for part in parts:
        if not part:
            normalized.append("")
            continue
        match = _SEGMENT_RE.match(part)
        if match:
            tag = match.group(1)
            index = match.group(2)
            if index is None:
                normalized.append(f"{tag}[1]")
            else:
                normalized.append(part)
        else:
            normalized.append(part)
    return "/".join(normalized)


class PositionIndex:
    """Maps xpoint strings to document-order positions.

    Built by infrastructure services (e.g., EpubPositionIndexService).
    Used by application layer use cases to assign positions to entities.
    """

    def __init__(self, element_positions: dict[tuple[int, str], int]) -> None:
        """
        Args:
            element_positions: mapping from (doc_fragment_index, xpath) to element index.
                Xpaths are normalized (explicit [1] indices added) on construction.
        """
        self._element_positions = {
            (frag, _normalize_xpath(xpath)): idx for (frag, xpath), idx in element_positions.items()
        }

    def resolve(self, xpoint_str: str) -> Position | None:
        """Resolve an xpoint string to a Position.

        Args:
            xpoint_str: xpoint string like "/body/DocFragment[14]/body/div[1]/p[3]/text().50"

        Returns:
            Position or None if the xpoint cannot be resolved
        """
        try:
            xpoint = XPoint.parse(xpoint_str)
        except Exception:
            return None

        doc_frag = xpoint.doc_fragment_index if xpoint.doc_fragment_index is not None else 1
        normalized_xpath = _normalize_xpath(xpoint.xpath)
        key = (doc_frag, normalized_xpath)

        element_index = self._element_positions.get(key)
        if element_index is None:
            return None

        char_index = xpoint.char_offset

        return Position(index=element_index, char_index=char_index)
