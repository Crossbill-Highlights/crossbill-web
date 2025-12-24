"""Book repository for database operations."""

import logging
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.engine import Row
from sqlalchemy.orm import Session

from src import models, schemas

logger = logging.getLogger(__name__)


class BookRepository:
    """Repository for Book database operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def find_by_title_and_author(
        self, title: str, author: str | None, user_id: int
    ) -> models.Book | None:
        """Find a book by its title, author, and user."""
        stmt = select(models.Book).where(
            models.Book.title == title,
            models.Book.author == author,
            models.Book.user_id == user_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def find_by_content_hash(self, content_hash: str, user_id: int) -> models.Book | None:
        """Find a book by its content hash and user."""
        stmt = select(models.Book).where(
            models.Book.content_hash == content_hash,
            models.Book.user_id == user_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, book_data: schemas.BookCreate, content_hash: str, user_id: int) -> models.Book:
        """Create a new book."""
        # Exclude keywords as they are handled separately via TagService
        book_dict = book_data.model_dump(exclude={"keywords"})
        book = models.Book(**book_dict, content_hash=content_hash, user_id=user_id)
        self.db.add(book)
        self.db.flush()
        self.db.refresh(book)
        logger.info(f"Created book: {book.title} (id={book.id}, user_id={user_id})")
        return book

    def update(self, book: models.Book, book_data: schemas.BookCreate) -> models.Book:
        """Update an existing book's metadata."""
        book.title = book_data.title
        book.author = book_data.author
        book.isbn = book_data.isbn
        book.description = book_data.description
        book.language = book_data.language
        book.page_count = book_data.page_count
        self.db.flush()
        self.db.refresh(book)
        logger.info(f"Updated book: {book.title} (id={book.id})")
        return book

    def get_or_create(
        self, book_data: schemas.BookCreate, content_hash: str, user_id: int
    ) -> tuple[models.Book, bool]:
        """Get existing book by content hash and user or create a new one.

        The content_hash is computed from the original title and author at upload time.
        This allows book metadata (title, author) to be edited later without breaking
        deduplication - the hash identifies the same book across uploads.

        Note: When an existing book is found, its metadata is NOT updated. This preserves
        any edits the user has made to the book's title/author in the app.

        Returns:
            tuple[Book, bool]: (book, created) where created is True if a new book was created
        """
        book = self.find_by_content_hash(content_hash, user_id)

        if book:
            # Return existing book without updating metadata
            # This preserves any user edits to the book's title/author
            logger.debug(f"Found existing book by hash: {book.title} (id={book.id})")
            return book, False

        # Create new book with the computed hash
        return self.create(book_data, content_hash, user_id), True

    def get_books_with_highlight_count(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 100,
        search_text: str | None = None,
    ) -> tuple[Sequence[Row[tuple[models.Book, int]]], int]:
        """
        Get books with their highlight counts for a specific user, sorted alphabetically by title.

        Args:
            user_id: ID of the user whose books to retrieve
            offset: Number of books to skip (default: 0)
            limit: Maximum number of books to return (default: 100)
            search_text: Optional text to search for in book title or author (case-insensitive)

        Returns:
            tuple[Sequence[tuple[Book, int]], int]: (list of (book, count) tuples, total count)
        """
        # Build base filter conditions - always filter by user
        filters = [models.Book.user_id == user_id]
        if search_text:
            search_pattern = f"%{search_text}%"
            filters.append(
                (models.Book.title.ilike(search_pattern))
                | (models.Book.author.ilike(search_pattern))
            )

        # Count query for total number of books
        total_stmt = select(func.count(models.Book.id)).where(*filters)
        total = self.db.execute(total_stmt).scalar() or 0

        # Main query for books with highlight counts (excluding soft-deleted highlights)
        stmt = (
            select(models.Book, func.count(models.Highlight.id).label("highlight_count"))
            .outerjoin(
                models.Highlight,
                (models.Book.id == models.Highlight.book_id)
                & (models.Highlight.deleted_at.is_(None)),
            )
            .where(*filters)
            .group_by(models.Book.id)
            .order_by(models.Book.title)
            .offset(offset)
            .limit(limit)
        )

        result = self.db.execute(stmt).all()
        return result, total

    def get_by_id(self, book_id: int, user_id: int) -> models.Book | None:
        """Get a book by its ID for a specific user."""
        stmt = select(models.Book).where(
            models.Book.id == book_id,
            models.Book.user_id == user_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def delete(self, book_id: int, user_id: int) -> bool:
        """
        Delete a book by its ID for a specific user (hard delete).

        Args:
            book_id: ID of the book to delete
            user_id: ID of the user who owns the book

        Returns:
            bool: True if book was deleted, False if book was not found
        """
        book = self.get_by_id(book_id, user_id)
        if not book:
            return False

        self.db.delete(book)
        self.db.flush()
        logger.info(f"Deleted book: {book.title} (id={book.id}, user_id={user_id})")
        return True

    def update_last_viewed(self, book_id: int, user_id: int) -> models.Book | None:
        """
        Update the last_viewed timestamp for a book.

        Args:
            book_id: ID of the book to update
            user_id: ID of the user who owns the book

        Returns:
            Updated book or None if not found
        """
        book = self.get_by_id(book_id, user_id)
        if not book:
            return None

        book.last_viewed = datetime.now(UTC)
        self.db.flush()
        logger.debug(f"Updated last_viewed for book: {book.title} (id={book.id})")
        return book

    def get_recently_viewed_books(
        self, user_id: int, limit: int = 10
    ) -> Sequence[Row[tuple[models.Book, int]]]:
        """
        Get recently viewed books with their highlight counts for a specific user.

        Only returns books that have been viewed (last_viewed is not NULL).

        Args:
            user_id: ID of the user whose books to retrieve
            limit: Maximum number of books to return (default: 10)

        Returns:
            Sequence of (book, highlight_count) tuples ordered by last_viewed DESC
        """
        stmt = (
            select(models.Book, func.count(models.Highlight.id).label("highlight_count"))
            .outerjoin(
                models.Highlight,
                (models.Book.id == models.Highlight.book_id)
                & (models.Highlight.deleted_at.is_(None)),
            )
            .where(
                models.Book.user_id == user_id,
                models.Book.last_viewed.isnot(None),
            )
            .group_by(models.Book.id)
            .order_by(models.Book.last_viewed.desc())
            .limit(limit)
        )

        return self.db.execute(stmt).all()
