"""Reading module domain layer."""

from .entities import Highlight, HighlightTag, ReadingSession
from .services import HighlightDeduplicationService

__all__ = [
    "Highlight",
    "HighlightDeduplicationService",
    "HighlightTag",
    "ReadingSession",
]
