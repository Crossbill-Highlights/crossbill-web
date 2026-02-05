"""Use case for flashcard operations."""

from dataclasses import dataclass

import structlog

from src.application.learning.protocols.flashcard_repository import FlashcardRepositoryProtocol
from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.reading.protocols.highlight_repository import HighlightRepositoryProtocol
from src.domain.common.value_objects.ids import BookId, FlashcardId, HighlightId, UserId
from src.domain.learning.entities.flashcard import Flashcard
from src.domain.library.entities.chapter import Chapter
from src.domain.reading.entities.highlight import Highlight
from src.domain.reading.entities.highlight_tag import HighlightTag
from src.exceptions import BookNotFoundError, NotFoundError, ValidationError

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
        self.flashcard_id = flashcard_id
        super().__init__(f"Flashcard with id {flashcard_id} not found")


class FlashcardUseCase:
    """Use case for flashcard CRUD operations."""

    def __init__(
        self,
        flashcard_repository: FlashcardRepositoryProtocol,
        book_repository: BookRepositoryProtocol,
        highlight_repository: HighlightRepositoryProtocol,
    ) -> None:
        """Initialize use case with repository protocols."""
        self.flashcard_repository = flashcard_repository
        self.book_repository = book_repository
        self.highlight_repository = highlight_repository

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
        highlight_id_vo = HighlightId(highlight_id)
        user_id_vo = UserId(user_id)

        highlight = self.highlight_repository.find_by_id(highlight_id_vo, user_id_vo)
        if not highlight:
            raise NotFoundError(f"Highlight with id {highlight_id} not found")

        flashcard = Flashcard.create(
            user_id=user_id_vo,
            book_id=highlight.book_id,
            question=question,
            answer=answer,
            highlight_id=highlight_id_vo,
        )
        flashcard = self.flashcard_repository.save(flashcard)

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

        # Persist (commit handled by DI infrastructure)
        flashcard = self.flashcard_repository.save(flashcard)

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
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        flashcards = self.flashcard_repository.find_by_book(book_id_vo, user_id_vo)

        highlight_ids = [fc.highlight_id for fc in flashcards if fc.highlight_id is not None]

        highlight_map: dict[int, tuple[Highlight, Chapter | None, list[HighlightTag]]] = {}
        if highlight_ids:
            highlights_data = self.highlight_repository.find_by_ids_with_tags(
                highlight_ids, user_id_vo
            )
            highlight_map = {h.id.value: (h, chapter, tags) for h, chapter, tags in highlights_data}

        # TODO: should we just return tuple of domain objects and then join them to Pydantic schema in router?
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

        flashcard_id_vo = FlashcardId(flashcard_id)
        user_id_vo = UserId(user_id)

        flashcard = self.flashcard_repository.find_by_id(flashcard_id_vo, user_id_vo)
        if not flashcard:
            raise FlashcardNotFoundError(flashcard_id)

        if question is not None:
            flashcard.update_question(question)
        if answer is not None:
            flashcard.update_answer(answer)

        flashcard = self.flashcard_repository.save(flashcard)

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
        flashcard_id_vo = FlashcardId(flashcard_id)
        user_id_vo = UserId(user_id)

        deleted = self.flashcard_repository.delete(flashcard_id_vo, user_id_vo)
        if not deleted:
            raise NotFoundError(f"Flashcard with id {flashcard_id} not found")

        logger.info("deleted_flashcard", flashcard_id=flashcard_id)
