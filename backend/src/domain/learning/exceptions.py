"""Learning domain exceptions."""

from src.domain.common.exceptions import EntityNotFoundError


class QuizSessionNotFoundError(EntityNotFoundError):
    """Raised when a quiz session cannot be found."""

    def __init__(self, session_id: int) -> None:
        super().__init__("QuizSession", session_id)


class FlashcardNotFoundError(EntityNotFoundError):
    """Raised when a flashcard cannot be found."""

    def __init__(self, flashcard_id: int) -> None:
        super().__init__("Flashcard", flashcard_id)
        self.flashcard_id = flashcard_id
