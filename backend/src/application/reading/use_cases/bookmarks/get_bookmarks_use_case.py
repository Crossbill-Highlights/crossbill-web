"""Use case for getting bookmarks."""

from src.application.common.ownership import require_book
from src.application.reading.protocols.book_repository import BookRepositoryProtocol
from src.application.reading.protocols.bookmark_repository import BookmarkRepositoryProtocol
from src.domain.common.value_objects.ids import BookId, UserId
from src.domain.reading.entities.bookmark import Bookmark


class GetBookmarksUseCase:
    def __init__(
        self,
        book_repository: BookRepositoryProtocol,
        bookmark_repository: BookmarkRepositoryProtocol,
    ) -> None:
        self.book_repository = book_repository
        self.bookmark_repository = bookmark_repository

    async def get_bookmarks_by_book(self, book_id: int, user_id: int) -> list[Bookmark]:
        """
        Get all bookmarks for a book.

        Args:
            book_id: ID of the book
            user_id: ID of the user

        Returns:
            List of bookmark entities

        Raises:
            BookNotFoundError: If book is not found
        """
        # Convert to value objects
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        # Validate book exists and belongs to user
        await require_book(self.book_repository, book_id_vo, user_id_vo)

        # Get bookmarks
        return await self.bookmark_repository.find_by_book(book_id_vo, user_id_vo)
