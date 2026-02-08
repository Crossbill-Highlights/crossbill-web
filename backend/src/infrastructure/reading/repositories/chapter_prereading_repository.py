"""Repository for ChapterPrereadingContent domain entities."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.common.value_objects.ids import BookId, ChapterId, PrereadingContentId
from src.domain.reading.entities.chapter_prereading_content import (
    ChapterPrereadingContent,
)
from src.infrastructure.reading.mappers.chapter_prereading_mapper import (
    ChapterPrereadingMapper,
)
from src.models import Chapter as ChapterORM
from src.models import ChapterPrereadingContent as PrereadingContentORM


class ChapterPrereadingRepository:
    """Repository implementation for chapter prereading content."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.mapper = ChapterPrereadingMapper()

    def find_by_id(self, id: PrereadingContentId) -> ChapterPrereadingContent | None:
        """Find prereading content by ID."""
        stmt = select(PrereadingContentORM).where(PrereadingContentORM.id == id.value)
        orm = self.db.execute(stmt).scalar_one_or_none()
        return self.mapper.to_domain(orm) if orm else None

    def find_all_by_book_id(self, book_id: BookId) -> list[ChapterPrereadingContent]:
        """Find all prereading content for chapters in a book."""
        stmt = (
            select(PrereadingContentORM)
            .join(ChapterORM, PrereadingContentORM.chapter_id == ChapterORM.id)
            .where(ChapterORM.book_id == book_id.value)
        )
        orms = self.db.execute(stmt).scalars().all()
        return [self.mapper.to_domain(orm) for orm in orms]

    def find_by_chapter_id(self, chapter_id: ChapterId) -> ChapterPrereadingContent | None:
        """Find prereading content for a specific chapter."""
        stmt = select(PrereadingContentORM).where(
            PrereadingContentORM.chapter_id == chapter_id.value
        )
        orm = self.db.execute(stmt).scalar_one_or_none()
        return self.mapper.to_domain(orm) if orm else None

    def save(self, content: ChapterPrereadingContent) -> ChapterPrereadingContent:
        """Save or update prereading content."""
        # Check if exists by chapter_id (unique constraint)
        existing = None
        if content.id.value != 0:
            existing = self.db.get(PrereadingContentORM, content.id.value)

        if not existing:
            # Also check by chapter_id for upsert behavior
            stmt = select(PrereadingContentORM).where(
                PrereadingContentORM.chapter_id == content.chapter_id.value
            )
            existing = self.db.execute(stmt).scalar_one_or_none()

        if existing:
            orm = self.mapper.to_orm(content, existing)
            self.db.commit()
            self.db.refresh(orm)
            return self.mapper.to_domain(orm)
        orm = self.mapper.to_orm(content)
        self.db.add(orm)
        self.db.commit()
        self.db.refresh(orm)
        return self.mapper.to_domain(orm)

    def delete(self, id: PrereadingContentId) -> None:
        """Delete prereading content by ID."""
        stmt = select(PrereadingContentORM).where(PrereadingContentORM.id == id.value)
        orm = self.db.execute(stmt).scalar_one_or_none()
        if orm:
            self.db.delete(orm)
            self.db.commit()
