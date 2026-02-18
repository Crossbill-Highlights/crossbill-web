"""Use case for getting highlight labels for a book."""

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.reading.protocols.highlight_style_repository import (
    HighlightStyleRepositoryProtocol,
)
from src.domain.common.value_objects import BookId, UserId
from src.domain.reading.entities.highlight_style import HighlightStyle
from src.domain.reading.services.highlight_style_resolver import (
    HighlightStyleResolver,
    ResolvedLabel,
)
from src.exceptions import NotFoundError


class GetBookHighlightLabelsUseCase:
    """Get all highlight labels for a book with resolved labels."""

    def __init__(
        self,
        highlight_style_repository: HighlightStyleRepositoryProtocol,
        book_repository: BookRepositoryProtocol,
        highlight_style_resolver: HighlightStyleResolver,
    ) -> None:
        self.highlight_style_repository = highlight_style_repository
        self.book_repository = book_repository
        self.resolver = highlight_style_resolver

    def execute(
        self, book_id: int, user_id: int
    ) -> list[tuple[HighlightStyle, ResolvedLabel, int]]:
        """Returns list of (style, resolved_label, highlight_count) for the book."""
        user_id_vo = UserId(user_id)
        book_id_vo = BookId(book_id)

        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise NotFoundError(f"Book {book_id} not found")

        all_styles = self.highlight_style_repository.find_for_resolution(user_id_vo, book_id_vo)

        book_combo_styles = [
            s for s in all_styles if s.is_combination_level() and not s.is_global()
        ]

        results: list[tuple[HighlightStyle, ResolvedLabel, int]] = []
        for style in book_combo_styles:
            resolved = self.resolver.resolve(style, all_styles)
            count = self.highlight_style_repository.count_highlights_by_style(style.id)
            results.append((style, resolved, count))

        return results
