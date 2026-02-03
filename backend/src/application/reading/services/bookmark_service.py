"""Application service for bookmark operations."""

import structlog

from src.application.reading.protocols.book_repository import BookRepositoryProtocol
from src.application.reading.protocols.bookmark_repository import BookmarkRepositoryProtocol
from src.application.reading.protocols.highlight_repository import HighlightRepositoryProtocol
from src.domain.common.value_objects.ids import BookId, BookmarkId, HighlightId, UserId
from src.domain.reading.entities.bookmark import Bookmark
from src.exceptions import BookNotFoundError, ValidationError

logger = structlog.get_logger(__name__)


class BookmarkService:
    """Application service for bookmark CRUD operations."""

    def __init__(
        self,
        book_repository: BookRepositoryProtocol,
        bookmark_repository: BookmarkRepositoryProtocol,
        highlight_repository: HighlightRepositoryProtocol,
    ) -> None:
        """Initialize service with database session."""
        self.book_repository = book_repository
        self.bookmark_repository = bookmark_repository
        self.highlight_repository = highlight_repository

    def create_bookmark(self, book_id: int, highlight_id: int, user_id: int) -> Bookmark:
        """
        Create a new bookmark for a highlight.

        Args:
            book_id: ID of the book
            highlight_id: ID of the highlight to bookmark
            user_id: ID of the user

        Returns:
            Created bookmark (or existing if already exists)

        Raises:
            BookNotFoundError: If book is not found
            ValidationError: If highlight doesn't exist or doesn't belong to the book
        """
        # Convert to value objects
        book_id_vo = BookId(book_id)
        highlight_id_vo = HighlightId(highlight_id)
        user_id_vo = UserId(user_id)

        # Validate book exists and belongs to user
        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        # Validate highlight exists and belongs to user
        highlight = self.highlight_repository.find_by_id(highlight_id_vo, user_id_vo)
        if not highlight:
            raise ValidationError(f"Highlight with id {highlight_id} not found", status_code=404)

        # Validate highlight belongs to the book
        if highlight.book_id != book_id_vo:
            raise ValidationError(
                f"Highlight {highlight_id} does not belong to book {book_id}",
                status_code=400,
            )

        # Check if bookmark already exists (idempotent)
        existing = self.bookmark_repository.find_by_book_and_highlight(book_id_vo, highlight_id_vo)
        if existing:
            logger.info(
                "bookmark_already_exists",
                book_id=book_id,
                highlight_id=highlight_id,
                bookmark_id=existing.id.value,
            )
            return existing

        # Create new bookmark
        bookmark = Bookmark.create(book_id=book_id_vo, highlight_id=highlight_id_vo)
        bookmark = self.bookmark_repository.save(bookmark)

        logger.info(
            "created_bookmark",
            bookmark_id=bookmark.id.value,
            book_id=book_id,
            highlight_id=highlight_id,
        )
        return bookmark

    def delete_bookmark(self, book_id: int, bookmark_id: int, user_id: int) -> None:
        """
        Delete a bookmark (idempotent operation).

        Args:
            book_id: ID of the book (for validation)
            bookmark_id: ID of the bookmark to delete
            user_id: ID of the user

        Raises:
            BookNotFoundError: If book is not found
        """
        # Convert to value objects
        book_id_vo = BookId(book_id)
        bookmark_id_vo = BookmarkId(bookmark_id)
        user_id_vo = UserId(user_id)

        # Validate book exists and belongs to user
        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        # Delete bookmark (idempotent)
        deleted = self.bookmark_repository.delete(bookmark_id_vo, user_id_vo)

        if deleted:
            logger.info("deleted_bookmark", bookmark_id=bookmark_id, book_id=book_id)
        else:
            logger.info(
                "bookmark_not_found_for_deletion",
                bookmark_id=bookmark_id,
                book_id=book_id,
            )

    def get_bookmarks_by_book(self, book_id: int, user_id: int) -> list[Bookmark]:
        """
        Get all bookmarks for a book.

        Args:
            book_id: ID of the book
            user_id: ID of the user

        Returns:
            List of bookmark entities

        Raises:
            BookNotFoundError: If book is not found
        """
        # Convert to value objects
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        # Validate book exists and belongs to user
        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        # Get bookmarks
        return self.bookmark_repository.find_by_book(book_id_vo, user_id_vo)
