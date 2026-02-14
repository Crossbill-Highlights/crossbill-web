"""Get book details use case."""

import logging

from src.application.learning.protocols.flashcard_repository import FlashcardRepositoryProtocol
from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.library.protocols.chapter_repository import ChapterRepositoryProtocol
from src.application.library.use_cases.book_tag_associations.get_book_tags_use_case import (
    GetBookTagsUseCase,
)
from src.application.reading.protocols.bookmark_repository import BookmarkRepositoryProtocol
from src.application.reading.protocols.highlight_repository import HighlightRepositoryProtocol
from src.application.reading.protocols.highlight_tag_repository import (
    HighlightTagRepositoryProtocol,
)
from src.application.reading.protocols.reading_session_repository import (
    ReadingSessionRepositoryProtocol,
)
from src.application.reading.use_cases.highlight_tags.get_highlight_tags_for_book_use_case import (
    GetHighlightTagsForBookUseCase,
)
from src.domain.common.value_objects import BookId, UserId
from src.domain.library.services.book_details_aggregator import BookDetailsAggregation
from src.domain.reading.services.highlight_grouping_service import (
    ChapterWithHighlights,
    HighlightGroupingService,
)
from src.exceptions import BookNotFoundError

logger = logging.getLogger(__name__)


class GetBookDetailsUseCase:
    """Use case for getting detailed book information."""

    def __init__(
        self,
        book_repository: BookRepositoryProtocol,
        chapter_repository: ChapterRepositoryProtocol,
        bookmark_repository: BookmarkRepositoryProtocol,
        highlight_repository: HighlightRepositoryProtocol,
        highlight_tag_repository: HighlightTagRepositoryProtocol,
        flashcard_repository: FlashcardRepositoryProtocol,
        get_book_tags_use_case: GetBookTagsUseCase,
        highlight_tag_use_case: GetHighlightTagsForBookUseCase,
        highlight_grouping_service: HighlightGroupingService,
        reading_session_repository: ReadingSessionRepositoryProtocol,
    ) -> None:
        self.book_repository = book_repository
        self.chapter_repository = chapter_repository
        self.bookmark_repository = bookmark_repository
        self.highlight_repository = highlight_repository
        self.highlight_tag_repository = highlight_tag_repository
        self.flashcard_repository = flashcard_repository
        self.get_book_tags_use_case = get_book_tags_use_case
        self.highlight_tag_use_case = highlight_tag_use_case
        self.highlight_grouping_service = highlight_grouping_service
        self.reading_session_repository = reading_session_repository

    def get_book_details(self, book_id: int, user_id: int) -> BookDetailsAggregation:
        """
        Get detailed information about a book including its chapters and highlights.

        Also updates the book's last_viewed timestamp.

        Args:
            book_id: ID of the book to retrieve
            user_id: ID of the user

        Returns:
            BookDetailsAggregation with aggregated book data

        Raises:
            BookNotFoundError: If book is not found
        """
        # Convert primitives to value objects
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        # Fetch and update book (returns domain entity, not ORM)
        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        book.mark_as_viewed()
        book = self.book_repository.save(book)

        # Get highlight tags using use case (from reading context)
        highlight_tags = self.highlight_tag_use_case.get_tags(book_id, user_id)

        # Get all highlights for book (returns domain entities)
        highlights_with_context = self.highlight_repository.search(
            search_text="",
            user_id=user_id_vo,
            book_id=book_id_vo,
            limit=10000,
        )

        # Use domain service to group highlights by chapter
        grouped = self.highlight_grouping_service.group_by_chapter(
            [(h, c, tags, flashcards) for h, _, c, tags, flashcards in highlights_with_context]
        )

        # Load ALL chapters for this book (not just those with highlights)
        all_chapters = self.chapter_repository.find_all_by_book(book_id_vo, user_id_vo)

        # Merge: ensure every chapter appears, even those without highlights
        grouped_by_id = {g.chapter_id: g for g in grouped}
        merged: list[ChapterWithHighlights] = []
        for ch in all_chapters:
            if ch.id.value in grouped_by_id:
                existing = grouped_by_id.pop(ch.id.value)
                # Ensure parent_id and start_position are set from the chapter entity
                existing.parent_id = ch.parent_id.value if ch.parent_id else None
                existing.start_position = ch.start_position
                merged.append(existing)
            else:
                merged.append(
                    ChapterWithHighlights(
                        chapter_id=ch.id.value,
                        chapter_name=ch.name,
                        chapter_number=ch.chapter_number,
                        highlights=[],
                        parent_id=ch.parent_id.value if ch.parent_id else None,
                        start_position=ch.start_position,
                    )
                )
        # Append any highlight groups for chapters not in all_chapters (e.g. deleted chapters)
        for remaining in grouped_by_id.values():
            merged.append(remaining)

        # Get reading position from latest reading session
        latest_sessions = self.reading_session_repository.find_by_book_id(
            book_id_vo, user_id_vo, limit=1, offset=0
        )
        reading_position = latest_sessions[0].end_position if latest_sessions else None

        # Get bookmarks (returns domain entities)
        bookmarks = self.bookmark_repository.find_by_book(book_id_vo, user_id_vo)

        # Get tags using use case
        tags = self.get_book_tags_use_case.get_tags(book_id, user_id)

        # Get highlight tag groups
        highlight_tag_groups = self.highlight_tag_repository.find_groups_by_book(book_id_vo)

        # Get book-level flashcards (not associated with any highlight)
        all_flashcards = self.flashcard_repository.find_by_book(book_id_vo, user_id_vo)
        book_flashcards = [f for f in all_flashcards if f.highlight_id is None]

        # Return domain aggregation
        return BookDetailsAggregation(
            book=book,
            tags=tags,
            highlight_tags=highlight_tags,
            highlight_tag_groups=highlight_tag_groups,
            bookmarks=bookmarks,
            chapters_with_highlights=merged,
            book_flashcards=book_flashcards,
            reading_position=reading_position,
        )
