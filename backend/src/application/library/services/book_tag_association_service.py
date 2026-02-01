"""
Application service for managing book-tag associations.

Handles adding and replacing tags on books.
"""

import structlog
from sqlalchemy.orm import Session

from src.domain.common.value_objects.ids import BookId, UserId
from src.domain.library.entities.tag import Tag
from src.domain.reading.exceptions import BookNotFoundError
from src.infrastructure.library.repositories.book_repository import BookRepository
from src.infrastructure.library.repositories.tag_repository import TagRepository

logger = structlog.get_logger(__name__)


class BookTagAssociationService:
    """Application service for managing book-tag associations."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.tag_repository = TagRepository(db)
        self.book_repository = BookRepository(db)

    def add_tags_to_book(self, book_id: int, tag_names: list[str], user_id: int) -> list[Tag]:
        """
        Add tags to book without removing existing ones.

        Args:
            book_id: ID of the book
            tag_names: List of tag names to add
            user_id: ID of the user

        Returns:
            All tags for the book after addition

        Raises:
            BookNotFoundError: If book not found
        """
        # Convert to value objects
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        # Validate book exists
        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(f"Book with id {book_id} not found")

        if not tag_names:
            # Return existing tags if no new ones to add
            return self.tag_repository.find_tags_for_book(book_id_vo, user_id_vo)

        # Get or create tags (bulk operation)
        all_tags = self.tag_repository.get_or_create_many(tag_names, user_id_vo)

        # Add tags to book using repository (handles duplicates)
        tag_ids = [tag.id for tag in all_tags]
        self.tag_repository.add_tags_to_book(book_id_vo, tag_ids, user_id_vo)
        self.db.commit()

        # Log the operation
        logger.info(
            "added_tags_to_book",
            book_id=book_id,
            tag_count=len(all_tags),
            tag_names=[tag.name for tag in all_tags],
        )

        # Return all tags for book
        return self.tag_repository.find_tags_for_book(book_id_vo, user_id_vo)

    def replace_book_tags(self, book_id: int, tag_names: list[str], user_id: int) -> list[Tag]:
        """
        Replace all tags on a book.

        Args:
            book_id: ID of the book
            tag_names: List of tag names (will replace all existing tags)
            user_id: ID of the user

        Returns:
            New tags for the book

        Raises:
            BookNotFoundError: If book not found
        """
        # Convert to value objects
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        # Validate book exists
        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(f"Book with id {book_id} not found")

        # Get or create tags (bulk operation)
        tags = self.tag_repository.get_or_create_many(tag_names, user_id_vo)

        # Replace book tags using repository
        tag_ids = [tag.id for tag in tags]
        self.tag_repository.replace_book_tags(book_id_vo, tag_ids, user_id_vo)
        self.db.commit()

        logger.info(
            "replaced_book_tags",
            book_id=book_id,
            tag_count=len(tags),
            tag_names=[tag.name for tag in tags],
        )

        return tags

    def get_tags_for_book(self, book_id: int, user_id: int) -> list[Tag]:
        """
        Get all tags for a book.

        Args:
            book_id: ID of the book
            user_id: ID of the user

        Returns:
            List of tags for the book

        Raises:
            BookNotFoundError: If book not found
        """
        # Convert to value objects
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        # Validate book exists
        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(f"Book with id {book_id} not found")

        return self.tag_repository.find_tags_for_book(book_id_vo, user_id_vo)
