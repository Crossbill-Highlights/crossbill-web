"""Mapper for Flashcard ORM ↔ Domain conversion."""

from src.domain.common.value_objects import BookId, FlashcardId, HighlightId, UserId
from src.domain.learning.entities.flashcard import Flashcard
from src.models import Flashcard as FlashcardORM


class FlashcardMapper:
    """Mapper for Flashcard ORM ↔ Domain conversion."""

    def to_domain(self, orm_model: FlashcardORM) -> Flashcard:
        """Convert ORM model to domain entity."""
        return Flashcard.create_with_id(
            id=FlashcardId(orm_model.id),
            user_id=UserId(orm_model.user_id),
            book_id=BookId(orm_model.book_id),
            question=orm_model.question,
            answer=orm_model.answer,
            highlight_id=HighlightId(orm_model.highlight_id) if orm_model.highlight_id else None,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at,
        )

    def to_orm(
        self, domain_entity: Flashcard, orm_model: FlashcardORM | None = None
    ) -> FlashcardORM:
        """Convert domain entity to ORM model."""
        if orm_model:
            # Update existing
            orm_model.user_id = domain_entity.user_id.value
            orm_model.book_id = domain_entity.book_id.value
            orm_model.question = domain_entity.question
            orm_model.answer = domain_entity.answer
            orm_model.highlight_id = (
                domain_entity.highlight_id.value if domain_entity.highlight_id else None
            )
            return orm_model

        # Create new
        return FlashcardORM(
            id=domain_entity.id.value if domain_entity.id.value != 0 else None,
            user_id=domain_entity.user_id.value,
            book_id=domain_entity.book_id.value,
            question=domain_entity.question,
            answer=domain_entity.answer,
            highlight_id=domain_entity.highlight_id.value if domain_entity.highlight_id else None,
        )
