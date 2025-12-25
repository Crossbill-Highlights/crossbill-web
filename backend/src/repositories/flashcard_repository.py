"""Flashcard repository for database operations."""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from src import models

logger = logging.getLogger(__name__)


class FlashcardRepository:
    """Repository for Flashcard database operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def get_by_id(self, flashcard_id: int, user_id: int) -> models.Flashcard | None:
        """Get a flashcard by its ID, verifying user ownership."""
        stmt = select(models.Flashcard).where(
            models.Flashcard.id == flashcard_id,
            models.Flashcard.user_id == user_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_book_id(self, book_id: int, user_id: int) -> list[models.Flashcard]:
        """Get all flashcards for a specific book, verifying user ownership."""
        stmt = (
            select(models.Flashcard)
            .options(
                joinedload(models.Flashcard.highlight).selectinload(models.Highlight.highlight_tags)
            )
            .where(
                models.Flashcard.book_id == book_id,
                models.Flashcard.user_id == user_id,
            )
            .order_by(models.Flashcard.created_at.desc())
        )
        return list(self.db.execute(stmt).unique().scalars().all())

    def get_by_highlight_id(self, highlight_id: int, user_id: int) -> list[models.Flashcard]:
        """Get all flashcards for a specific highlight, verifying user ownership."""
        stmt = (
            select(models.Flashcard)
            .where(
                models.Flashcard.highlight_id == highlight_id,
                models.Flashcard.user_id == user_id,
            )
            .order_by(models.Flashcard.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def create(
        self,
        user_id: int,
        book_id: int,
        question: str,
        answer: str,
        highlight_id: int | None = None,
    ) -> models.Flashcard:
        """Create a new flashcard."""
        flashcard = models.Flashcard(
            user_id=user_id,
            book_id=book_id,
            highlight_id=highlight_id,
            question=question,
            answer=answer,
        )
        self.db.add(flashcard)
        self.db.flush()
        self.db.refresh(flashcard)
        logger.info(
            f"Created flashcard: book_id={flashcard.book_id}, "
            f"highlight_id={flashcard.highlight_id} (id={flashcard.id}, user_id={user_id})"
        )
        return flashcard

    def update(
        self,
        flashcard_id: int,
        user_id: int,
        question: str | None = None,
        answer: str | None = None,
    ) -> models.Flashcard | None:
        """Update a flashcard's question and/or answer.

        Returns the updated flashcard if found, None otherwise.
        """
        flashcard = self.get_by_id(flashcard_id, user_id)
        if not flashcard:
            return None

        if question is not None:
            flashcard.question = question
        if answer is not None:
            flashcard.answer = answer

        self.db.flush()
        self.db.refresh(flashcard)
        logger.info(f"Updated flashcard: id={flashcard_id}")
        return flashcard

    def delete(self, flashcard_id: int, user_id: int) -> bool:
        """Delete a flashcard by its ID, verifying user ownership.

        Returns True if deleted, False if not found or not owned by user.
        """
        flashcard = self.get_by_id(flashcard_id, user_id)
        if not flashcard:
            return False
        self.db.delete(flashcard)
        self.db.flush()
        logger.info(f"Deleted flashcard: id={flashcard_id}")
        return True
