"""Repository for BookReflection domain entities."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.common.value_objects import BookId, UserId
from src.domain.reflection.entities.book_reflection import BookReflection
from src.domain.reflection.exceptions import BookReflectionNotFoundError
from src.infrastructure.common.repositories import BaseRepository
from src.infrastructure.notes.orm.note_model import Note as NoteORM
from src.infrastructure.reflection.mappers.book_reflection_mapper import BookReflectionMapper
from src.infrastructure.reflection.orm.book_reflection_model import (
    BookReflection as BookReflectionORM,
)


class BookReflectionRepository(BaseRepository[BookReflection, BookReflectionORM]):
    """Repository for BookReflection domain entities.

    ``save`` is overridden because a reflection also owns a note association
    collection that must be synced from the referenced ORM rows.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.mapper = BookReflectionMapper()
        super().__init__(db, BookReflectionORM, self.mapper)

    async def find_by_book_id(self, book_id: BookId, user_id: UserId) -> BookReflection | None:
        stmt = select(BookReflectionORM).where(
            BookReflectionORM.book_id == book_id.value,
            BookReflectionORM.user_id == user_id.value,
        )
        result = await self.db.execute(stmt)
        orm_model = result.scalar_one_or_none()
        return self.mapper.to_domain(orm_model) if orm_model is not None else None

    async def save(self, reflection: BookReflection) -> BookReflection:
        if reflection.id.value == 0:
            orm_model = self.mapper.to_orm(reflection)
            await self._sync_notes(orm_model, reflection)
            self.db.add(orm_model)
            await self.db.flush()
        else:
            orm_model = await self.db.get(BookReflectionORM, reflection.id.value)
            if not orm_model:
                raise BookReflectionNotFoundError(reflection.id.value)
            self.mapper.to_orm(reflection, orm_model)
            await self._sync_notes(orm_model, reflection)
        reflection_id = orm_model.id
        await self.db.commit()

        stmt = select(BookReflectionORM).where(BookReflectionORM.id == reflection_id)
        result = await self.db.execute(stmt)
        saved = result.scalar_one()
        return self.mapper.to_domain(saved)

    async def _sync_notes(self, orm_model: BookReflectionORM, reflection: BookReflection) -> None:
        """Replace the note association rows with rows matching the reflection's ids."""
        if reflection.note_ids:
            result = await self.db.execute(
                select(NoteORM).where(NoteORM.id.in_(reflection.note_ids))
            )
            orm_model.notes = list(result.scalars().all())
        else:
            orm_model.notes = []
