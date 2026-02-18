"""Helper for resolving highlight labels in API responses."""

from src.domain.common.value_objects import BookId, UserId
from src.domain.reading.services.highlight_style_resolver import (
    HighlightStyleResolver,
    ResolvedLabel,
)
from src.infrastructure.reading.repositories.highlight_style_repository import (
    HighlightStyleRepository,
)


class HighlightLabelResolver:
    """Resolves labels for a batch of highlights efficiently."""

    def __init__(
        self,
        highlight_style_repository: HighlightStyleRepository,
        resolver: HighlightStyleResolver,
    ) -> None:
        self.style_repo = highlight_style_repository
        self.resolver = resolver

    def resolve_for_book(
        self, user_id: UserId, book_id: BookId
    ) -> dict[int, ResolvedLabel]:
        """Resolve labels for all highlight styles in a book.

        Returns a dict mapping highlight_style_id -> ResolvedLabel.
        """
        all_styles = self.style_repo.find_for_resolution(user_id, book_id)

        result: dict[int, ResolvedLabel] = {}
        for style in all_styles:
            if style.is_combination_level() and not style.is_global():
                resolved = self.resolver.resolve(style, all_styles)
                result[style.id.value] = resolved

        return result
