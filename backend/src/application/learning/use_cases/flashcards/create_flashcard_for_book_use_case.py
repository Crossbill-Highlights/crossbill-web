"""Use case for creating standalone flashcards for books."""

import structlog

from src.application.learning.protocols.flashcard_repository import FlashcardRepositoryProtocol
from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.library.protocols.chapter_repository import ChapterRepositoryProtocol
from src.domain.common.value_objects.ids import BookId, ChapterId, UserId
from src.domain.learning.entities.flashcard import Flashcard
from src.exceptions import BookNotFoundError, NotFoundError, ValidationError

logger = structlog.get_logger(__name__)


class CreateFlashcardForBookUseCase:
    """Use case for creating standalone flashcards for books."""

    def __init__(
        self,
        flashcard_repository: FlashcardRepositoryProtocol,
        book_repository: BookRepositoryProtocol,
        chapter_repository: ChapterRepositoryProtocol,
    ) -> None:
        """Initialize use case with repository protocols."""
        self.flashcard_repository = flashcard_repository
        self.book_repository = book_repository
        self.chapter_repository = chapter_repository

    def create_flashcard(
        self,
        book_id: int,
        user_id: int,
        question: str,
        answer: str,
        chapter_id: int | None = None,
    ) -> Flashcard:
        """
        Create a new standalone flashcard for a book (without a highlight).

        Args:
            book_id: ID of the book
            user_id: ID of the user
            question: Question text for the flashcard
            answer: Answer text for the flashcard
            chapter_id: Optional ID of the chapter

        Returns:
            Created flashcard domain entity

        Raises:
            BookNotFoundError: If book is not found
            NotFoundError: If chapter is not found
            ValidationError: If chapter does not belong to the book
        """
        # Convert to value objects
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        # Validate book exists and belongs to user
        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        # Validate chapter if provided
        chapter_id_vo: ChapterId | None = None
        if chapter_id is not None:
            chapter_id_vo = ChapterId(chapter_id)
            chapter = self.chapter_repository.find_by_id(chapter_id_vo, user_id_vo)
            if not chapter:
                raise NotFoundError(f"Chapter with id {chapter_id} not found")
            if chapter.book_id != book_id_vo:
                raise ValidationError("Chapter does not belong to this book")

        # Create flashcard using domain factory (no highlight)
        flashcard = Flashcard.create(
            user_id=user_id_vo,
            book_id=book_id_vo,
            question=question,
            answer=answer,
            highlight_id=None,
            chapter_id=chapter_id_vo,
        )

        # Persist (commit handled by DI infrastructure)
        flashcard = self.flashcard_repository.save(flashcard)

        logger.info(
            "created_flashcard_for_book",
            flashcard_id=flashcard.id.value,
            book_id=book_id,
        )
        return flashcard
