"""
Use case for creating a new highlight tag group.
"""

import structlog

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.reading.protocols.highlight_tag_repository import (
    HighlightTagRepositoryProtocol,
)
from src.domain.common.value_objects.ids import BookId, UserId
from src.domain.reading.entities.highlight_tag_group import HighlightTagGroup
from src.exceptions import CrossbillError, NotFoundError

logger = structlog.get_logger(__name__)


class CreateHighlightTagGroupUseCase:
    """Use case for creating a new highlight tag group."""

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
