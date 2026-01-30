"""
Application service for managing highlight-tag associations.

Handles adding and removing tags from highlights.
"""

import structlog
from sqlalchemy.orm import Session

from src.domain.common.value_objects.ids import BookId, HighlightId, HighlightTagId, UserId
from src.domain.reading.entities.highlight import Highlight
from src.domain.reading.entities.highlight_tag import HighlightTag
from src.infrastructure.reading.repositories.highlight_repository import (
    HighlightRepository,
)
from src.infrastructure.reading.repositories.highlight_tag_repository import (
    HighlightTagRepository,
)

logger = structlog.get_logger(__name__)


class HighlightTagAssociationService:
    """Application service for managing tag-highlight associations."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.highlight_repository = HighlightRepository(db)
        self.tag_repository = HighlightTagRepository(db)

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
            raise ValueError(f"Highlight with id {highlight_id} not found")

        tag = self.tag_repository.find_by_id(tag_id_vo, user_id_vo)
        if not tag:
            raise ValueError(f"Tag with id {tag_id} not found")

        # Use domain entity to validate
        highlight.add_tag(tag)

        # Persist association via repository
        added = self.tag_repository.add_tag_to_highlight(highlight_id_vo, tag_id_vo, user_id_vo)
        if added:
            self.db.commit()
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
            raise ValueError(f"Highlight with id {highlight_id} not found")

        # Verify highlight belongs to book
        if highlight.book_id != book_id_vo:
            raise ValueError(f"Highlight {highlight_id} does not belong to book {book_id}")

        # Validate tag name
        tag_name = tag_name.strip()
        if not tag_name:
            raise ValueError("Tag name cannot be empty")

        # Get or create tag
        tag = self.tag_repository.find_by_book_and_name(book_id_vo, tag_name, user_id_vo)
        if not tag:
            # Create new tag
            tag = HighlightTag.create(
                user_id=user_id_vo,
                book_id=book_id_vo,
                name=tag_name,
            )
            tag = self.tag_repository.save(tag)
            self.db.flush()

        # Use domain entity to validate
        highlight.add_tag(tag)

        # Persist association via repository
        tag_id_vo = HighlightTagId(tag.id.value)
        added = self.tag_repository.add_tag_to_highlight(highlight_id_vo, tag_id_vo, user_id_vo)
        if added:
            self.db.commit()
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
            raise ValueError(f"Highlight with id {highlight_id} not found")

        # Remove association via repository
        removed = self.tag_repository.remove_tag_from_highlight(
            highlight_id_vo, tag_id_vo, user_id_vo
        )
        if removed:
            self.db.commit()
            logger.info("removed_tag_from_highlight", highlight_id=highlight_id, tag_id=tag_id)

        return highlight
