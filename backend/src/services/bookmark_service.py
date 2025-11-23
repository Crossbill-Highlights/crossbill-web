"""Service layer for bookmark-related business logic."""

import logging

from sqlalchemy.orm import Session

from src import repositories, schemas
from src.exceptions import BookNotFoundError, ValidationError

logger = logging.getLogger(__name__)


class BookmarkService:
    """Service for handling bookmark-related operations."""

    def __init__(self, db: Session) -> None:
        """Initialize service with database session."""
        self.db = db
        self.bookmark_repo = repositories.BookmarkRepository(db)
        self.book_repo = repositories.BookRepository(db)
        self.highlight_repo = repositories.HighlightRepository(db)

    def create_bookmark(self, book_id: int, highlight_id: int, user_id: int) -> schemas.Bookmark:
        """
        Create a new bookmark for a highlight in a book.

        Args:
            book_id: ID of the book
            highlight_id: ID of the highlight to bookmark
            user_id: ID of the user

        Returns:
            Created bookmark

        Raises:
            BookNotFoundError: If book is not found
            ValidationError: If highlight doesn't exist or doesn't belong to the book
        """
        # Validate book exists
        book = self.book_repo.get_by_id(book_id, user_id)
        if not book:
            raise BookNotFoundError(book_id)

        # Validate highlight exists and belongs to the book
        highlight = self.highlight_repo.get_by_id(highlight_id, user_id)
        if not highlight:
            raise ValidationError(f"Highlight with id {highlight_id} not found", status_code=404)

        if highlight.book_id != book_id:
            raise ValidationError(
                f"Highlight {highlight_id} does not belong to book {book_id}",
                status_code=400,
            )

        # Check if bookmark already exists
        existing_bookmark = self.bookmark_repo.get_by_book_and_highlight(
            book_id, highlight_id, user_id
        )
        if existing_bookmark:
            logger.info(
                f"Bookmark already exists for book {book_id}, highlight {highlight_id}, returning existing"
            )
            return schemas.Bookmark.model_validate(existing_bookmark)

        # Create bookmark
        bookmark = self.bookmark_repo.create(book_id, highlight_id, user_id)
        self.db.commit()

        logger.info(f"Created bookmark {bookmark.id} for book {book_id}, highlight {highlight_id}")
        return schemas.Bookmark.model_validate(bookmark)

    def delete_bookmark(self, book_id: int, bookmark_id: int, user_id: int) -> None:
        """
        Delete a bookmark. This operation is idempotent.

        Args:
            book_id: ID of the book (used for validation)
            bookmark_id: ID of the bookmark to delete
            user_id: ID of the user

        Raises:
            BookNotFoundError: If book is not found
        """
        # Validate book exists
        book = self.book_repo.get_by_id(book_id, user_id)
        if not book:
            raise BookNotFoundError(book_id)

        # Try to delete the bookmark (idempotent - returns False if not found)
        deleted = self.bookmark_repo.delete(bookmark_id, user_id)
        self.db.commit()

        if deleted:
            logger.info(f"Deleted bookmark {bookmark_id} from book {book_id}")
        else:
            logger.info(f"Bookmark {bookmark_id} not found for deletion (idempotent operation)")

    def get_bookmarks_by_book(self, book_id: int, user_id: int) -> schemas.BookmarksResponse:
        """
        Get all bookmarks for a specific book.

        Args:
            book_id: ID of the book
            user_id: ID of the user

        Returns:
            List of bookmarks

        Raises:
            BookNotFoundError: If book is not found
        """
        # Validate book exists
        book = self.book_repo.get_by_id(book_id, user_id)
        if not book:
            raise BookNotFoundError(book_id)

        bookmarks = self.bookmark_repo.get_by_book_id(book_id, user_id)
        return schemas.BookmarksResponse(
            bookmarks=[schemas.Bookmark.model_validate(b) for b in bookmarks]
        )
