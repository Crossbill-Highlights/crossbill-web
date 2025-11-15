"""Service layer for highlight tag-related business logic."""

import structlog
from sqlalchemy.orm import Session

from src import models, repositories
from src.exceptions import CrossbillError

logger = structlog.get_logger(__name__)


class HighlightTagService:
    """Service for handling highlight tag-related operations."""

    def __init__(self, db: Session) -> None:
        """Initialize service with database session."""
        self.db = db
        self.highlight_tag_repo = repositories.HighlightTagRepository(db)
        self.highlight_repo = repositories.HighlightRepository(db)
        self.book_repo = repositories.BookRepository(db)

    def get_tags_for_highlight(self, highlight_id: int) -> list[models.HighlightTag]:
        """
        Get all tags associated with a highlight.

        Args:
            highlight_id: ID of the highlight

        Returns:
            List of HighlightTag models

        Raises:
            ValueError: If highlight not found
        """
        highlight = self.highlight_repo.get_by_id(highlight_id)
        if not highlight:
            raise ValueError(f"Highlight with id {highlight_id} not found")

        return highlight.highlight_tags

    def get_tags_for_book(self, book_id: int) -> list[models.HighlightTag]:
        """
        Get all highlight tags for a book.

        Args:
            book_id: ID of the book

        Returns:
            List of HighlightTag models

        Raises:
            ValueError: If book not found
        """
        book = self.book_repo.get_by_id(book_id)
        if not book:
            raise ValueError(f"Book with id {book_id} not found")

        return self.highlight_tag_repo.get_by_book_id(book_id)

    def create_tag_for_book(self, book_id: int, name: str) -> models.HighlightTag:
        """
        Create a new highlight tag for a book.

        Args:
            book_id: ID of the book
            name: Name of the tag

        Returns:
            Created HighlightTag model

        Raises:
            ValueError: If book not found or tag name is empty
            CrossbillError: If tag already exists
        """
        # Validate book exists
        book = self.book_repo.get_by_id(book_id)
        if not book:
            raise ValueError(f"Book with id {book_id} not found")

        # Validate tag name
        name = name.strip()
        if not name:
            raise ValueError("Tag name cannot be empty")

        # Check if tag already exists
        existing_tag = self.highlight_tag_repo.get_by_book_and_name(book_id, name)
        if existing_tag:
            raise CrossbillError(f"Tag '{name}' already exists for this book", status_code=409)

        # Create the tag
        tag = self.highlight_tag_repo.create(book_id, name)
        self.db.commit()

        logger.info("created_highlight_tag", tag_id=tag.id, book_id=book_id, name=name)
        return tag

    def delete_tag(self, book_id: int, tag_id: int) -> bool:
        """
        Delete a highlight tag.

        Args:
            book_id: ID of the book (for validation)
            tag_id: ID of the tag to delete

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If tag doesn't belong to the specified book
        """
        tag = self.highlight_tag_repo.get_by_id(tag_id)
        if not tag:
            return False

        # Verify the tag belongs to the specified book
        if tag.book_id != book_id:
            raise ValueError(f"Tag {tag_id} does not belong to book {book_id}")

        # Delete the tag (cascade will remove associations)
        success = self.highlight_tag_repo.delete(tag_id)
        if success:
            self.db.commit()
            logger.info("deleted_highlight_tag", tag_id=tag_id, book_id=book_id)

        return success

    def add_tag_to_highlight(self, highlight_id: int, tag_id: int) -> models.Highlight:
        """
        Add a tag to a highlight.

        Args:
            highlight_id: ID of the highlight
            tag_id: ID of the tag

        Returns:
            Updated Highlight model

        Raises:
            ValueError: If highlight or tag not found, or if they belong to different books
        """
        highlight = self.highlight_repo.get_by_id(highlight_id)
        if not highlight:
            raise ValueError(f"Highlight with id {highlight_id} not found")

        tag = self.highlight_tag_repo.get_by_id(tag_id)
        if not tag:
            raise ValueError(f"Tag with id {tag_id} not found")

        # Verify the tag and highlight belong to the same book
        if highlight.book_id != tag.book_id:
            raise ValueError(
                f"Tag {tag_id} (book_id={tag.book_id}) does not belong to the same book as highlight {highlight_id} (book_id={highlight.book_id})"
            )

        # Add tag if not already present
        if tag not in highlight.highlight_tags:
            highlight.highlight_tags.append(tag)
            self.db.commit()
            logger.info("added_tag_to_highlight", highlight_id=highlight_id, tag_id=tag_id)

        return highlight

    def add_tag_to_highlight_by_name(
        self, book_id: int, highlight_id: int, tag_name: str
    ) -> models.Highlight:
        """
        Add a tag to a highlight by tag name, creating the tag if it doesn't exist.

        Args:
            book_id: ID of the book (for validation and tag creation)
            highlight_id: ID of the highlight
            tag_name: Name of the tag to add

        Returns:
            Updated Highlight model

        Raises:
            ValueError: If highlight not found, tag name is empty, or book/highlight mismatch
        """
        # Validate highlight exists and belongs to the book
        highlight = self.highlight_repo.get_by_id(highlight_id)
        if not highlight:
            raise ValueError(f"Highlight with id {highlight_id} not found")

        if highlight.book_id != book_id:
            raise ValueError(f"Highlight {highlight_id} does not belong to book {book_id}")

        # Validate tag name
        tag_name = tag_name.strip()
        if not tag_name:
            raise ValueError("Tag name cannot be empty")

        # Get or create the tag
        tag = self.highlight_tag_repo.get_or_create(book_id, tag_name)

        # Add tag if not already present
        if tag not in highlight.highlight_tags:
            highlight.highlight_tags.append(tag)
            self.db.commit()
            logger.info(
                "added_tag_to_highlight_by_name",
                highlight_id=highlight_id,
                tag_id=tag.id,
                tag_name=tag_name,
            )
        else:
            logger.debug(
                "tag_already_on_highlight",
                highlight_id=highlight_id,
                tag_id=tag.id,
            )

        return highlight

    def remove_tag_from_highlight(self, highlight_id: int, tag_id: int) -> models.Highlight:
        """
        Remove a tag from a highlight.

        Args:
            highlight_id: ID of the highlight
            tag_id: ID of the tag

        Returns:
            Updated Highlight model

        Raises:
            ValueError: If highlight not found
        """
        highlight = self.highlight_repo.get_by_id(highlight_id)
        if not highlight:
            raise ValueError(f"Highlight with id {highlight_id} not found")

        # Remove tag if present
        tag = self.highlight_tag_repo.get_by_id(tag_id)
        if tag and tag in highlight.highlight_tags:
            highlight.highlight_tags.remove(tag)
            self.db.commit()
            logger.info("removed_tag_from_highlight", highlight_id=highlight_id, tag_id=tag_id)

        return highlight
