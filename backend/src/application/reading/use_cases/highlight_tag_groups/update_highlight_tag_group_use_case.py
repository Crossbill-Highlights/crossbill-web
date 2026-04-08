"""
Use case for updating a highlight tag group's name.
"""

import structlog

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.reading.protocols.highlight_tag_repository import (
    HighlightTagRepositoryProtocol,
)
from uuid import UUID

from src.domain.common.value_objects.ids import BookId, HighlightTagGroupId, UserId
from src.domain.reading.entities.highlight_tag_group import HighlightTagGroup
from src.domain.reading.exceptions import (
    BookNotFoundError,
    DuplicateTagGroupNameError,
    HighlightTagGroupNotFoundError,
)

logger = structlog.get_logger(__name__)


class UpdateHighlightTagGroupUseCase:
    """Use case for updating a highlight tag group's name."""

    def __init__(
        self,
        tag_repository: HighlightTagRepositoryProtocol,
        book_repository: BookRepositoryProtocol,
    ) -> None:
        self.tag_repository = tag_repository
        self.book_repository = book_repository

    async def update_group(
        self, group_id: int, book_id: UUID, new_name: str, user_id: int
    ) -> HighlightTagGroup:
        """
        Update a tag group's name.

        Args:
            group_id: ID of the group
            book_id: ID of the book
            new_name: New name for the group
            user_id: ID of the user

        Returns:
            Updated group entity

        Raises:
            BookNotFoundError: If book not found
            HighlightTagGroupNotFoundError: If group not found
            DuplicateTagGroupNameError: If new name already exists
        """
        group_id_vo = HighlightTagGroupId(group_id)
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        book = await self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        # Load group and verify it belongs to the correct book
        group = await self.tag_repository.find_group_by_id(group_id_vo, book_id_vo)
        if not group:
            raise HighlightTagGroupNotFoundError(group_id)

        # Check for duplicate (if name changed)
        if new_name.strip() != group.name:
            existing = await self.tag_repository.find_group_by_name(book_id_vo, new_name.strip())
            if existing:
                raise DuplicateTagGroupNameError(new_name)

        group.rename(new_name)
        group = await self.tag_repository.save_group(group)

        logger.info("updated_tag_group", group_id=group_id, new_name=new_name)
        return group
