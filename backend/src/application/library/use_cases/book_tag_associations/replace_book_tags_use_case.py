"""
Use case for replacing all tags on a book.
"""

import structlog

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.library.protocols.tag_repository import TagRepositoryProtocol
from src.domain.common.value_objects.ids import BookId, UserId
from src.domain.library.entities.tag import Tag
from src.domain.reading.exceptions import BookNotFoundError

logger = structlog.get_logger(__name__)


class ReplaceBookTagsUseCase:
    """Use case for replacing all tags on a book."""

    def __init__(
        self,
        tag_repository: TagRepositoryProtocol,
        book_repository: BookRepositoryProtocol,
    ) -> None:
        """
        Initialize use case with dependencies.

        Args:
            tag_repository: Tag repository protocol implementation
            book_repository: Book repository protocol implementation
        """
        self.tag_repository = tag_repository
        self.book_repository = book_repository

    def replace_tags(self, book_id: int, tag_names: list[str], user_id: int) -> list[Tag]:
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
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(f"Book with id {book_id} not found")

        tags = self.tag_repository.get_or_create_many(tag_names, user_id_vo)

        tag_ids = [tag.id for tag in tags]
        self.tag_repository.replace_book_tags(book_id_vo, tag_ids, user_id_vo)

        logger.info(
            "replaced_book_tags",
            book_id=book_id,
            tag_count=len(tags),
            tag_names=[tag.name for tag in tags],
        )

        return tags
