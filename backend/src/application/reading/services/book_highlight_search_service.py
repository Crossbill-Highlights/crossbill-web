"""
Book-scoped highlight search application service.

Provides full-text search within a specific book's highlights.
"""

from sqlalchemy.orm import Session

from src.domain.common.value_objects import BookId, UserId
from src.domain.reading.services.highlight_grouping_service import (
    ChapterWithHighlights,
    HighlightGroupingService,
)
from src.exceptions import BookNotFoundError
from src.infrastructure.library.repositories.book_repository import BookRepository
from src.infrastructure.reading.repositories.highlight_repository import HighlightRepository


class BookHighlightSearchService:
    """Application service for searching highlights within a book."""

    def __init__(self, db: Session) -> None:
        """
        Initialize service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.book_repository = BookRepository(db)
        self.highlight_repository = HighlightRepository(db)
        self.highlight_grouping_service = HighlightGroupingService()

    def search_book_highlights(
        self, book_id: int, user_id: int, search_text: str, limit: int = 100
    ) -> tuple[list[ChapterWithHighlights], int]:
        """
        Search for highlights within a specific book using full-text search.

        Results are grouped by chapter, with only chapters containing
        matching highlights included in the response.

        Args:
            book_id: ID of the book to search within
            user_id: ID of the user
            search_text: Text to search for
            limit: Maximum number of results to return

        Returns:
            Tuple of (chapters with highlights, total highlight count)

        Raises:
            BookNotFoundError: If book is not found or doesn't belong to user
        """
        # Convert primitives to value objects
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        # Verify book exists and belongs to user
        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        # Search highlights (returns domain entities)
        highlights_with_context = self.highlight_repository.search(
            search_text=search_text,
            user_id=user_id_vo,
            book_id=book_id_vo,
            limit=limit,
        )

        # Use domain service to group highlights by chapter
        grouped = self.highlight_grouping_service.group_by_chapter(
            [(h, c, tags) for h, _, c, tags in highlights_with_context]
        )

        # Calculate total number of highlights
        total = sum(len(chapter_group.highlights) for chapter_group in grouped)

        return (grouped, total)
