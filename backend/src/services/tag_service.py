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
