"""
Book-scoped highlight search.

Provides full-text search within a specific book's highlights.
"""

from src.application.reading.protocols.book_repository import BookRepositoryProtocol
from src.application.reading.protocols.highlight_repository import HighlightRepositoryProtocol
from src.application.reading.protocols.highlight_style_repository import (
    HighlightStyleRepositoryProtocol,
)
from src.domain.common.value_objects import BookId, UserId
from src.domain.reading.services.highlight_grouping_service import (
    ChapterWithHighlights,
    HighlightGroupingService,
)
from src.domain.reading.services.highlight_style_resolver import (
    HighlightStyleResolver,
    ResolvedLabel,
)
from src.exceptions import BookNotFoundError


class HighlightSearchUseCase:
    def __init__(
        self,
        book_repository: BookRepositoryProtocol,
        highlight_repository: HighlightRepositoryProtocol,
        highlight_style_repository: HighlightStyleRepositoryProtocol | None = None,
        highlight_style_resolver: HighlightStyleResolver | None = None,
    ) -> None:
        self.book_repository = book_repository
        self.highlight_repository = highlight_repository
        self.highlight_grouping_service = HighlightGroupingService()
        self.highlight_style_repository = highlight_style_repository
        self.highlight_style_resolver = highlight_style_resolver

    def search_book_highlights(
        self, book_id: int, user_id: int, search_text: str, limit: int = 100
    ) -> tuple[list[ChapterWithHighlights], int, dict[int, ResolvedLabel]]:
        """
        Search for highlights within a specific book using full-text search.

        Results are grouped by chapter, with only chapters containing
        matching highlights included in the response.

        Args:
            book_id: ID of the book to search within
            user_id: ID of the user
            search_text: Text to search for
            limit: Maximum number of results to return

        Returns:
            Tuple of (chapters with highlights, total highlight count, resolved labels)

        Raises:
            BookNotFoundError: If book is not found or doesn't belong to user
        """
        # Convert primitives to value objects
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        # Verify book exists and belongs to user
        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        # Search highlights (returns domain entities)
        highlights_with_context = self.highlight_repository.search(
            search_text=search_text,
            user_id=user_id_vo,
            book_id=book_id_vo,
            limit=limit,
        )

        # Use domain service to group highlights by chapter
        grouped = self.highlight_grouping_service.group_by_chapter(
            [(h, c, tags, flashcards) for h, _, c, tags, flashcards in highlights_with_context]
        )

        # Calculate total number of highlights
        total = sum(len(chapter_group.highlights) for chapter_group in grouped)

        # Resolve labels
        labels: dict[int, ResolvedLabel] = {}
        if self.highlight_style_repository and self.highlight_style_resolver:
            all_styles = self.highlight_style_repository.find_for_resolution(user_id_vo, book_id_vo)
            for style in all_styles:
                if style.is_combination_level() and not style.is_global():
                    resolved = self.highlight_style_resolver.resolve(style, all_styles)
                    labels[style.id.value] = resolved

        return (grouped, total, labels)
