"""Use case for getting highlight tags for a book."""

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.reading.protocols.highlight_tag_repository import (
    HighlightTagRepositoryProtocol,
)
from src.domain.common.value_objects.ids import BookId, UserId
from src.domain.reading.entities.highlight_tag import HighlightTag
from src.exceptions import NotFoundError


class GetHighlightTagsForBookUseCase:
    """Use case for getting highlight tags for a book."""

    def __init__(
        self,
        tag_repository: HighlightTagRepositoryProtocol,
        book_repository: BookRepositoryProtocol,
    ) -> None:
        self.tag_repository = tag_repository
        self.book_repository = book_repository

    def get_tags(self, book_id: int, user_id: int) -> list[HighlightTag]:
        """
        Get all tags for a book.

        Args:
            book_id: ID of the book
            user_id: ID of the user

        Returns:
            List of tag entities

        Raises:
            NotFoundError: If book not found
        """
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise NotFoundError(f"Book with id {book_id} not found")

        return self.tag_repository.find_by_book(book_id_vo, user_id_vo)
