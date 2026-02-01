"""Application service for flashcard operations."""

from dataclasses import dataclass

import structlog
from sqlalchemy.orm import Session

from src.domain.common.value_objects.ids import BookId, FlashcardId, HighlightId, UserId
from src.domain.learning.entities.flashcard import Flashcard
from src.domain.library.entities.chapter import Chapter
from src.domain.reading.entities.highlight import Highlight
from src.domain.reading.entities.highlight_tag import HighlightTag
from src.exceptions import BookNotFoundError, NotFoundError, ValidationError
from src.infrastructure.learning.repositories.flashcard_repository import FlashcardRepository
from src.infrastructure.library.repositories.book_repository import BookRepository
from src.infrastructure.reading.repositories.highlight_repository import HighlightRepository

logger = structlog.get_logger(__name__)


@dataclass
class FlashcardWithHighlight:
    """DTO for flashcard with its associated highlight and tags."""

    flashcard: Flashcard
    highlight: Highlight | None
    chapter: Chapter | None
    highlight_tags: list[HighlightTag]


class FlashcardNotFoundError(NotFoundError):
    """Flashcard not found error."""

    def __init__(self, flashcard_id: int) -> None:
        """Initialize with flashcard ID."""
        self.flashcard_id = flashcard_id
        super().__init__(f"Flashcard with id {flashcard_id} not found")


class FlashcardService:
    """Application service for flashcard CRUD operations."""

    def __init__(self, db: Session) -> None:
        """Initialize service with database session."""
        self.db = db
        self.flashcard_repository = FlashcardRepository(db)
        self.book_repository = BookRepository(db)
        self.highlight_repository = HighlightRepository(db)

    def create_flashcard_for_highlight(
        self, highlight_id: int, user_id: int, question: str, answer: str
    ) -> Flashcard:
        """
        Create a new flashcard for a highlight.

        Args:
            highlight_id: ID of the highlight
            user_id: ID of the user
            question: Question text for the flashcard
            answer: Answer text for the flashcard

        Returns:
            Created flashcard domain entity

        Raises:
            ValidationError: If highlight is not found
        """
        # Convert to value objects
        highlight_id_vo = HighlightId(highlight_id)
        user_id_vo = UserId(user_id)

        # Validate highlight exists and belongs to user
        highlight = self.highlight_repository.find_by_id(highlight_id_vo, user_id_vo)
        if not highlight:
            raise ValidationError(f"Highlight with id {highlight_id} not found", status_code=404)

        # Create flashcard using domain factory
        flashcard = Flashcard.create(
            user_id=user_id_vo,
            book_id=highlight.book_id,
            question=question,
            answer=answer,
            highlight_id=highlight_id_vo,
        )

        # Persist and commit
        flashcard = self.flashcard_repository.save(flashcard)
        self.db.commit()

        logger.info(
            "created_flashcard_for_highlight",
            flashcard_id=flashcard.id.value,
            highlight_id=highlight_id,
        )
        return flashcard

    def create_flashcard_for_book(
        self, book_id: int, user_id: int, question: str, answer: str
    ) -> Flashcard:
        """
        Create a new standalone flashcard for a book (without a highlight).

        Args:
            book_id: ID of the book
            user_id: ID of the user
            question: Question text for the flashcard
            answer: Answer text for the flashcard

        Returns:
            Created flashcard domain entity

        Raises:
            BookNotFoundError: If book is not found
        """
        # Convert to value objects
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        # Validate book exists and belongs to user
        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        # Create flashcard using domain factory (no highlight)
        flashcard = Flashcard.create(
            user_id=user_id_vo,
            book_id=book_id_vo,
            question=question,
            answer=answer,
            highlight_id=None,
        )

        # Persist and commit
        flashcard = self.flashcard_repository.save(flashcard)
        self.db.commit()

        logger.info(
            "created_flashcard_for_book",
            flashcard_id=flashcard.id.value,
            book_id=book_id,
        )
        return flashcard

    def get_flashcards_by_book(self, book_id: int, user_id: int) -> list[FlashcardWithHighlight]:
        """
        Get all flashcards for a book with their associated highlights.

        Args:
            book_id: ID of the book
            user_id: ID of the user

        Returns:
            List of FlashcardWithHighlight DTOs

        Raises:
            BookNotFoundError: If book is not found
        """
        # Convert to value objects
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        # Validate book exists and belongs to user
        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        # Get flashcards
        flashcards = self.flashcard_repository.find_by_book(book_id_vo, user_id_vo)

        # Collect unique highlight IDs from flashcards
        highlight_ids = [fc.highlight_id for fc in flashcards if fc.highlight_id is not None]

        # Fetch highlights with chapters and tags if there are any
        highlight_map: dict[int, tuple[Highlight, Chapter | None, list[HighlightTag]]] = {}
        if highlight_ids:
            highlights_data = self.highlight_repository.find_by_ids_with_tags(
                highlight_ids, user_id_vo
            )
            highlight_map = {h.id.value: (h, chapter, tags) for h, chapter, tags in highlights_data}

        # Combine flashcards with their highlights
        result = []
        for fc in flashcards:
            highlight = None
            chapter = None
            tags = []
            if fc.highlight_id:
                highlight_data = highlight_map.get(fc.highlight_id.value)
                if highlight_data:
                    highlight, chapter, tags = highlight_data

            result.append(
                FlashcardWithHighlight(
                    flashcard=fc, highlight=highlight, chapter=chapter, highlight_tags=tags
                )
            )

        return result

    def update_flashcard(
        self,
        flashcard_id: int,
        user_id: int,
        question: str | None = None,
        answer: str | None = None,
    ) -> Flashcard:
        """
        Update a flashcard's question and/or answer.

        Args:
            flashcard_id: ID of the flashcard to update
            user_id: ID of the user
            question: New question text (optional)
            answer: New answer text (optional)

        Returns:
            Updated flashcard domain entity

        Raises:
            FlashcardNotFoundError: If flashcard is not found
            ValidationError: If neither question nor answer is provided
        """
        if question is None and answer is None:
            raise ValidationError("At least one of question or answer must be provided")

        # Convert to value objects
        flashcard_id_vo = FlashcardId(flashcard_id)
        user_id_vo = UserId(user_id)

        # Load flashcard domain entity
        flashcard = self.flashcard_repository.find_by_id(flashcard_id_vo, user_id_vo)
        if not flashcard:
            raise FlashcardNotFoundError(flashcard_id)

        # Use domain methods to update
        if question is not None:
            flashcard.update_question(question)
        if answer is not None:
            flashcard.update_answer(answer)

        # Persist and commit
        flashcard = self.flashcard_repository.save(flashcard)
        self.db.commit()

        logger.info("updated_flashcard", flashcard_id=flashcard_id)
        return flashcard

    def delete_flashcard(self, flashcard_id: int, user_id: int) -> None:
        """
        Delete a flashcard.

        Args:
            flashcard_id: ID of the flashcard to delete
            user_id: ID of the user

        Raises:
            ValidationError: If flashcard is not found
        """
        # Convert to value objects
        flashcard_id_vo = FlashcardId(flashcard_id)
        user_id_vo = UserId(user_id)

        # Delete via repository
        deleted = self.flashcard_repository.delete(flashcard_id_vo, user_id_vo)
        if not deleted:
            raise ValidationError(f"Flashcard with id {flashcard_id} not found", status_code=404)

        self.db.commit()
        logger.info("deleted_flashcard", flashcard_id=flashcard_id)
