"""Chapter repository for database operations."""

import logging
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from crossbill import models

logger = logging.getLogger(__name__)


class ChapterRepository:
    """Repository for Chapter database operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def find_by_name_and_book(self, book_id: int, name: str) -> models.Chapter | None:
        """Find a chapter by name and book ID."""
        stmt = select(models.Chapter).where(
            models.Chapter.book_id == book_id, models.Chapter.name == name
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create(
        self, book_id: int, name: str, chapter_number: int | None = None
    ) -> models.Chapter:
        """Create a new chapter."""
        chapter = models.Chapter(book_id=book_id, name=name, chapter_number=chapter_number)
        self.db.add(chapter)
        self.db.flush()
        self.db.refresh(chapter)
        logger.info(f"Created chapter: {name} for book_id={book_id} (number={chapter_number})")
        return chapter

    def update_chapter_number(self, chapter_id: int, chapter_number: int | None) -> models.Chapter:
        """Update the chapter number for an existing chapter."""
        stmt = select(models.Chapter).where(models.Chapter.id == chapter_id)
        chapter = self.db.execute(stmt).scalar_one_or_none()
        if chapter:
            chapter.chapter_number = chapter_number
            self.db.flush()
            self.db.refresh(chapter)
            logger.info(f"Updated chapter {chapter_id} number to {chapter_number}")
        return chapter

    def get_or_create(
        self, book_id: int, name: str, chapter_number: int | None = None
    ) -> models.Chapter:
        """Get existing chapter by name and book or create a new one."""
        chapter = self.find_by_name_and_book(book_id, name)

        if chapter:
            # Update chapter number if it's different
            if chapter_number is not None and chapter.chapter_number != chapter_number:
                chapter.chapter_number = chapter_number
                self.db.flush()
                self.db.refresh(chapter)
                logger.info(
                    f"Updated chapter number for '{name}' (book_id={book_id}) to {chapter_number}"
                )
            return chapter

        try:
            return self.create(book_id, name, chapter_number)
        except IntegrityError:
            # Handle race condition: another request created the chapter
            self.db.rollback()
            chapter = self.find_by_name_and_book(book_id, name)
            if chapter:
                # Update chapter number if it's different
                if chapter_number is not None and chapter.chapter_number != chapter_number:
                    chapter.chapter_number = chapter_number
                    self.db.flush()
                    self.db.refresh(chapter)
                return chapter
            raise

    def get_by_book_id(self, book_id: int) -> Sequence[models.Chapter]:
        """Get all chapters for a book, ordered by chapter_number if available."""
        stmt = (
            select(models.Chapter)
            .where(models.Chapter.book_id == book_id)
            .order_by(
                # Order by chapter_number if available, otherwise by name
                # NULL chapter_numbers go to the end
                models.Chapter.chapter_number.is_(None),
                models.Chapter.chapter_number,
                models.Chapter.name,
            )
        )
        return self.db.execute(stmt).scalars().all()
