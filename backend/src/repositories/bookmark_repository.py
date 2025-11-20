"""Bookmark repository for database operations."""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from src import models

logger = logging.getLogger(__name__)


class BookmarkRepository:
    """Repository for Bookmark database operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def get_by_id(self, bookmark_id: int) -> models.Bookmark | None:
        """Get a bookmark by its ID."""
        stmt = select(models.Bookmark).where(models.Bookmark.id == bookmark_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_book_id(self, book_id: int) -> list[models.Bookmark]:
        """Get all bookmarks for a specific book."""
        stmt = (
            select(models.Bookmark)
            .where(models.Bookmark.book_id == book_id)
            .order_by(models.Bookmark.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_by_book_and_highlight(self, book_id: int, highlight_id: int) -> models.Bookmark | None:
        """Get a bookmark by book_id and highlight_id."""
        stmt = select(models.Bookmark).where(
            models.Bookmark.book_id == book_id, models.Bookmark.highlight_id == highlight_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, book_id: int, highlight_id: int) -> models.Bookmark:
        """Create a new bookmark."""
        bookmark = models.Bookmark(book_id=book_id, highlight_id=highlight_id)
        self.db.add(bookmark)
        self.db.flush()
        self.db.refresh(bookmark)
        logger.info(
            f"Created bookmark: book_id={bookmark.book_id}, highlight_id={bookmark.highlight_id} (id={bookmark.id})"
        )
        return bookmark

    def delete(self, bookmark_id: int) -> bool:
        """Delete a bookmark by its ID. Returns True if deleted, False if not found."""
        bookmark = self.get_by_id(bookmark_id)
        if not bookmark:
            return False
        self.db.delete(bookmark)
        self.db.flush()
        logger.info(f"Deleted bookmark: id={bookmark_id}")
        return True
