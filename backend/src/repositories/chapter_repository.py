"""Chapter repository for database operations."""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from src import models

logger = logging.getLogger(__name__)


class ChapterRepository:
    """Repository for Chapter database operations.

    Note: Chapters don't have direct user_id. User ownership is verified
    through the book relationship where necessary.
    """

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def find_by_name_and_book(self, book_id: int, name: str, user_id: int) -> models.Chapter | None:
        """Find a chapter by name and book ID, verifying user ownership."""
        stmt = (
            select(models.Chapter)
            .join(models.Book, models.Chapter.book_id == models.Book.id)
            .where(
                models.Chapter.book_id == book_id,
                models.Chapter.name == name,
                models.Book.user_id == user_id,
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create(
        self, book_id: int, user_id: int, name: str, chapter_number: int | None = None
    ) -> models.Chapter:
        """Create a new chapter.

        Note: Assumes book ownership has been verified by the caller.
        """
        chapter = models.Chapter(book_id=book_id, name=name, chapter_number=chapter_number)
        self.db.add(chapter)
        self.db.flush()
        self.db.refresh(chapter)
        logger.info(f"Created chapter: {name} for book_id={book_id} (number={chapter_number})")
        return chapter

    def get_by_names(
        self, book_id: int, names: set[str], user_id: int
    ) -> dict[str, models.Chapter]:
        """Get multiple chapters by names for a book in one query.

        Returns a dictionary mapping chapter names to Chapter objects.
        """
        if not names:
            return {}

        stmt = (
            select(models.Chapter)
            .join(models.Book, models.Chapter.book_id == models.Book.id)
            .where(
                models.Chapter.book_id == book_id,
                models.Chapter.name.in_(names),
                models.Book.user_id == user_id,
            )
        )
        chapters = self.db.execute(stmt).scalars().all()
        return {chapter.name: chapter for chapter in chapters}

    def get_by_numbers(
        self, book_id: int, chapter_numbers: set[int], user_id: int
    ) -> dict[int, models.Chapter]:
        """Get multiple chapters by chapter_numbers for a book in one query.

        Returns a dictionary mapping chapter_number to Chapter objects.
        Used for accurate highlight-chapter association when chapter_number is available.
        """
        if not chapter_numbers:
            return {}

        stmt = (
            select(models.Chapter)
            .join(models.Book, models.Chapter.book_id == models.Book.id)
            .where(
                models.Chapter.book_id == book_id,
                models.Chapter.chapter_number.in_(chapter_numbers),
                models.Book.user_id == user_id,
            )
        )
        chapters = self.db.execute(stmt).scalars().all()
        return {
            chapter.chapter_number: chapter
            for chapter in chapters
            if chapter.chapter_number is not None
        }

    def bulk_create(
        self, book_id: int, user_id: int, chapter_data: list[tuple[str, int | None]]
    ) -> list[models.Chapter]:
        """Bulk create multiple chapters.

        Args:
            book_id: The book ID
            user_id: The user ID (for ownership verification)
            chapter_data: List of tuples (name, chapter_number)

        Returns:
            List of created Chapter objects
        """
        if not chapter_data:
            return []

        chapters = [
            models.Chapter(book_id=book_id, name=name, chapter_number=chapter_number)
            for name, chapter_number in chapter_data
        ]

        self.db.add_all(chapters)
        self.db.flush()

        logger.info(f"Bulk created {len(chapters)} chapters for book_id={book_id}")
        return chapters
