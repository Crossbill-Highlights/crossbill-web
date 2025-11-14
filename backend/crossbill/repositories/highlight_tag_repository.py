"""HighlightTag repository for database operations."""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from crossbill import models

logger = logging.getLogger(__name__)


class HighlightTagRepository:
    """Repository for HighlightTag database operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def get_by_id(self, tag_id: int) -> models.HighlightTag | None:
        """Get a highlight tag by its ID."""
        stmt = select(models.HighlightTag).where(models.HighlightTag.id == tag_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_book_and_name(self, book_id: int, name: str) -> models.HighlightTag | None:
        """Get a highlight tag by book ID and name."""
        stmt = select(models.HighlightTag).where(
            models.HighlightTag.book_id == book_id,
            models.HighlightTag.name == name,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_book_id(self, book_id: int) -> list[models.HighlightTag]:
        """Get all highlight tags for a book."""
        stmt = (
            select(models.HighlightTag)
            .where(models.HighlightTag.book_id == book_id)
            .order_by(models.HighlightTag.name)
        )
        return list(self.db.execute(stmt).scalars().all())

    def create(self, book_id: int, name: str) -> models.HighlightTag:
        """Create a new highlight tag."""
        tag = models.HighlightTag(book_id=book_id, name=name)
        self.db.add(tag)
        self.db.flush()
        self.db.refresh(tag)
        logger.info(f"Created highlight tag: {tag.name} (id={tag.id}, book_id={book_id})")
        return tag

    def get_or_create(self, book_id: int, name: str) -> models.HighlightTag:
        """Get existing highlight tag by book and name or create a new one."""
        tag = self.get_by_book_and_name(book_id, name)
        if tag:
            return tag
        return self.create(book_id, name)

    def delete(self, tag_id: int) -> bool:
        """Delete a highlight tag by ID."""
        tag = self.get_by_id(tag_id)
        if not tag:
            return False
        self.db.delete(tag)
        self.db.flush()
        logger.info(f"Deleted highlight tag: {tag.name} (id={tag_id})")
        return True
