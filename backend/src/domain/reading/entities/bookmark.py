"""Bookmark entity for tracking reading progress."""

from dataclasses import dataclass
from datetime import datetime

from src.domain.common.entity import Entity
from src.domain.common.value_objects.ids import BookId, BookmarkId, HighlightId


@dataclass
class Bookmark(Entity[BookmarkId]):
    """
    Bookmark that marks a highlight as a reading progress marker.

    Business Rules:
    - A bookmark links a highlight within a book
    - User ownership is verified through the book relationship
    - One bookmark per highlight (uniqueness enforced at book+highlight level)
    """

    id: BookmarkId
    book_id: BookId
    highlight_id: HighlightId
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate invariants."""
        # No additional validation needed - IDs validated by value objects

    def belongs_to_book(self, book_id: BookId) -> bool:
        """Check if this bookmark belongs to the specified book."""
        return self.book_id == book_id

    def marks_highlight(self, highlight_id: HighlightId) -> bool:
        """Check if this bookmark marks the specified highlight."""
        return self.highlight_id == highlight_id

    @classmethod
    def create(cls, book_id: BookId, highlight_id: HighlightId) -> "Bookmark":
        """
        Create a new bookmark.

        Args:
            book_id: ID of the book
            highlight_id: ID of the highlight to bookmark

        Returns:
            New Bookmark instance
        """
        return cls(
            id=BookmarkId.generate(),
            book_id=book_id,
            highlight_id=highlight_id,
        )

    @classmethod
    def create_with_id(
        cls,
        id: BookmarkId,
        book_id: BookId,
        highlight_id: HighlightId,
        created_at: datetime,
    ) -> "Bookmark":
        """
        Reconstitute a bookmark from persistence.

        Args:
            id: Existing bookmark ID
            book_id: ID of the book
            highlight_id: ID of the highlight
            created_at: Timestamp when bookmark was created

        Returns:
            Reconstituted Bookmark instance
        """
        return cls(
            id=id,
            book_id=book_id,
            highlight_id=highlight_id,
            created_at=created_at,
        )
