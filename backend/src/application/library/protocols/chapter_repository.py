"""Protocol for Chapter repository in library context."""

from typing import Protocol

from src.domain.common.value_objects.ids import BookId, ChapterId, UserId
from src.domain.library.entities.chapter import Chapter


class ChapterRepositoryProtocol(Protocol):
    """Protocol for Chapter repository operations in library context."""

    def find_by_id(self, chapter_id: ChapterId, user_id: UserId) -> Chapter | None:
        """Find a chapter by ID with ownership verification."""
        ...

    def sync_chapters_from_toc(
        self, book_id: BookId, user_id: UserId, chapters: list[tuple[str, int, str | None]]
    ) -> int:
        """
        Synchronize chapters from TOC data, creating new and updating existing chapters.

        This method handles bulk chapter creation/update from EPUB TOC parsing.
        It preserves hierarchical parent-child relationships and handles duplicates.

        Args:
            book_id: ID of the book
            user_id: ID of the user (for ownership verification)
            chapters: List of (chapter_name, chapter_number, parent_name) tuples

        Returns:
            Number of chapters created (not including updates)
        """
        ...
