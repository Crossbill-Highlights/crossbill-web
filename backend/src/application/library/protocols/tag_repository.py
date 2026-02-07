"""Protocol for Tag repository in library context."""

from typing import Protocol

from src.domain.common.value_objects.ids import BookId, TagId, UserId
from src.domain.library.entities.tag import Tag


class TagRepositoryProtocol(Protocol):
    """Protocol for Tag repository operations in library context."""

    def find_tags_for_book(self, book_id: BookId, user_id: UserId) -> list[Tag]:
        """
        Get all tags associated with a book.

        Args:
            book_id: The book ID
            user_id: The user ID

        Returns:
            List of tag entities
        """
        ...

    def get_or_create_many(self, names: list[str], user_id: UserId) -> list[Tag]:
        """
        Get existing tags or create new ones for a list of names.

        Args:
            names: List of tag names
            user_id: The user ID

        Returns:
            List of tag entities (mix of existing and newly created)
        """
        ...

    def add_tags_to_book(self, book_id: BookId, tag_ids: list[TagId], user_id: UserId) -> None:
        """
        Add tags to a book (manages the many-to-many association).

        Only adds tags that are not already associated with the book.

        Args:
            book_id: The book ID
            tag_ids: List of tag IDs to add
            user_id: The user ID for authorization check
        """
        ...

    def replace_book_tags(self, book_id: BookId, tag_ids: list[TagId], user_id: UserId) -> None:
        """
        Replace all tags on a book (manages the many-to-many association).

        Args:
            book_id: The book ID
            tag_ids: List of tag IDs (will replace all existing tags)
            user_id: The user ID for authorization check
        """
        ...
