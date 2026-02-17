"""HighlightStyle value object for highlight visual style.

Represents the visual style of a highlight as set by KOReader,
including color (e.g. "gray", "yellow") and style/drawer
(e.g. "lighten", "strikethrough", "underscore").
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Self


@dataclass(frozen=True)
class HighlightStyle:
    """Visual style of a highlight from KOReader."""

    color: str | None = None
    style: str | None = None

    def to_json(self) -> dict[str, str | None]:
        """Serialize to JSON-compatible dict."""
        return {"color": self.color, "style": self.style}

    @classmethod
    def from_json(cls, data: dict[str, str | None]) -> Self:
        """Deserialize from JSON dict."""
        return cls(color=data.get("color"), style=data.get("style"))

    @classmethod
    def default(cls) -> Self:
        """Create default style matching KOReader's default."""
        return cls(color="gray", style="lighten")
