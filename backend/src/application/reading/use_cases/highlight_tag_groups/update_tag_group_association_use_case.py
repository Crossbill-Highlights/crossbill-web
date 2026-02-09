"""
Use case for updating a tag's group association.
"""

import structlog

from src.application.reading.protocols.highlight_tag_repository import (
    HighlightTagRepositoryProtocol,
)
from src.domain.common.value_objects.ids import (
    BookId,
    HighlightTagGroupId,
    HighlightTagId,
    UserId,
)
from src.domain.reading.entities.highlight_tag import HighlightTag
from src.exceptions import NotFoundError, ValidationError

logger = structlog.get_logger(__name__)


class UpdateTagGroupAssociationUseCase:
    """Use case for updating a tag's group association."""

    def __init__(
        self,
        tag_repository: HighlightTagRepositoryProtocol,
    ) -> None:
        self.tag_repository = tag_repository

    def update_association(
        self, book_id: int, tag_id: int, group_id: int | None, user_id: int
    ) -> HighlightTag:
        """
        Update a tag's group association.

        Args:
            book_id: ID of the book
            tag_id: ID of the tag
            group_id: ID of the group (or None to clear association)
            user_id: ID of the user

        Returns:
            Updated tag entity

        Raises:
            ValueError: If tag, group, or book not found, or if they don't match
        """
        tag_id_vo = HighlightTagId(tag_id)
        user_id_vo = UserId(user_id)
        book_id_vo = BookId(book_id)
        group_id_vo = HighlightTagGroupId(group_id) if group_id else None

        tag = self.tag_repository.find_by_id(tag_id_vo, user_id_vo)
        if not tag:
            raise NotFoundError(f"Tag with id {tag_id} not found")

        # Verify belongs to book
        if tag.book_id != book_id_vo:
            raise ValidationError(f"Tag {tag_id} does not belong to book {book_id}")

        # Validate group if provided
        if group_id_vo:
            group = self.tag_repository.find_group_by_id(group_id_vo, book_id_vo)
            if not group:
                raise NotFoundError(f"Tag group with id {group_id} not found")

        tag.update_group(group_id_vo)
        tag = self.tag_repository.save(tag)

        logger.info("updated_tag_group_association", tag_id=tag_id, group_id=group_id)
        return tag
