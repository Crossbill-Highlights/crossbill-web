"""
Search highlights use case.

Provides full-text search across user's highlights.
"""

from sqlalchemy.orm import Session

from src.domain.common.value_objects import BookId, UserId
from src.domain.library.entities.book import Book
from src.domain.library.entities.chapter import Chapter
from src.domain.reading.entities.highlight import Highlight
from src.domain.reading.entities.highlight_tag import HighlightTag
from src.infrastructure.reading.repositories.highlight_repository import HighlightRepository


class SearchHighlightsService:
    """Application service for searching highlights."""

    def __init__(self, db: Session) -> None:
        """
        Initialize service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.highlight_repository = HighlightRepository(db)

    def search(
        self,
        search_text: str,
        user_id: int,
        book_id: int | None = None,
        limit: int = 100,
    ) -> list[tuple[Highlight, Book, Chapter | None, list[HighlightTag]]]:
        """
        Search for highlights using full-text search.

        Args:
            search_text: Text to search for in highlights
            user_id: ID of the user whose highlights to search
            book_id: Optional book ID to filter by
            limit: Maximum number of results to return (default 100)

        Returns:
            List of tuples containing (Highlight entity, Book entity, Chapter entity or None, list[HighlightTag])
            ordered by relevance (PostgreSQL) or creation date (SQLite).
        """
        # Convert primitives to value objects
        user_id_vo = UserId(user_id)
        book_id_vo = BookId(book_id) if book_id is not None else None

        # Delegate to repository
        return self.highlight_repository.search(
            search_text=search_text,
            user_id=user_id_vo,
            book_id=book_id_vo,
            limit=limit,
        )
