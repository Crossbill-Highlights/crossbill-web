from typing import Protocol

from src.domain.common.value_objects.ids import BookId, ChapterId, UserId


class ChapterPrereadingProviderProtocol(Protocol):
    async def get_chapter_ids_needing_prereading(
        self, book_id: BookId, user_id: UserId
    ) -> list[ChapterId]: ...
