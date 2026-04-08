"""Use case for deleting highlight tags."""

import structlog

from src.application.reading.protocols.highlight_tag_repository import (
    HighlightTagRepositoryProtocol,
)
from uuid import UUID

from src.domain.common.value_objects.ids import HighlightTagId, UserId
from src.domain.reading.exceptions import HighlightTagNotFoundError

logger = structlog.get_logger(__name__)


class DeleteHighlightTagUseCase:
    """Use case for deleting highlight tags."""

    def __init__(
        self,
        tag_repository: HighlightTagRepositoryProtocol,
    ) -> None:
        self.tag_repository = tag_repository

    async def delete_tag(self, book_id: UUID, tag_id: int, user_id: int) -> bool:
        """
        Delete a tag.

        Args:
            book_id: ID of the book
            tag_id: ID of the tag to delete
            user_id: ID of the user

        Returns:
            True if deleted, False if not found

        Raises:
            NotFoundError: If tag doesn't belong to book
        """
        tag_id_vo = HighlightTagId(tag_id)
        user_id_vo = UserId(user_id)

        tag = await self.tag_repository.find_by_id(tag_id_vo, user_id_vo)
        if not tag:
            return False

        if tag.book_id.value != book_id:
            raise HighlightTagNotFoundError(tag_id)

        success = await self.tag_repository.delete(tag_id_vo, user_id_vo)
        if success:
            logger.info("deleted_highlight_tag", tag_id=tag_id, book_id=book_id)

        return success
