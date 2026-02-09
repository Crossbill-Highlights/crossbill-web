"""Exceptions for learning use cases."""

from src.exceptions import NotFoundError


class FlashcardNotFoundError(NotFoundError):
    """Flashcard not found error."""

    def __init__(self, flashcard_id: int) -> None:
        self.flashcard_id = flashcard_id
        super().__init__(f"Flashcard with id {flashcard_id} not found")
