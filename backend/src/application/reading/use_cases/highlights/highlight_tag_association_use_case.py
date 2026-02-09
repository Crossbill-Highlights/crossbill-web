"""
Use case for managing highlight-tag associations.

Handles adding and removing tags from highlights.
"""

import structlog

from src.application.reading.protocols.highlight_repository import (
    HighlightRepositoryProtocol,
)
from src.application.reading.protocols.highlight_tag_repository import (
    HighlightTagRepositoryProtocol,
)
from src.domain.common.value_objects.ids import BookId, HighlightId, HighlightTagId, UserId
from src.domain.reading.entities.highlight import Highlight
from src.domain.reading.entities.highlight_tag import HighlightTag
from src.exceptions import NotFoundError

logger = structlog.get_logger(__name__)


class HighlightTagAssociationUseCase:
    """Use case for managing tag-highlight associations."""

    def __init__(
        self,
        highlight_repository: HighlightRepositoryProtocol,
        tag_repository: HighlightTagRepositoryProtocol,
    ) -> None:
        self.highlight_repository = highlight_repository
        self.tag_repository = tag_repository

    def add_tag_by_id(self, highlight_id: int, tag_id: int, user_id: int) -> Highlight:
        """
        Add an existing tag to a highlight.

        Args:
            highlight_id: ID of the highlight
            tag_id: ID of the tag to add
            user_id: ID of the user

        Returns:
            Updated highlight entity

        Raises:
            ValueError: If highlight or tag not found
        """
        highlight_id_vo = HighlightId(highlight_id)
        tag_id_vo = HighlightTagId(tag_id)
        user_id_vo = UserId(user_id)

        # Load entities
        highlight = self.highlight_repository.find_by_id(highlight_id_vo, user_id_vo)
        if not highlight:
            raise NotFoundError(f"Highlight with id {highlight_id} not found")

        tag = self.tag_repository.find_by_id(tag_id_vo, user_id_vo)
        if not tag:
            raise NotFoundError(f"Tag with id {tag_id} not found")

        # Use domain entity to validate
        highlight.add_tag(tag)

        # Persist association via repository
        added = self.tag_repository.add_tag_to_highlight(highlight_id_vo, tag_id_vo, user_id_vo)
        if added:
            logger.info("added_tag_to_highlight", highlight_id=highlight_id, tag_id=tag_id)

        return highlight

    def add_tag_by_name(
        self, book_id: int, highlight_id: int, tag_name: str, user_id: int
    ) -> Highlight:
        """
        Add tag by name, creating if it doesn't exist (get-or-create pattern).

        Args:
            book_id: ID of the book
            highlight_id: ID of the highlight
            tag_name: Name of the tag
            user_id: ID of the user

        Returns:
            Updated highlight entity

        Raises:
            ValueError: If highlight not found or doesn't belong to book, or tag name is empty
        """
        highlight_id_vo = HighlightId(highlight_id)
        user_id_vo = UserId(user_id)
        book_id_vo = BookId(book_id)

        # Load highlight
        highlight = self.highlight_repository.find_by_id(highlight_id_vo, user_id_vo)
        if not highlight:
            raise NotFoundError(f"Highlight with id {highlight_id} not found")

        # Validate tag name
        tag_name = tag_name.strip()
        if not tag_name:
            raise NotFoundError("Tag name cannot be empty")

        # Get or create tag
        tag = self.tag_repository.find_by_book_and_name(book_id_vo, tag_name, user_id_vo)
        if not tag:
            # Create new tag
            tag = HighlightTag.create(
                user_id=user_id_vo,
                book_id=book_id_vo,
                name=tag_name,
            )

        # Use domain entity to validate
        highlight.add_tag(tag)

        # Persist association via repository
        tag = self.tag_repository.save(tag)
        tag_id_vo = HighlightTagId(tag.id.value)
        added = self.tag_repository.add_tag_to_highlight(highlight_id_vo, tag_id_vo, user_id_vo)
        if added:
            logger.info(
                "added_tag_to_highlight_by_name",
                highlight_id=highlight_id,
                tag_id=tag.id.value,
                tag_name=tag_name,
            )

        return highlight

    def remove_tag(self, highlight_id: int, tag_id: int, user_id: int) -> Highlight:
        """
        Remove a tag from a highlight.

        Args:
            highlight_id: ID of the highlight
            tag_id: ID of the tag to remove
            user_id: ID of the user

        Returns:
            Updated highlight entity

        Raises:
            ValueError: If highlight not found
        """
        highlight_id_vo = HighlightId(highlight_id)
        tag_id_vo = HighlightTagId(tag_id)
        user_id_vo = UserId(user_id)

        # Load highlight
        highlight = self.highlight_repository.find_by_id(highlight_id_vo, user_id_vo)
        if not highlight:
            raise NotFoundError(f"Highlight with id {highlight_id} not found")

        # Remove association via repository
        removed = self.tag_repository.remove_tag_from_highlight(
            highlight_id_vo, tag_id_vo, user_id_vo
        )
        if removed:
            logger.info("removed_tag_from_highlight", highlight_id=highlight_id, tag_id=tag_id)

        return highlight
