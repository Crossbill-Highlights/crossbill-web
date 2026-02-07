"""
Use case for tag group management.

Handles creating, updating, deleting tag groups and managing tag-group associations.
"""

import structlog
from mcp.server.fastmcp.exceptions import ValidationError

from src.application.library.protocols.book_repository import BookRepositoryProtocol
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
from src.domain.reading.entities.highlight_tag_group import HighlightTagGroup
from src.exceptions import CrossbillError, NotFoundError

logger = structlog.get_logger(__name__)


class HighlightTagGroupUseCase:
    """Use case for tag group management."""

    def __init__(
        self,
        tag_repository: HighlightTagRepositoryProtocol,
        book_repository: BookRepositoryProtocol,
    ) -> None:
        self.tag_repository = tag_repository
        self.book_repository = book_repository

    def create_group(self, book_id: int, name: str, user_id: int) -> HighlightTagGroup:
        """
        Create a new tag group.

        Args:
            book_id: ID of the book
            name: Name of the group
            user_id: ID of the user

        Returns:
            Created group entity

        Raises:
            ValueError: If book not found
            CrossbillError: If group with same name already exists
        """
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        # Validate book exists
        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise NotFoundError(f"Book with id {book_id} not found")

        # Check for duplicate name
        existing = self.tag_repository.find_group_by_name(book_id_vo, name.strip())
        if existing:
            raise CrossbillError(
                f"Tag group '{name}' already exists for this book", status_code=409
            )

        group = HighlightTagGroup.create(book_id=book_id_vo, name=name)
        group = self.tag_repository.save_group(group)

        logger.info("created_tag_group", group_id=group.id.value, book_id=book_id)
        return group

    def update_group(
        self, group_id: int, book_id: int, new_name: str, user_id: int
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
            ValueError: If group or book not found
            CrossbillError: If new name already exists
        """
        group_id_vo = HighlightTagGroupId(group_id)
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise NotFoundError(f"Book with id {book_id} not found")

        # Load group and verify it belongs to the correct book
        group = self.tag_repository.find_group_by_id(group_id_vo, book_id_vo)
        if not group:
            raise NotFoundError(f"Tag group with id {group_id} not found")

        # Check for duplicate (if name changed)
        if new_name.strip() != group.name:
            existing = self.tag_repository.find_group_by_name(book_id_vo, new_name.strip())
            if existing:
                raise CrossbillError(
                    f"Tag group '{new_name}' already exists for this book",
                    status_code=409,
                )

        group.rename(new_name)
        group = self.tag_repository.save_group(group)

        logger.info("updated_tag_group", group_id=group_id, new_name=new_name)
        return group

    def delete_group(self, group_id: int, user_id: int) -> bool:
        """
        Delete a tag group (nullifies tag associations).

        Args:
            group_id: ID of the group to delete
            user_id: ID of the user

        Returns:
            True if deleted, False if not found
        """
        group_id_vo = HighlightTagGroupId(group_id)

        success = self.tag_repository.delete_group(group_id_vo)
        if success:
            logger.info("deleted_tag_group", group_id=group_id)

        return success

    def update_tag_group_association(
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
