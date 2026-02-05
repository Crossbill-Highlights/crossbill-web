"""Protocol for Flashcard repository in learning context."""

from typing import Protocol

from src.domain.common.value_objects.ids import BookId, UserId


class FlashcardRepositoryProtocol(Protocol):
    """Protocol for Flashcard repository operations in learning context."""

    def count_by_book(self, book_id: BookId, user_id: UserId) -> int:
        """
        Count flashcards for a book.

        Args:
            book_id: The book ID
            user_id: The user ID

        Returns:
            Count of flashcards
        """
        ...
