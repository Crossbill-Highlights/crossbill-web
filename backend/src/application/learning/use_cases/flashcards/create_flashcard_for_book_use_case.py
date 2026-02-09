"""Use case for creating standalone flashcards for books."""

import structlog

from src.application.learning.protocols.flashcard_repository import FlashcardRepositoryProtocol
from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.domain.common.value_objects.ids import BookId, UserId
from src.domain.learning.entities.flashcard import Flashcard
from src.exceptions import BookNotFoundError

logger = structlog.get_logger(__name__)


class CreateFlashcardForBookUseCase:
    """Use case for creating standalone flashcards for books."""

    def __init__(
        self,
        flashcard_repository: FlashcardRepositoryProtocol,
        book_repository: BookRepositoryProtocol,
    ) -> None:
        """Initialize use case with repository protocols."""
        self.flashcard_repository = flashcard_repository
        self.book_repository = book_repository

    def create_flashcard(self, book_id: int, user_id: int, question: str, answer: str) -> Flashcard:
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
