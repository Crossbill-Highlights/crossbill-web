"""
Get recently viewed books use case.

Retrieves books ordered by last viewed timestamp with highlight and flashcard counts.
"""

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.domain.common.value_objects import UserId
from src.domain.library.entities.book import Book
from src.domain.library.entities.tag import Tag


class GetRecentlyViewedBooksUseCase:
    """Use case for retrieving recently viewed books."""

    def __init__(self, book_repository: BookRepositoryProtocol) -> None:
        """
        Initialize use case with dependencies.

        Args:
            book_repository: Book repository protocol implementation
        """
        self.book_repository = book_repository

    def get_recently_viewed(
        self, user_id: int, limit: int = 10
    ) -> list[tuple[Book, int, int, list[Tag]]]:
        """
        Get recently viewed books with their counts and tags.

        Args:
            user_id: ID of the user whose books to retrieve
            limit: Maximum number of books to return (default: 10)

        Returns:
            List of tuples containing (Book entity, highlight_count, flashcard_count, list[Tag])
            ordered by last_viewed DESC. Only includes books that have been viewed
            (last_viewed is not NULL).
        """
        # Convert primitive to value object
        user_id_vo = UserId(user_id)

        # Delegate to repository
        return self.book_repository.get_recently_viewed_books(
            user_id=user_id_vo,
            limit=limit,
        )
