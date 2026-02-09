"""Use case for deleting flashcards."""

import structlog

from src.application.learning.protocols.flashcard_repository import FlashcardRepositoryProtocol
from src.domain.common.value_objects.ids import FlashcardId, UserId
from src.exceptions import NotFoundError

logger = structlog.get_logger(__name__)


class DeleteFlashcardUseCase:
    """Use case for deleting flashcards."""

    def __init__(
        self,
        flashcard_repository: FlashcardRepositoryProtocol,
    ) -> None:
        """Initialize use case with repository protocols."""
        self.flashcard_repository = flashcard_repository

    def delete_flashcard(self, flashcard_id: int, user_id: int) -> None:
        """
        Delete a flashcard.

        Args:
            flashcard_id: ID of the flashcard to delete
            user_id: ID of the user

        Raises:
            NotFoundError: If flashcard is not found
        """
        flashcard_id_vo = FlashcardId(flashcard_id)
        user_id_vo = UserId(user_id)

        deleted = self.flashcard_repository.delete(flashcard_id_vo, user_id_vo)
        if not deleted:
            raise NotFoundError(f"Flashcard with id {flashcard_id} not found")

        logger.info("deleted_flashcard", flashcard_id=flashcard_id)
