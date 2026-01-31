"""
Application service for highlight tag CRUD operations.

Handles core tag operations: create, delete, rename, and list.
"""

import structlog
from sqlalchemy.orm import Session

from src.domain.common.value_objects.ids import BookId, HighlightTagId, UserId
from src.domain.reading.entities.highlight_tag import HighlightTag
from src.exceptions import CrossbillError
from src.infrastructure.library.repositories.book_repository import BookRepository
from src.infrastructure.reading.repositories.highlight_tag_repository import (
    HighlightTagRepository,
)

logger = structlog.get_logger(__name__)


class HighlightTagService:
    """Application service for highlight tag CRUD operations."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.tag_repository = HighlightTagRepository(db)
        self.book_repository = BookRepository(db)

    def create_tag(self, book_id: int, name: str, user_id: int) -> HighlightTag:
        """
        Create a new tag for a book.

        Args:
            book_id: ID of the book
            name: Name of the tag
            user_id: ID of the user creating the tag

        Returns:
            Created tag entity

        Raises:
            ValueError: If book not found
            CrossbillError: If tag with same name already exists
        """
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise ValueError(f"Book with id {book_id} not found")

        existing_tag = self.tag_repository.find_by_book_and_name(
            book_id_vo, name.strip(), user_id_vo
        )
        if existing_tag:
            raise CrossbillError(f"Tag '{name}' already exists for this book", status_code=409)

        tag = HighlightTag.create(
            user_id=user_id_vo,
            book_id=book_id_vo,
            name=name,
        )

        tag = self.tag_repository.save(tag)
        self.db.commit()

        logger.info("created_highlight_tag", tag_id=tag.id.value, book_id=book_id)
        return tag

    def delete_tag(self, book_id: int, tag_id: int, user_id: int) -> bool:
        """
        Delete a tag.

        Args:
            book_id: ID of the book
            tag_id: ID of the tag to delete
            user_id: ID of the user

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If tag doesn't belong to book
        """
        tag_id_vo = HighlightTagId(tag_id)
        user_id_vo = UserId(user_id)

        tag = self.tag_repository.find_by_id(tag_id_vo, user_id_vo)
        if not tag:
            return False

        if tag.book_id.value != book_id:
            raise ValueError(f"Tag {tag_id} does not belong to book {book_id}")

        success = self.tag_repository.delete(tag_id_vo, user_id_vo)
        if success:
            self.db.commit()
            logger.info("deleted_highlight_tag", tag_id=tag_id, book_id=book_id)

        return success

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
            ValueError: If tag not found or doesn't belong to book
            CrossbillError: If new name already exists
        """
        tag_id_vo = HighlightTagId(tag_id)
        user_id_vo = UserId(user_id)
        book_id_vo = BookId(book_id)

        # Load tag
        tag = self.tag_repository.find_by_id(tag_id_vo, user_id_vo)
        if not tag:
            raise ValueError(f"Tag with id {tag_id} not found")

        if tag.book_id != book_id_vo:
            raise ValueError(f"Tag {tag_id} does not belong to book {book_id}")

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
        self.db.commit()

        logger.info("updated_highlight_tag_name", tag_id=tag_id, new_name=new_name)
        return tag

    def get_tags_for_book(self, book_id: int, user_id: int) -> list[HighlightTag]:
        """
        Get all tags for a book.

        Args:
            book_id: ID of the book
            user_id: ID of the user

        Returns:
            List of tag entities

        Raises:
            ValueError: If book not found
        """
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        # Validate book exists
        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise ValueError(f"Book with id {book_id} not found")

        return self.tag_repository.find_by_book(book_id_vo, user_id_vo)
