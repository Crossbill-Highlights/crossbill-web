"""Use case for creating highlight tags."""

import structlog

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.reading.protocols.highlight_tag_repository import (
    HighlightTagRepositoryProtocol,
)
from src.domain.common.value_objects.ids import BookId, UserId
from src.domain.reading.entities.highlight_tag import HighlightTag
from src.exceptions import CrossbillError, NotFoundError

logger = structlog.get_logger(__name__)


class CreateHighlightTagUseCase:
    """Use case for creating highlight tags."""

    def __init__(
        self,
        tag_repository: HighlightTagRepositoryProtocol,
        book_repository: BookRepositoryProtocol,
    ) -> None:
        self.tag_repository = tag_repository
        self.book_repository = book_repository

    def create_tag(self, book_id: int, name: str, user_id: int) -> HighlightTag:
        """
        Create a new tag for a book.

        Args:
            book_id: ID of the book
            name: Name of the tag
            user_id: ID of the user creating the tag

        Returns:
            Created tag entity

        Raises:
            NotFoundError: If book not found
            CrossbillError: If tag with same name already exists
        """
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise NotFoundError(f"Book with id {book_id} not found")

        existing_tag = self.tag_repository.find_by_book_and_name(
            book_id_vo, name.strip(), user_id_vo
        )
        if existing_tag:
            raise CrossbillError(f"Tag '{name}' already exists for this book", status_code=409)

        tag = HighlightTag.create(
            user_id=user_id_vo,
            book_id=book_id_vo,
            name=name,
        )

        tag = self.tag_repository.save(tag)

        logger.info("created_highlight_tag", tag_id=tag.id.value, book_id=book_id)
        return tag
