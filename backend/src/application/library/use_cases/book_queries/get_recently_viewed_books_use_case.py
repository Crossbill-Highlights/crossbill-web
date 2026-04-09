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

    def __init__(
        self,
        book_repository: BookRepositoryProtocol,
    ) -> None:
        """Initialize use case with dependencies."""
        self.book_repository = book_repository

    async def get_recently_viewed(
        self, user_id: int, limit: int = 10
    ) -> list[tuple[Book, int, int, list[Tag]]]:
        """
        Get recently viewed books with their counts and tags.

        Returns:
            List of tuples containing (Book, highlight_count, flashcard_count, list[Tag])
            ordered by last_viewed DESC.
        """
        user_id_vo = UserId(user_id)
        return await self.book_repository.get_recently_viewed_books(
            user_id=user_id_vo,
            limit=limit,
        )
