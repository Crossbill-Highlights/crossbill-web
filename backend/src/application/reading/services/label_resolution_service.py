"""Application service that resolves highlight labels for a book.

This collapses the label-resolution block that used to be copy-pasted into
every use case that returns highlights. Use cases depend on this single service
instead of juggling a highlight-style repository and resolver pair.
"""

from src.application.reading.protocols.highlight_style_repository import (
    HighlightStyleRepositoryProtocol,
)
from src.domain.common.value_objects import BookId, UserId
from src.domain.reading.entities.highlight_style import HighlightStyle
from src.domain.reading.services.highlight_style_resolver import (
    HighlightStyleResolver,
    ResolvedLabel,
)


class LabelResolutionService:
    """Resolves effective labels for a book's combination-level highlight styles."""

    def __init__(
        self,
        highlight_style_repository: HighlightStyleRepositoryProtocol,
        highlight_style_resolver: HighlightStyleResolver,
    ) -> None:
        self._style_repository = highlight_style_repository
        self._resolver = highlight_style_resolver

    async def resolve_combination_labels(
        self, user_id: UserId, book_id: BookId
    ) -> list[tuple[HighlightStyle, ResolvedLabel]]:
        """Resolve every book-scoped combination style paired with its label."""
        all_styles = await self._style_repository.find_for_resolution(user_id, book_id)
        return [
            (style, self._resolver.resolve(style, all_styles))
            for style in all_styles
            if style.is_combination_level() and not style.is_global()
        ]

    async def resolve_for_book(
        self, user_id: UserId, book_id: BookId
    ) -> dict[int, ResolvedLabel]:
        """Map highlight-style id to its resolved label for a book."""
        return {
            style.id.value: label
            for style, label in await self.resolve_combination_labels(user_id, book_id)
        }
