"""Book repository for database operations."""

import logging
from collections.abc import Sequence

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

    def create(self, book_data: schemas.BookCreate, user_id: int) -> models.Book:
        """Create a new book."""
        book = models.Book(**book_data.model_dump(), user_id=user_id)
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
        self.db.flush()
        self.db.refresh(book)
        logger.info(f"Updated book: {book.title} (id={book.id})")
        return book

    def get_or_create(self, book_data: schemas.BookCreate, user_id: int) -> models.Book:
        """Get existing book by title, author, and user or create a new one."""
        book = self.find_by_title_and_author(book_data.title, book_data.author, user_id)

        if book:
            # Update metadata in case it changed
            return self.update(book, book_data)

        # Create new book
        return self.create(book_data, user_id)

    def get_books_with_highlight_count(
        self, user_id: int, offset: int = 0, limit: int = 100, search_text: str | None = None
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
