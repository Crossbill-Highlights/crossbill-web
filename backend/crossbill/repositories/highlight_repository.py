"""Highlight repository for database operations."""

import logging
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from crossbill import models, schemas

logger = logging.getLogger(__name__)


class HighlightRepository:
    """Repository for Highlight database operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def create(self, book_id: int, highlight_data: schemas.HighlightCreate) -> models.Highlight:
        """Create a new highlight."""
        highlight = models.Highlight(
            book_id=book_id, **highlight_data.model_dump(exclude={"chapter", "chapter_number"})
        )
        self.db.add(highlight)
        self.db.flush()
        self.db.refresh(highlight)
        return highlight

    def create_with_chapter(
        self, book_id: int, chapter_id: int | None, highlight_data: schemas.HighlightCreate
    ) -> models.Highlight:
        """Create a new highlight with chapter association."""
        highlight = models.Highlight(
            book_id=book_id,
            chapter_id=chapter_id,
            **highlight_data.model_dump(exclude={"chapter", "chapter_number"}),
        )
        self.db.add(highlight)
        self.db.flush()
        self.db.refresh(highlight)
        return highlight

    def try_create(
        self, book_id: int, chapter_id: int | None, highlight_data: schemas.HighlightCreate
    ) -> tuple[models.Highlight | None, bool]:
        """
        Try to create a highlight.

        Returns:
            tuple[Highlight | None, bool]: (highlight, was_created)
            If duplicate (including soft-deleted), returns (None, False)
        """
        try:
            highlight = self.create_with_chapter(book_id, chapter_id, highlight_data)
            return highlight, True
        except IntegrityError:
            # Duplicate - unique constraint violated (active or soft-deleted)
            self.db.rollback()
            logger.debug(
                f"Skipped duplicate highlight for book_id={book_id}, "
                f"text='{highlight_data.text[:50]}...'"
            )
            return None, False

    def bulk_create(
        self, book_id: int, highlights_data: list[tuple[int | None, schemas.HighlightCreate]]
    ) -> tuple[int, int]:
        """
        Bulk create highlights with deduplication.

        Args:
            book_id: ID of the book
            highlights_data: List of (chapter_id, highlight_data) tuples

        Returns:
            tuple[int, int]: (created_count, skipped_count)
        """
        created = 0
        skipped = 0

        for chapter_id, highlight_data in highlights_data:
            _, was_created = self.try_create(book_id, chapter_id, highlight_data)
            if was_created:
                created += 1
            else:
                skipped += 1

        logger.info(
            f"Bulk created highlights for book_id={book_id}: "
            f"{created} created, {skipped} skipped"
        )
        return created, skipped

    def find_by_book(self, book_id: int) -> Sequence[models.Highlight]:
        """Find all non-deleted highlights for a book."""
        stmt = select(models.Highlight).where(
            models.Highlight.book_id == book_id, models.Highlight.deleted_at.is_(None)
        )
        return self.db.execute(stmt).scalars().all()

    def find_by_chapter(self, chapter_id: int) -> Sequence[models.Highlight]:
        """Find all non-deleted highlights for a chapter, ordered by datetime."""
        stmt = (
            select(models.Highlight)
            .where(models.Highlight.chapter_id == chapter_id, models.Highlight.deleted_at.is_(None))
            .order_by(models.Highlight.datetime)
        )
        return self.db.execute(stmt).scalars().all()

    def search(
        self, search_text: str, book_id: int | None = None, limit: int = 100
    ) -> Sequence[models.Highlight]:
        """
        Search for highlights using full-text search (PostgreSQL) or LIKE (SQLite).

        Args:
            search_text: Text to search for
            book_id: Optional book ID to filter by
            limit: Maximum number of results to return (default 100)

        Returns:
            Sequence of matching highlights with their relationships loaded
        """
        # Check database type
        is_postgresql = self.db.bind.dialect.name == "postgresql"

        # Build the base query with eager loading of relationships
        stmt = (
            select(models.Highlight)
            .join(models.Book)
            .outerjoin(models.Chapter, models.Highlight.chapter_id == models.Chapter.id)
            .where(models.Highlight.deleted_at.is_(None))
        )

        if is_postgresql:
            # PostgreSQL: Use full-text search
            search_query = func.plainto_tsquery("english", search_text)
            stmt = stmt.where(models.Highlight.text_search_vector.op("@@")(search_query))
        else:
            # SQLite: Use LIKE-based search
            stmt = stmt.where(models.Highlight.text.ilike(f"%{search_text}%"))

        # Add optional book_id filter
        if book_id is not None:
            stmt = stmt.where(models.Highlight.book_id == book_id)

        # Order by relevance and limit results
        if is_postgresql:
            search_query = func.plainto_tsquery("english", search_text)
            stmt = stmt.order_by(
                func.ts_rank(models.Highlight.text_search_vector, search_query).desc()
            )
        else:
            # SQLite: Order by created_at (newest first)
            stmt = stmt.order_by(models.Highlight.created_at.desc())

        stmt = stmt.limit(limit)

        return self.db.execute(stmt).scalars().all()

    def soft_delete_by_ids(self, book_id: int, highlight_ids: list[int]) -> int:
        """
        Soft delete highlights by their IDs for a specific book.

        Args:
            book_id: ID of the book (for validation)
            highlight_ids: List of highlight IDs to soft delete

        Returns:
            int: Number of highlights soft deleted
        """
        # Find highlights that belong to the book and are not already deleted
        stmt = select(models.Highlight).where(
            models.Highlight.id.in_(highlight_ids),
            models.Highlight.book_id == book_id,
            models.Highlight.deleted_at.is_(None),
        )
        highlights = self.db.execute(stmt).scalars().all()

        # Soft delete each highlight
        count = 0
        for highlight in highlights:
            highlight.deleted_at = datetime.now(UTC)
            count += 1

        self.db.flush()
        logger.info(f"Soft deleted {count} highlights for book_id={book_id}")
        return count
