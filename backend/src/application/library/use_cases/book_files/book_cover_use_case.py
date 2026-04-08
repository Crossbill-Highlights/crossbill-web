"""Book cover management use case."""

import logging
from uuid import UUID

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.library.protocols.file_repository import FileRepositoryProtocol
from src.domain.common.value_objects import BookId, UserId
from src.domain.reading.exceptions import BookNotFoundError

logger = logging.getLogger(__name__)


class BookCoverUseCase:
    """Use case for book cover management operations."""

    def __init__(
        self,
        book_repository: BookRepositoryProtocol,
        file_repository: FileRepositoryProtocol,
    ) -> None:
        self.book_repository = book_repository
        self.file_repository = file_repository

    async def get_cover(self, book_id: UUID, user_id: int) -> bytes | None:
        """
        Get the cover image bytes with ownership verification.

        Args:
            book_id: ID of the book
            user_id: ID of the user requesting the cover

        Returns:
            Cover image bytes, or None if no cover exists

        Raises:
            BookNotFoundError: If book is not found or user doesn't own it
        """
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        book = await self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        return await self.file_repository.get_cover(book_id_vo)
