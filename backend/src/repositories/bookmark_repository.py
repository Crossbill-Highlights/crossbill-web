"""Bookmark repository for database operations."""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from src import models

logger = logging.getLogger(__name__)


class BookmarkRepository:
    """Repository for Bookmark database operations.

    Note: Bookmarks don't have direct user_id. User ownership is verified
    through the book relationship.
    """

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def get_by_id(self, bookmark_id: int, user_id: int) -> models.Bookmark | None:
        """Get a bookmark by its ID, verifying user ownership through book."""
        stmt = (
            select(models.Bookmark)
            .join(models.Book, models.Bookmark.book_id == models.Book.id)
            .where(
                models.Bookmark.id == bookmark_id,
                models.Book.user_id == user_id,
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_book_id(self, book_id: int, user_id: int) -> list[models.Bookmark]:
        """Get all bookmarks for a specific book, verifying user ownership."""
        stmt = (
            select(models.Bookmark)
            .join(models.Book, models.Bookmark.book_id == models.Book.id)
            .where(
                models.Bookmark.book_id == book_id,
                models.Book.user_id == user_id,
            )
            .order_by(models.Bookmark.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_by_book_and_highlight(
        self, book_id: int, highlight_id: int, user_id: int
    ) -> models.Bookmark | None:
        """Get a bookmark by book_id and highlight_id, verifying user ownership."""
        stmt = (
            select(models.Bookmark)
            .join(models.Book, models.Bookmark.book_id == models.Book.id)
            .where(
                models.Bookmark.book_id == book_id,
                models.Bookmark.highlight_id == highlight_id,
                models.Book.user_id == user_id,
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, book_id: int, highlight_id: int, user_id: int) -> models.Bookmark:
        """Create a new bookmark.

        Note: Assumes book/highlight ownership has been verified by the caller.
        The user_id parameter is for logging purposes and future verification.
        """
        bookmark = models.Bookmark(book_id=book_id, highlight_id=highlight_id)
        self.db.add(bookmark)
        self.db.flush()
        self.db.refresh(bookmark)
        logger.info(
            f"Created bookmark: book_id={bookmark.book_id}, "
            f"highlight_id={bookmark.highlight_id} (id={bookmark.id}, user_id={user_id})"
        )
        return bookmark

    def delete(self, bookmark_id: int, user_id: int) -> bool:
        """Delete a bookmark by its ID, verifying user ownership.

        Returns True if deleted, False if not found or not owned by user.
        """
        bookmark = self.get_by_id(bookmark_id, user_id)
        if not bookmark:
            return False
        self.db.delete(bookmark)
        self.db.flush()
        logger.info(f"Deleted bookmark: id={bookmark_id}")
        return True
