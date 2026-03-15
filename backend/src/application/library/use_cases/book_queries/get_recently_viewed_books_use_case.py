"""
Get recently viewed books use case.

Retrieves books ordered by last viewed timestamp with highlight and flashcard counts.
"""

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.library.protocols.file_repository import FileRepositoryProtocol
from src.domain.common.value_objects import UserId
from src.domain.library.entities.book import Book
from src.domain.library.entities.tag import Tag


class GetRecentlyViewedBooksUseCase:
    """Use case for retrieving recently viewed books."""

    def __init__(
        self,
        book_repository: BookRepositoryProtocol,
        file_repository: FileRepositoryProtocol,
    ) -> None:
        """
        Initialize use case with dependencies.

        Args:
            book_repository: Book repository protocol implementation
            file_repository: File repository protocol implementation
        """
        self.book_repository = book_repository
        self.file_repository = file_repository

    async def get_recently_viewed(
        self, user_id: int, limit: int = 10
    ) -> list[tuple[Book, int, int, list[Tag], bool]]:
        """
        Get recently viewed books with their counts and tags.

        Args:
            user_id: ID of the user whose books to retrieve
            limit: Maximum number of books to return (default: 10)

        Returns:
            List of tuples containing (Book entity, highlight_count, flashcard_count, list[Tag], has_cover)
            ordered by last_viewed DESC. Only includes books that have been viewed
            (last_viewed is not NULL).
        """
        user_id_vo = UserId(user_id)

        results = await self.book_repository.get_recently_viewed_books(
            user_id=user_id_vo,
            limit=limit,
        )

        return [
            (
                book,
                h_count,
                f_count,
                tags,
                await self.file_repository.find_cover(book.id) is not None,
            )
            for book, h_count, f_count, tags in results
        ]
