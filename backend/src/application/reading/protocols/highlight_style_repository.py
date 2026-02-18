"""Protocol for HighlightStyle repository."""

from typing import Protocol

from src.domain.common.value_objects import BookId, HighlightStyleId, UserId
from src.domain.reading.entities.highlight_style import HighlightStyle


class HighlightStyleRepositoryProtocol(Protocol):
    """Interface for HighlightStyle persistence."""

    def find_by_id(self, style_id: HighlightStyleId, user_id: UserId) -> HighlightStyle | None: ...

    def find_or_create(
        self,
        user_id: UserId,
        book_id: BookId,
        device_color: str | None,
        device_style: str | None,
    ) -> HighlightStyle: ...

    def find_by_book(self, book_id: BookId, user_id: UserId) -> list[HighlightStyle]: ...

    def find_global(self, user_id: UserId) -> list[HighlightStyle]: ...

    def find_for_resolution(self, user_id: UserId, book_id: BookId) -> list[HighlightStyle]: ...

    def save(self, style: HighlightStyle) -> HighlightStyle: ...

    def count_highlights_by_style(self, style_id: HighlightStyleId) -> int: ...
