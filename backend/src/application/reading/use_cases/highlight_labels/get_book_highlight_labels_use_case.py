"""Use case for getting highlight labels for a book."""

from src.application.common.ownership import require_book
from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.reading.protocols.highlight_style_repository import (
    HighlightStyleRepositoryProtocol,
)
from src.application.reading.services.label_resolution_service import LabelResolutionService
from src.domain.common.value_objects import BookId, UserId
from src.domain.reading.entities.highlight_style import HighlightStyle
from src.domain.reading.services.highlight_style_resolver import ResolvedLabel


class GetBookHighlightLabelsUseCase:
    """Get all highlight labels for a book with resolved labels."""

    def __init__(
        self,
        highlight_style_repository: HighlightStyleRepositoryProtocol,
        book_repository: BookRepositoryProtocol,
        label_resolution_service: LabelResolutionService,
    ) -> None:
        self.highlight_style_repository = highlight_style_repository
        self.book_repository = book_repository
        self.label_resolution_service = label_resolution_service

    async def execute(
        self, book_id: int, user_id: int
    ) -> list[tuple[HighlightStyle, ResolvedLabel, int]]:
        """Returns list of (style, resolved_label, highlight_count) for the book."""
        user_id_vo = UserId(user_id)
        book_id_vo = BookId(book_id)

        await require_book(self.book_repository, book_id_vo, user_id_vo)

        combination_labels = await self.label_resolution_service.resolve_combination_labels(
            user_id_vo, book_id_vo
        )

        results: list[tuple[HighlightStyle, ResolvedLabel, int]] = []
        for style, resolved in combination_labels:
            count = await self.highlight_style_repository.count_highlights_by_style(style.id)
            results.append((style, resolved, count))

        return results
