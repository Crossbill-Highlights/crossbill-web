"""Use case for deleting tags."""

import structlog

from src.application.reading.protocols.tag_repository import (
    TagRepositoryProtocol,
)
from src.domain.common.value_objects.ids import TagId, UserId
from src.domain.reading.exceptions import TagNotFoundError

logger = structlog.get_logger(__name__)


class DeleteTagUseCase:
    """Use case for deleting tags."""

    def __init__(
        self,
        tag_repository: TagRepositoryProtocol,
    ) -> None:
        self.tag_repository = tag_repository

    async def delete_tag(self, book_id: int, tag_id: int, user_id: int) -> bool:
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
        tag_id_vo = TagId(tag_id)
        user_id_vo = UserId(user_id)

        tag = await self.tag_repository.find_by_id(tag_id_vo, user_id_vo)
        if not tag:
            return False

        if tag.book_id.value != book_id:
            raise TagNotFoundError(tag_id)

        success = await self.tag_repository.delete(tag_id_vo, user_id_vo)
        if success:
            logger.info("deleted_tag", tag_id=tag_id, book_id=book_id)

        return success
