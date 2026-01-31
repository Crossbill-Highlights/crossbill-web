from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.common.value_objects.ids import BookId, ChapterId, UserId
from src.domain.library.entities.chapter import Chapter
from src.infrastructure.library.mappers.chapter_mapper import ChapterMapper
from src.models import Book as BookORM
from src.models import Chapter as ChapterORM


class ChapterRepository:
    """Domain-centric repository for Chapter persistence."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.mapper = ChapterMapper()

    def get_by_numbers(
        self, book_id: BookId, chapter_numbers: set[int], user_id: UserId
    ) -> dict[int, Chapter]:
        """
        Get chapters by their numeric chapter_number.

        Returns dict mapping chapter_number → Chapter entity.
        Only includes chapters with non-null chapter_number.
        Used during highlight upload for efficient chapter association.
        """
        if not chapter_numbers:
            return {}

        stmt = (
            select(ChapterORM)
            .join(BookORM, BookORM.id == ChapterORM.book_id)
            .where(BookORM.id == book_id.value)
            .where(BookORM.user_id == user_id.value)
            .where(ChapterORM.chapter_number.in_(chapter_numbers))
            .where(ChapterORM.chapter_number.is_not(None))
        )

        orm_models = self.db.execute(stmt).scalars().all()

        # Map to dict by chapter_number
        result: dict[int, Chapter] = {}
        for orm_model in orm_models:
            if orm_model.chapter_number is not None:
                result[orm_model.chapter_number] = self.mapper.to_domain(orm_model)

        return result

    def find_by_id(self, chapter_id: ChapterId) -> Chapter | None:
        """Find chapter by ID."""
        stmt = select(ChapterORM).where(ChapterORM.id == chapter_id.value)
        orm_model = self.db.execute(stmt).scalar_one_or_none()

        if not orm_model:
            return None

        return self.mapper.to_domain(orm_model)

    def save(self, chapter: Chapter) -> Chapter:
        """Persist chapter to database."""
        if chapter.id.value == 0:
            # Create new
            orm_model = self.mapper.to_orm(chapter)
            self.db.add(orm_model)
            self.db.flush()
            return self.mapper.to_domain(orm_model)
        # Update existing
        stmt = select(ChapterORM).where(ChapterORM.id == chapter.id.value)
        existing_orm = self.db.execute(stmt).scalar_one()
        self.mapper.to_orm(chapter, existing_orm)
        self.db.flush()
        return self.mapper.to_domain(existing_orm)
