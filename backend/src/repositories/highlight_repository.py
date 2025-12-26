"""Highlight repository for database operations."""

import logging
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from src import models, schemas

logger = logging.getLogger(__name__)


class HighlightRepository:
    """Repository for Highlight database operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def create(
        self,
        book_id: int,
        user_id: int,
        content_hash: str,
        highlight_data: schemas.HighlightCreate,
    ) -> models.Highlight:
        """Create a new highlight."""
        highlight = models.Highlight(
            book_id=book_id,
            user_id=user_id,
            content_hash=content_hash,
            **highlight_data.model_dump(exclude={"chapter", "chapter_number"}),
        )
        self.db.add(highlight)
        self.db.flush()
        self.db.refresh(highlight)
        return highlight

    def create_with_chapter(
        self,
        book_id: int,
        user_id: int,
        chapter_id: int | None,
        content_hash: str,
        highlight_data: schemas.HighlightCreate,
    ) -> models.Highlight:
        """Create a new highlight with chapter association."""
        highlight = models.Highlight(
            book_id=book_id,
            user_id=user_id,
            chapter_id=chapter_id,
            content_hash=content_hash,
            **highlight_data.model_dump(exclude={"chapter", "chapter_number"}),
        )
        self.db.add(highlight)
        self.db.flush()
        self.db.refresh(highlight)
        return highlight

    def try_create(
        self,
        book_id: int,
        user_id: int,
        chapter_id: int | None,
        content_hash: str,
        highlight_data: schemas.HighlightCreate,
    ) -> tuple[models.Highlight | None, bool]:
        """
        Try to create a highlight.

        Returns:
            tuple[Highlight | None, bool]: (highlight, was_created)
            If duplicate (including soft-deleted), returns (None, False)
        """
        # Use a savepoint to isolate this insert
        # This way, if it fails, we only rollback this specific insert
        # and not all previous work in the transaction
        savepoint = self.db.begin_nested()
        try:
            highlight = self.create_with_chapter(
                book_id, user_id, chapter_id, content_hash, highlight_data
            )
            return highlight, True
        except IntegrityError:
            # Duplicate - unique constraint violated (active or soft-deleted)
            # Rollback only to the savepoint, not the entire transaction
            savepoint.rollback()
            logger.debug(
                f"Skipped duplicate highlight for book_id={book_id}, content_hash='{content_hash}'"
            )
            return None, False

    def bulk_create(
        self,
        book_id: int,
        user_id: int,
        highlights_data: list[tuple[int | None, str, schemas.HighlightCreate]],
    ) -> tuple[int, int]:
        """
        Bulk create highlights with deduplication.

        Args:
            book_id: ID of the book
            user_id: ID of the user
            highlights_data: List of (chapter_id, content_hash, highlight_data) tuples

        Returns:
            tuple[int, int]: (created_count, skipped_count)
        """
        created = 0
        skipped = 0

        for chapter_id, content_hash, highlight_data in highlights_data:
            _, was_created = self.try_create(
                book_id, user_id, chapter_id, content_hash, highlight_data
            )
            if was_created:
                created += 1
            else:
                skipped += 1

        logger.info(
            f"Bulk created highlights for book_id={book_id}: {created} created, {skipped} skipped"
        )
        return created, skipped

    def get_by_id(self, highlight_id: int, user_id: int) -> models.Highlight | None:
        """Get a highlight by its ID for a specific user (including soft-deleted ones)."""
        stmt = select(models.Highlight).where(
            models.Highlight.id == highlight_id,
            models.Highlight.user_id == user_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def find_by_book(self, book_id: int, user_id: int) -> Sequence[models.Highlight]:
        """Find all non-deleted highlights for a book owned by the user."""
        stmt = select(models.Highlight).where(
            models.Highlight.book_id == book_id,
            models.Highlight.user_id == user_id,
            models.Highlight.deleted_at.is_(None),
        )
        return self.db.execute(stmt).scalars().all()

    def find_by_book_with_relationships(
        self, book_id: int, user_id: int
    ) -> Sequence[models.Highlight]:
        """Find all non-deleted highlights for a book with relationships loaded, ordered by datetime."""
        stmt = (
            select(models.Highlight)
            .options(
                selectinload(models.Highlight.flashcards),
                selectinload(models.Highlight.highlight_tags),
            )
            .where(
                models.Highlight.book_id == book_id,
                models.Highlight.user_id == user_id,
                models.Highlight.deleted_at.is_(None),
            )
            .order_by(models.Highlight.datetime)
        )
        return self.db.execute(stmt).scalars().all()

    def count_by_book_id(self, book_id: int, user_id: int) -> int:
        """Count all non-deleted highlights for a book owned by the user."""
        stmt = select(func.count(models.Highlight.id)).where(
            models.Highlight.book_id == book_id,
            models.Highlight.user_id == user_id,
            models.Highlight.deleted_at.is_(None),
        )
        return self.db.execute(stmt).scalar() or 0

    def search(
        self, search_text: str, user_id: int, book_id: int | None = None, limit: int = 100
    ) -> Sequence[models.Highlight]:
        """
        Search for highlights using full-text search (PostgreSQL) or LIKE (SQLite).

        Args:
            search_text: Text to search for
            user_id: ID of the user whose highlights to search
            book_id: Optional book ID to filter by
            limit: Maximum number of results to return (default 100)

        Returns:
            Sequence of matching highlights with their relationships loaded
        """
        # Check database type
        is_postgresql = self.db.bind is not None and self.db.bind.dialect.name == "postgresql"

        # Build the base query with eager loading of relationships
        stmt = (
            select(models.Highlight)
            .join(models.Book)
            .outerjoin(models.Chapter, models.Highlight.chapter_id == models.Chapter.id)
            .where(
                models.Highlight.user_id == user_id,
                models.Highlight.deleted_at.is_(None),
            )
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

    def soft_delete_by_ids(self, book_id: int, user_id: int, highlight_ids: list[int]) -> int:
        """
        Soft delete highlights by their IDs for a specific book and user.

        Also deletes all bookmarks and flashcards associated with the deleted highlights,
        as soft-deleted highlights should not have active bookmarks or flashcards.

        Args:
            book_id: ID of the book (for validation)
            user_id: ID of the user who owns the highlights
            highlight_ids: List of highlight IDs to soft delete

        Returns:
            int: Number of highlights soft deleted
        """
        # Subquery to get valid highlight IDs (belong to book/user, not already deleted)
        valid_highlight_ids_subquery = (
            select(models.Highlight.id)
            .where(
                models.Highlight.id.in_(highlight_ids),
                models.Highlight.book_id == book_id,
                models.Highlight.user_id == user_id,
                models.Highlight.deleted_at.is_(None),
            )
            .scalar_subquery()
        )

        # Bulk delete all bookmarks for valid highlights
        stmt_delete_bookmarks = delete(models.Bookmark).where(
            models.Bookmark.highlight_id.in_(valid_highlight_ids_subquery)
        )
        result = self.db.execute(stmt_delete_bookmarks)
        bookmarks_deleted = getattr(result, "rowcount", 0) or 0

        # Bulk delete all flashcards for valid highlights
        stmt_delete_flashcards = delete(models.Flashcard).where(
            models.Flashcard.highlight_id.in_(valid_highlight_ids_subquery)
        )
        result = self.db.execute(stmt_delete_flashcards)
        flashcards_deleted = getattr(result, "rowcount", 0) or 0

        # Bulk soft delete all valid highlights in a single query
        stmt_soft_delete = (
            update(models.Highlight)
            .where(
                models.Highlight.id.in_(highlight_ids),
                models.Highlight.book_id == book_id,
                models.Highlight.user_id == user_id,
                models.Highlight.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(UTC))
        )
        result = self.db.execute(stmt_soft_delete)
        count = getattr(result, "rowcount", 0) or 0

        self.db.flush()
        logger.info(
            f"Soft deleted {count} highlights, {bookmarks_deleted} associated bookmarks, "
            f"and {flashcards_deleted} associated flashcards for book_id={book_id}, user_id={user_id}"
        )
        return count

    def update_note(
        self, highlight_id: int, user_id: int, note: str | None
    ) -> models.Highlight | None:
        """
        Update the note field of a highlight.

        Args:
            highlight_id: ID of the highlight to update
            user_id: ID of the user who owns the highlight
            note: New note text (or None to clear)

        Returns:
            Updated highlight or None if not found or already deleted
        """
        # Get the highlight (excluding soft-deleted ones)
        stmt = select(models.Highlight).where(
            models.Highlight.id == highlight_id,
            models.Highlight.user_id == user_id,
            models.Highlight.deleted_at.is_(None),
        )
        highlight = self.db.execute(stmt).scalar_one_or_none()

        if highlight is None:
            return None

        # Update the note
        highlight.note = note
        self.db.flush()
        self.db.refresh(highlight)

        logger.info(f"Updated note for highlight_id={highlight_id}")
        return highlight
