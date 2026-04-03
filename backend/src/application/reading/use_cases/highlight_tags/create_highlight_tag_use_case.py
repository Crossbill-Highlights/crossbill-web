"""Use case for creating highlight tags."""

import structlog

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.reading.protocols.highlight_tag_repository import (
    HighlightTagRepositoryProtocol,
)
from src.domain.common.value_objects.ids import BookId, UserId
from src.domain.reading.entities.highlight_tag import HighlightTag
from src.domain.reading.exceptions import BookNotFoundError, DuplicateTagNameError

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

    async def create_tag(self, book_id: int, name: str, user_id: int) -> HighlightTag:
        """
        Create a new tag for a book.

        Args:
            book_id: ID of the book
            name: Name of the tag
            user_id: ID of the user creating the tag

        Returns:
            Created tag entity

        Raises:
            BookNotFoundError: If book not found
            DuplicateTagNameError: If tag with same name already exists
        """
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        book = await self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        existing_tag = await self.tag_repository.find_by_book_and_name(
            book_id_vo, name.strip(), user_id_vo
        )
        if existing_tag:
            raise DuplicateTagNameError(name)

        tag = HighlightTag.create(
            user_id=user_id_vo,
            book_id=book_id_vo,
            name=name,
        )

        tag = await self.tag_repository.save(tag)

        logger.info("created_highlight_tag", tag_id=tag.id.value, book_id=book_id)
        return tag
