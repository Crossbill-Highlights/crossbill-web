"""Service layer for flashcard-related business logic."""

import logging

import structlog
from sqlalchemy.orm import Session

from src import repositories, schemas
from src.exceptions import BookNotFoundError, NotFoundError, ValidationError
from src.services.ai.ai_service import get_ai_flashcard_suggestions_from_text

logger = logging.getLogger(__name__)
structlog_logger = structlog.get_logger(__name__)


class HighlightNotFoundError(NotFoundError):
    """Highlight not found error."""

    def __init__(self, highlight_id: int) -> None:
        """Initialize with highlight ID."""
        self.highlight_id = highlight_id
        super().__init__(f"Highlight with id {highlight_id} not found")


class FlashcardNotFoundError(NotFoundError):
    """Flashcard not found error."""

    def __init__(self, flashcard_id: int) -> None:
        """Initialize with flashcard ID."""
        self.flashcard_id = flashcard_id
        super().__init__(f"Flashcard with id {flashcard_id} not found")


class FlashcardService:
    """Service for handling flashcard-related operations."""

    def __init__(self, db: Session) -> None:
        """Initialize service with database session."""
        self.db = db
        self.flashcard_repo = repositories.FlashcardRepository(db)
        self.book_repo = repositories.BookRepository(db)
        self.highlight_repo = repositories.HighlightRepository(db)

    def create_flashcard_for_highlight(
        self,
        highlight_id: int,
        user_id: int,
        question: str,
        answer: str,
    ) -> schemas.Flashcard:
        """
        Create a new flashcard for a highlight.

        Args:
            highlight_id: ID of the highlight
            user_id: ID of the user
            question: Question text for the flashcard
            answer: Answer text for the flashcard

        Returns:
            Created flashcard

        Raises:
            HighlightNotFoundError: If highlight is not found
        """
        # Validate highlight exists and belongs to user
        highlight = self.highlight_repo.get_by_id(highlight_id, user_id)
        if not highlight:
            raise HighlightNotFoundError(highlight_id)

        # Create flashcard with book_id from highlight
        flashcard = self.flashcard_repo.create(
            user_id=user_id,
            book_id=highlight.book_id,
            question=question,
            answer=answer,
            highlight_id=highlight_id,
        )
        self.db.commit()

        logger.info(f"Created flashcard {flashcard.id} for highlight {highlight_id}")
        return schemas.Flashcard.model_validate(flashcard)

    def create_flashcard_for_book(
        self,
        book_id: int,
        user_id: int,
        question: str,
        answer: str,
    ) -> schemas.Flashcard:
        """
        Create a new standalone flashcard for a book (without a highlight).

        Args:
            book_id: ID of the book
            user_id: ID of the user
            question: Question text for the flashcard
            answer: Answer text for the flashcard

        Returns:
            Created flashcard

        Raises:
            BookNotFoundError: If book is not found
        """
        # Validate book exists and belongs to user
        book = self.book_repo.get_by_id(book_id, user_id)
        if not book:
            raise BookNotFoundError(book_id)

        # Create flashcard without highlight
        flashcard = self.flashcard_repo.create(
            user_id=user_id,
            book_id=book_id,
            question=question,
            answer=answer,
            highlight_id=None,
        )
        self.db.commit()

        logger.info(f"Created flashcard {flashcard.id} for book {book_id}")
        return schemas.Flashcard.model_validate(flashcard)

    def get_flashcards_by_book(
        self, book_id: int, user_id: int
    ) -> schemas.FlashcardsWithHighlightsResponse:
        """
        Get all flashcards for a specific book with embedded highlight data.

        Args:
            book_id: ID of the book
            user_id: ID of the user

        Returns:
            List of flashcards with highlight data

        Raises:
            BookNotFoundError: If book is not found
        """
        # Validate book exists
        book = self.book_repo.get_by_id(book_id, user_id)
        if not book:
            raise BookNotFoundError(book_id)

        flashcards = self.flashcard_repo.get_by_book_id(book_id, user_id)
        return schemas.FlashcardsWithHighlightsResponse(
            flashcards=[schemas.FlashcardWithHighlight.model_validate(f) for f in flashcards]
        )

    def update_flashcard(
        self,
        flashcard_id: int,
        user_id: int,
        question: str | None = None,
        answer: str | None = None,
    ) -> schemas.Flashcard:
        """
        Update a flashcard's question and/or answer.

        Args:
            flashcard_id: ID of the flashcard to update
            user_id: ID of the user
            question: New question text (optional)
            answer: New answer text (optional)

        Returns:
            Updated flashcard

        Raises:
            FlashcardNotFoundError: If flashcard is not found
            ValidationError: If neither question nor answer is provided
        """
        if question is None and answer is None:
            raise ValidationError("At least one of question or answer must be provided")

        flashcard = self.flashcard_repo.update(flashcard_id, user_id, question, answer)
        if not flashcard:
            raise FlashcardNotFoundError(flashcard_id)

        self.db.commit()
        logger.info(f"Updated flashcard {flashcard_id}")
        return schemas.Flashcard.model_validate(flashcard)

    def delete_flashcard(self, flashcard_id: int, user_id: int) -> None:
        """
        Delete a flashcard.

        Args:
            flashcard_id: ID of the flashcard to delete
            user_id: ID of the user

        Raises:
            FlashcardNotFoundError: If flashcard is not found
        """
        deleted = self.flashcard_repo.delete(flashcard_id, user_id)
        if not deleted:
            raise FlashcardNotFoundError(flashcard_id)

        self.db.commit()
        logger.info(f"Deleted flashcard {flashcard_id}")

    async def get_flashcard_suggestions(
        self,
        highlight_id: int,
        user_id: int,
    ) -> list[schemas.FlashcardSuggestionItem]:
        """
        Get AI-generated flashcard suggestions for a highlight.

        Args:
            highlight_id: ID of the highlight
            user_id: ID of the user (for ownership verification)

        Returns:
            List of flashcard suggestions

        Raises:
            HighlightNotFoundError: If highlight not found or user doesn't own it
        """
        # Retrieve highlight using repository
        highlight = self.highlight_repo.get_by_id(highlight_id, user_id)

        # Validate highlight exists
        if highlight is None:
            raise HighlightNotFoundError(highlight_id)

        # Get AI suggestions from highlight text
        ai_suggestions = await get_ai_flashcard_suggestions_from_text(highlight.text)

        # Convert FlashcardSuggestion objects to FlashcardSuggestionItem schemas
        suggestions = [
            schemas.FlashcardSuggestionItem(question=suggestion.question, answer=suggestion.answer)
            for suggestion in ai_suggestions
        ]

        structlog_logger.info(
            "flashcard_suggestions_generated",
            highlight_id=highlight_id,
            suggestion_count=len(suggestions),
        )

        return suggestions
