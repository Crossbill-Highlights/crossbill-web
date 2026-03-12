"""Repository for Flashcard domain entities."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.common.value_objects.ids import BookId, FlashcardId, UserId
from src.domain.learning.entities.flashcard import Flashcard
from src.infrastructure.learning.mappers.flashcard_mapper import FlashcardMapper
from src.models import Flashcard as FlashcardORM


class FlashcardRepository:
    """Repository for Flashcard domain entities."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.mapper = FlashcardMapper()

    async def find_by_id(self, flashcard_id: FlashcardId, user_id: UserId) -> Flashcard | None:
        """
        Find a flashcard by ID with user ownership check.

        Args:
            flashcard_id: The flashcard ID
            user_id: The user ID for ownership verification

        Returns:
            Flashcard entity if found and owned by user, None otherwise
        """
        stmt = select(FlashcardORM).where(
            FlashcardORM.id == flashcard_id.value,
            FlashcardORM.user_id == user_id.value,
        )
        result = await self.db.execute(stmt)
        orm_model = result.scalar_one_or_none()
        return self.mapper.to_domain(orm_model) if orm_model else None

    async def find_by_book(self, book_id: BookId, user_id: UserId) -> list[Flashcard]:
        """
        Get all flashcards for a book.

        Args:
            book_id: The book ID
            user_id: The user ID for ownership verification

        Returns:
            List of flashcard entities ordered by created_at DESC
        """
        stmt = (
            select(FlashcardORM)
            .where(
                FlashcardORM.book_id == book_id.value,
                FlashcardORM.user_id == user_id.value,
            )
            .order_by(FlashcardORM.created_at.desc())
        )
        result = await self.db.execute(stmt)
        orm_models = result.scalars().all()
        return [self.mapper.to_domain(orm) for orm in orm_models]

    async def count_by_book(self, book_id: BookId, user_id: UserId) -> int:
        """
        Count flashcards for a book.

        Args:
            book_id: The book ID
            user_id: The user ID for ownership verification

        Returns:
            Count of flashcards
        """
        stmt = select(func.count(FlashcardORM.id)).where(
            FlashcardORM.book_id == book_id.value,
            FlashcardORM.user_id == user_id.value,
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def save(self, flashcard: Flashcard) -> Flashcard:
        """
        Save a flashcard entity (create or update).

        Args:
            flashcard: The flashcard entity to save

        Returns:
            Saved flashcard entity with database-generated values
        """
        if flashcard.id.value == 0:
            # Create new
            orm_model = self.mapper.to_orm(flashcard)
            self.db.add(orm_model)
            await self.db.commit()
            await self.db.refresh(orm_model)
            return self.mapper.to_domain(orm_model)
        # Update existing
        orm_model = await self.db.get(FlashcardORM, flashcard.id.value)
        if not orm_model:
            raise ValueError(f"Flashcard {flashcard.id.value} not found")
        self.mapper.to_orm(flashcard, orm_model)
        await self.db.commit()
        await self.db.refresh(orm_model)
        return self.mapper.to_domain(orm_model)

    async def delete(self, flashcard_id: FlashcardId, user_id: UserId) -> bool:
        """
        Delete a flashcard.

        Args:
            flashcard_id: The flashcard ID
            user_id: The user ID for ownership verification

        Returns:
            True if deleted, False if not found
        """
        stmt = select(FlashcardORM).where(
            FlashcardORM.id == flashcard_id.value,
            FlashcardORM.user_id == user_id.value,
        )
        result = await self.db.execute(stmt)
        flashcard_orm = result.scalar_one_or_none()

        if not flashcard_orm:
            return False

        await self.db.delete(flashcard_orm)
        await self.db.commit()
        return True
