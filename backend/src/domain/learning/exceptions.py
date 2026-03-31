"""Learning domain exceptions."""

from src.domain.common.exceptions import EntityNotFoundError


class FlashcardNotFoundError(EntityNotFoundError):
    """Raised when a flashcard cannot be found."""

    def __init__(self, flashcard_id: int) -> None:
        super().__init__("Flashcard", flashcard_id)
        self.flashcard_id = flashcard_id
