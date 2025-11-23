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

    def get_tags_for_highlight(self, highlight_id: int, user_id: int) -> list[models.HighlightTag]:
        """
        Get all tags associated with a highlight.

        Args:
            highlight_id: ID of the highlight

        Returns:
            List of HighlightTag models

        Raises:
            ValueError: If highlight not found
        """
        highlight = self.highlight_repo.get_by_id(highlight_id, user_id)
        if not highlight:
            raise ValueError(f"Highlight with id {highlight_id} not found")

        return highlight.highlight_tags

    def get_tags_for_book(self, book_id: int, user_id: int) -> list[models.HighlightTag]:
        """
        Get all highlight tags for a book.

        Args:
            book_id: ID of the book

        Returns:
            List of HighlightTag models

        Raises:
            ValueError: If book not found
        """
        book = self.book_repo.get_by_id(book_id, user_id)
        if not book:
            raise ValueError(f"Book with id {book_id} not found")

        return self.highlight_tag_repo.get_by_book_id(book_id, user_id)

    def create_tag_for_book(self, book_id: int, name: str, user_id: int) -> models.HighlightTag:
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
        book = self.book_repo.get_by_id(book_id, user_id)
        if not book:
            raise ValueError(f"Book with id {book_id} not found")

        # Validate tag name
        name = name.strip()
        if not name:
            raise ValueError("Tag name cannot be empty")

        # Check if tag already exists
        existing_tag = self.highlight_tag_repo.get_by_book_and_name(book_id, name, user_id)
        if existing_tag:
            raise CrossbillError(f"Tag '{name}' already exists for this book", status_code=409)

        # Create the tag
        tag = self.highlight_tag_repo.create(book_id, user_id, name)
        self.db.commit()

        logger.info("created_highlight_tag", tag_id=tag.id, book_id=book_id, name=name)
        return tag

    def delete_tag(self, book_id: int, tag_id: int, user_id: int) -> bool:
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
        tag = self.highlight_tag_repo.get_by_id(tag_id, user_id)
        if not tag:
            return False

        # Verify the tag belongs to the specified book
        if tag.book_id != book_id:
            raise ValueError(f"Tag {tag_id} does not belong to book {book_id}")

        # Delete the tag (cascade will remove associations)
        success = self.highlight_tag_repo.delete(tag_id, user_id)
        if success:
            self.db.commit()
            logger.info("deleted_highlight_tag", tag_id=tag_id, book_id=book_id)

        return success

    def add_tag_to_highlight(
        self, highlight_id: int, tag_id: int, user_id: int
    ) -> models.Highlight:
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
        highlight = self.highlight_repo.get_by_id(highlight_id, user_id)
        if not highlight:
            raise ValueError(f"Highlight with id {highlight_id} not found")

        tag = self.highlight_tag_repo.get_by_id(tag_id, user_id)
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
        self, book_id: int, highlight_id: int, tag_name: str, user_id: int
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
        highlight = self.highlight_repo.get_by_id(highlight_id, user_id)
        if not highlight:
            raise ValueError(f"Highlight with id {highlight_id} not found")

        if highlight.book_id != book_id:
            raise ValueError(f"Highlight {highlight_id} does not belong to book {book_id}")

        # Validate tag name
        tag_name = tag_name.strip()
        if not tag_name:
            raise ValueError("Tag name cannot be empty")

        # Get or create the tag
        tag = self.highlight_tag_repo.get_or_create(book_id, user_id, tag_name)

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

    def remove_tag_from_highlight(
        self, highlight_id: int, tag_id: int, user_id: int
    ) -> models.Highlight:
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
        highlight = self.highlight_repo.get_by_id(highlight_id, user_id)
        if not highlight:
            raise ValueError(f"Highlight with id {highlight_id} not found")

        # Remove tag if present
        tag = self.highlight_tag_repo.get_by_id(tag_id, user_id)
        if tag and tag in highlight.highlight_tags:
            highlight.highlight_tags.remove(tag)
            self.db.commit()
            logger.info("removed_tag_from_highlight", highlight_id=highlight_id, tag_id=tag_id)

        return highlight

    def update_tag(
        self,
        book_id: int,
        tag_id: int,
        user_id: int,
        name: str | None = None,
        tag_group_id: int | None = None,
    ) -> models.HighlightTag:
        """
        Update a highlight tag's name and/or tag group association.

        Args:
            book_id: ID of the book (for validation)
            tag_id: ID of the tag to update
            name: New name for the tag (optional)
            tag_group_id: ID of the tag group to associate with (optional, None to remove association)

        Returns:
            Updated HighlightTag model

        Raises:
            ValueError: If tag not found or doesn't belong to the specified book
            CrossbillError: If new name conflicts with existing tag
        """
        tag = self.highlight_tag_repo.get_by_id(tag_id, user_id)
        if not tag:
            raise ValueError(f"Tag with id {tag_id} not found")

        # Verify the tag belongs to the specified book
        if tag.book_id != book_id:
            raise ValueError(f"Tag {tag_id} does not belong to book {book_id}")

        # Validate tag group if provided
        if tag_group_id is not None:
            tag_group = self.highlight_tag_repo.get_tag_group_by_id(tag_group_id, user_id)
            if not tag_group:
                raise ValueError(f"Tag group with id {tag_group_id} not found")
            if tag_group.book_id != book_id:
                raise ValueError(f"Tag group {tag_group_id} does not belong to book {book_id}")

        # Prepare update data
        update_data = {}
        if name is not None:
            name = name.strip()
            if not name:
                raise ValueError("Tag name cannot be empty")
            # Check if new name conflicts with existing tag
            if name != tag.name:
                existing_tag = self.highlight_tag_repo.get_by_book_and_name(book_id, name, user_id)
                if existing_tag:
                    raise CrossbillError(
                        f"Tag '{name}' already exists for this book", status_code=409
                    )
            update_data["name"] = name

        # Allow explicit None to remove tag group association
        update_data["tag_group_id"] = tag_group_id

        # Update the tag
        updated_tag = self.highlight_tag_repo.update(tag_id, user_id, **update_data)
        if updated_tag:
            self.db.commit()
            logger.info(
                "updated_highlight_tag", tag_id=tag_id, book_id=book_id, updates=update_data
            )
            return updated_tag

        raise ValueError(f"Failed to update tag {tag_id}")

    # HighlightTagGroup service methods

    def get_tag_groups_for_book(self, book_id: int, user_id: int) -> list[models.HighlightTagGroup]:
        """
        Get all highlight tag groups for a book.

        Args:
            book_id: ID of the book

        Returns:
            List of HighlightTagGroup models (empty list if book doesn't exist)
        """
        return self.highlight_tag_repo.get_tag_groups_by_book_id(book_id, user_id)

    def upsert_tag_group(
        self, book_id: int, name: str, user_id: int, tag_group_id: int | None = None
    ) -> models.HighlightTagGroup:
        """
        Create a new tag group or update existing one.

        Args:
            book_id: ID of the book
            name: Name of the tag group
            tag_group_id: ID of existing tag group to update (optional)

        Returns:
            Created or updated HighlightTagGroup model

        Raises:
            ValueError: If book not found or tag group name is empty
            CrossbillError: If updating and tag group doesn't belong to the book
        """
        # Validate book exists
        book = self.book_repo.get_by_id(book_id, user_id)
        if not book:
            raise ValueError(f"Book with id {book_id} not found")

        # Validate tag group name
        name = name.strip()
        if not name:
            raise ValueError("Tag group name cannot be empty")

        # If updating, verify tag group belongs to the book
        if tag_group_id:
            existing_tag_group = self.highlight_tag_repo.get_tag_group_by_id(tag_group_id, user_id)
            if existing_tag_group and existing_tag_group.book_id != book_id:
                raise CrossbillError(
                    f"Tag group {tag_group_id} does not belong to book {book_id}", status_code=400
                )

        # Upsert the tag group
        tag_group = self.highlight_tag_repo.upsert_tag_group(book_id, user_id, name, tag_group_id)
        self.db.commit()

        logger.info(
            "upserted_highlight_tag_group",
            tag_group_id=tag_group.id,
            book_id=book_id,
            name=name,
        )
        return tag_group

    def delete_tag_group(self, tag_group_id: int, user_id: int) -> bool:
        """
        Delete a highlight tag group.

        Args:
            tag_group_id: ID of the tag group to delete

        Returns:
            True if deleted, False if not found
        """
        # Delete the tag group (tags' foreign keys will be set to NULL)
        success = self.highlight_tag_repo.delete_tag_group(tag_group_id, user_id)
        if success:
            self.db.commit()
            logger.info("deleted_highlight_tag_group", tag_group_id=tag_group_id)

        return success
