"""Use case for updating highlight tag names."""

import structlog

from src.application.reading.protocols.highlight_tag_repository import (
    HighlightTagRepositoryProtocol,
)
from src.domain.common import ValidationError
from src.domain.common.value_objects.ids import BookId, HighlightTagId, UserId
from src.domain.reading.entities.highlight_tag import HighlightTag
from src.exceptions import CrossbillError, NotFoundError

logger = structlog.get_logger(__name__)


class UpdateHighlightTagNameUseCase:
    """Use case for updating highlight tag names."""

    def __init__(
        self,
        tag_repository: HighlightTagRepositoryProtocol,
    ) -> None:
        self.tag_repository = tag_repository

    def update_tag_name(
        self, book_id: int, tag_id: int, new_name: str, user_id: int
    ) -> HighlightTag:
        """
        Update a tag's name.

        Args:
            book_id: ID of the book
            tag_id: ID of the tag to update
            new_name: New name for the tag
            user_id: ID of the user

        Returns:
            Updated tag entity

        Raises:
            NotFoundError: If tag not found
            ValidationError: If tag doesn't belong to book
            CrossbillError: If new name already exists
        """
        tag_id_vo = HighlightTagId(tag_id)
        user_id_vo = UserId(user_id)
        book_id_vo = BookId(book_id)

        tag = self.tag_repository.find_by_id(tag_id_vo, user_id_vo)
        if not tag:
            raise NotFoundError(f"Tag with id {tag_id} not found")

        if tag.book_id != book_id_vo:
            raise ValidationError(f"Tag {tag_id} does not belong to book {book_id}")

        if new_name.strip() != tag.name:
            existing = self.tag_repository.find_by_book_and_name(
                book_id_vo, new_name.strip(), user_id_vo
            )
            if existing:
                raise CrossbillError(
                    f"Tag '{new_name}' already exists for this book", status_code=409
                )

        tag.rename(new_name)
        tag = self.tag_repository.save(tag)

        logger.info("updated_highlight_tag_name", tag_id=tag_id, new_name=new_name)
        return tag
