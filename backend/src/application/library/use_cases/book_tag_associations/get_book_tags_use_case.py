"""
Use case for getting all tags for a book.
"""

import structlog

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.library.protocols.tag_repository import TagRepositoryProtocol
from src.domain.common.value_objects.ids import BookId, UserId
from src.domain.library.entities.tag import Tag
from src.domain.reading.exceptions import BookNotFoundError

logger = structlog.get_logger(__name__)


class GetBookTagsUseCase:
    """Use case for getting all tags for a book."""

    def __init__(
        self,
        tag_repository: TagRepositoryProtocol,
        book_repository: BookRepositoryProtocol,
    ) -> None:
        """
        Initialize use case with dependencies.

        Args:
            tag_repository: Tag repository protocol implementation
            book_repository: Book repository protocol implementation
        """
        self.tag_repository = tag_repository
        self.book_repository = book_repository

    def get_tags(self, book_id: int, user_id: int) -> list[Tag]:
        """
        Get all tags for a book.

        Args:
            book_id: ID of the book
            user_id: ID of the user

        Returns:
            List of tags for the book

        Raises:
            BookNotFoundError: If book not found
        """
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(f"Book with id {book_id} not found")

        return self.tag_repository.find_tags_for_book(book_id_vo, user_id_vo)
