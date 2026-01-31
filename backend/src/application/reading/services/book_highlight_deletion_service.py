"""
Book highlight deletion application service.

Handles soft deletion of highlights with cascade to bookmarks/flashcards.
"""

from sqlalchemy.orm import Session

from src.domain.common.value_objects import BookId, HighlightId, UserId
from src.exceptions import BookNotFoundError
from src.infrastructure.library.repositories.book_repository import BookRepository
from src.infrastructure.reading.repositories.highlight_repository import HighlightRepository


class BookHighlightDeletionService:
    """Application service for deleting highlights from a book."""

    def __init__(self, db: Session) -> None:
        """
        Initialize service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.book_repository = BookRepository(db)
        self.highlight_repository = HighlightRepository(db)

    def delete_highlights(
        self, book_id: int, highlight_ids: list[int], user_id: int
    ) -> int:
        """
        Soft delete highlights from a book.

        This performs a soft delete by marking the highlights as deleted.
        When syncing highlights, deleted highlights will not be recreated,
        ensuring that user deletions persist across syncs.

        Also cascades to delete all bookmarks and flashcards associated with
        the deleted highlights.

        Args:
            book_id: ID of the book
            highlight_ids: List of highlight IDs to delete
            user_id: ID of the user

        Returns:
            Number of highlights deleted

        Raises:
            BookNotFoundError: If book is not found
        """
        # Convert primitives to value objects
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)
        highlight_ids_vo = [HighlightId(hid) for hid in highlight_ids]

        # Verify book exists
        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        # Soft delete highlights (cascades to bookmarks and flashcards)
        return self.highlight_repository.soft_delete_by_ids(
            highlight_ids=highlight_ids_vo,
            user_id=user_id_vo,
            book_id=book_id_vo,
        )
