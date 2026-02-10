"""
Book details aggregation domain service.

Provides dataclass for aggregating book data for detail view.
"""

from dataclasses import dataclass, field
from typing import Any

from src.domain.learning.entities.flashcard import Flashcard
from src.domain.library.entities.book import Book
from src.domain.reading.services.highlight_grouping_service import ChapterWithHighlights


@dataclass
class BookDetailsAggregation:
    """Aggregated book data for detail view."""

    book: Book
    tags: list[Any]  # Legacy ORM models (temporary)
    highlight_tags: list[Any]  # Legacy ORM models (temporary)
    highlight_tag_groups: list[Any]  # Legacy ORM models (temporary)
    bookmarks: list[Any]  # Legacy ORM models (temporary)
    chapters_with_highlights: list[ChapterWithHighlights]
    book_flashcards: list[Flashcard] = field(default_factory=list)
