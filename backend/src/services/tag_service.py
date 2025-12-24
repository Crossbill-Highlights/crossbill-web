"""Service layer for tag-related business logic."""

import logging

from sqlalchemy.orm import Session

from src import models, repositories

logger = logging.getLogger(__name__)


class TagService:
    """Service for handling tag-related operations."""

    def __init__(self, db: Session) -> None:
        """Initialize service with database session."""
        self.db = db
        self.tag_repo = repositories.TagRepository(db)
        self.book_repo = repositories.BookRepository(db)

    def update_book_tags(self, book_id: int, tag_names: list[str], user_id: int) -> models.Book:
        """
        Update the tags associated with a book.

        This method will:
        - Create new tags if they don't exist
        - Replace the book's current tags with the provided tags
        - Reuse existing tags if they already exist

        Args:
            book_id: ID of the book to update
            tag_names: List of tag names to associate with the book

        Returns:
            Updated book with new tags

        Raises:
            ValueError: If book is not found
        """
        book = self.book_repo.get_by_id(book_id, user_id)
        if not book:
            raise ValueError(f"Book with id {book_id} not found")

        # Get or create tags
        tags = []
        for tag_name in tag_names:
            name = tag_name.strip()
            if name:  # Skip empty strings
                tag = self.tag_repo.get_or_create(name, user_id)
                tags.append(tag)

        # Update book's tags
        book.tags = tags
        self.db.flush()
        self.db.refresh(book)

        logger.info(f"Updated tags for book {book_id}: {[tag.name for tag in tags]}")
        return book

    def add_book_tags(self, book_id: int, tag_names: list[str], user_id: int) -> models.Book:
        """
        Add tags to a book without removing existing tags.

        This method will:
        - Create new tags if they don't exist
        - Add new tags to the book's existing tags
        - Skip tags that are already associated with the book
        - Reuse existing tags if they already exist

        Args:
            book_id: ID of the book to update
            tag_names: List of tag names to add to the book
            user_id: ID of the user

        Returns:
            Updated book with new tags

        Raises:
            ValueError: If book is not found
        """
        book = self.book_repo.get_by_id(book_id, user_id)
        if not book:
            raise ValueError(f"Book with id {book_id} not found")

        # Get existing tag names for this book
        existing_tag_names = {tag.name for tag in book.tags}

        # Get or create tags and add new ones
        new_tags_added = []
        for tag_name in tag_names:
            name = tag_name.strip()
            if name and name not in existing_tag_names:
                tag = self.tag_repo.get_or_create(name, user_id)
                book.tags.append(tag)
                new_tags_added.append(name)

        if new_tags_added:
            self.db.flush()
            self.db.refresh(book)
            logger.info(f"Added tags to book {book_id}: {new_tags_added}")

        return book
