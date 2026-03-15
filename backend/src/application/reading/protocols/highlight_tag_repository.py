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

    async def find_by_id(self, tag_id: HighlightTagId, user_id: UserId) -> HighlightTag | None: ...

    async def find_by_book_and_name(
        self, book_id: BookId, name: str, user_id: UserId
    ) -> HighlightTag | None: ...

    async def find_by_book(self, book_id: BookId, user_id: UserId) -> list[HighlightTag]: ...

    async def save(self, tag: HighlightTag) -> HighlightTag: ...

    async def delete(self, tag_id: HighlightTagId, user_id: UserId) -> bool: ...

    # Tag group methods

    async def find_groups_by_book(self, book_id: BookId) -> list[HighlightTagGroup]: ...

    async def find_group_by_id(
        self, group_id: HighlightTagGroupId, book_id: BookId
    ) -> HighlightTagGroup | None: ...

    async def find_group_by_name(self, book_id: BookId, name: str) -> HighlightTagGroup | None: ...

    async def save_group(self, group: HighlightTagGroup) -> HighlightTagGroup: ...

    async def delete_group(self, group_id: HighlightTagGroupId) -> bool: ...

    async def check_group_exists(self, group_id: HighlightTagGroupId) -> bool: ...

    # Tag-Highlight association methods

    async def add_tag_to_highlight(
        self, highlight_id: HighlightId, tag_id: HighlightTagId, user_id: UserId
    ) -> bool: ...

    async def remove_tag_from_highlight(
        self, highlight_id: HighlightId, tag_id: HighlightTagId, user_id: UserId
    ) -> bool: ...
