"""Common value objects shared across all domain modules."""

from .content_hash import ContentHash
from .highlight_style import HighlightStyle
from .ids import (
    BookId,
    ChapterId,
    FlashcardId,
    HighlightId,
    HighlightTagId,
    PrereadingContentId,
    ReadingSessionId,
    TagId,
    UserId,
)
from .position import Position
from .position_index import PositionIndex
from .xpoint import XPoint, XPointRange

__all__ = [
    "BookId",
    "ChapterId",
    "ContentHash",
    "FlashcardId",
    "HighlightId",
    "HighlightStyle",
    "HighlightTagId",
    "Position",
    "PositionIndex",
    "PrereadingContentId",
    "ReadingSessionId",
    "TagId",
    "UserId",
    "XPoint",
    "XPointRange",
]
