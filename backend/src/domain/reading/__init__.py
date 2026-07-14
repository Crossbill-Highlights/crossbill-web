"""Reading module domain layer."""

from .entities import Highlight, ReadingSession, Tag
from .services import HighlightDeduplicationService

__all__ = [
    "Highlight",
    "HighlightDeduplicationService",
    "ReadingSession",
    "Tag",
]
