"""Protocol for HighlightTag and HighlightTagGroup repository operations."""

from typing import Protocol

from src.domain.common.value_objects.ids import (
    BookId,
    HighlightId,
    HighlightTagGroupId,
    HighlightTagId,
    UserId,
)
from src.domain.reading.entities.highlight_tag import HighlightTag
from src.domain.reading.entities.highlight_tag_group import HighlightTagGroup


class HighlightTagRepositoryProtocol(Protocol):
    """Protocol defining the interface for HighlightTag and HighlightTagGroup repository operations."""

    # Tag methods

    def find_by_id(self, tag_id: HighlightTagId, user_id: UserId) -> HighlightTag | None: ...

    def find_by_book_and_name(
        self, book_id: BookId, name: str, user_id: UserId
    ) -> HighlightTag | None: ...

    def find_by_book(self, book_id: BookId, user_id: UserId) -> list[HighlightTag]: ...

    def save(self, tag: HighlightTag) -> HighlightTag: ...

    def delete(self, tag_id: HighlightTagId, user_id: UserId) -> bool: ...

    # Tag group methods

    def find_groups_by_book(self, book_id: BookId) -> list[HighlightTagGroup]: ...

    def find_group_by_id(
        self, group_id: HighlightTagGroupId, book_id: BookId
    ) -> HighlightTagGroup | None: ...

    def find_group_by_name(self, book_id: BookId, name: str) -> HighlightTagGroup | None: ...

    def save_group(self, group: HighlightTagGroup) -> HighlightTagGroup: ...

    def delete_group(self, group_id: HighlightTagGroupId) -> bool: ...

    def check_group_exists(self, group_id: HighlightTagGroupId) -> bool: ...

    # Tag-Highlight association methods

    def add_tag_to_highlight(
        self, highlight_id: HighlightId, tag_id: HighlightTagId, user_id: UserId
    ) -> bool: ...

    def remove_tag_from_highlight(
        self, highlight_id: HighlightId, tag_id: HighlightTagId, user_id: UserId
    ) -> bool: ...
