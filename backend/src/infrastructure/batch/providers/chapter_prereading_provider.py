"""Provider for determining which chapters need prereading generated."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.common.value_objects.ids import BookId, ChapterId, UserId
from src.models import Chapter, ChapterPrereadingContent


class ChapterPrereadingProvider:
    """Queries which chapter IDs in a book are missing prereading content."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_chapter_ids_needing_prereading(
        self, book_id: BookId, user_id: UserId
    ) -> list[ChapterId]:
        """Return chapter IDs that belong to the book and don't have prereading yet."""
        # Subquery: chapters that already have prereading
        has_prereading = (
            select(ChapterPrereadingContent.chapter_id)
            .where(ChapterPrereadingContent.chapter_id == Chapter.id)
            .correlate(Chapter)
            .exists()
        )

        result = await self.db.execute(
            select(Chapter.id)
            .where(
                Chapter.book_id == book_id.value,
                ~has_prereading,
            )
            .order_by(Chapter.id)
        )

        return [ChapterId(row[0]) for row in result.all()]
