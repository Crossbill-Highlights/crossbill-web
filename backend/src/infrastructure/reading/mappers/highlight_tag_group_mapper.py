"""Mapper for HighlightTagGroup ORM ↔ Domain conversion."""

from src.domain.common.value_objects.ids import BookId, HighlightTagGroupId
from src.domain.reading.entities.highlight_tag_group import HighlightTagGroup
from src.models import HighlightTagGroup as HighlightTagGroupORM


class HighlightTagGroupMapper:
    """Mapper for HighlightTagGroup ORM ↔ Domain conversion."""

    def to_domain(self, orm_model: HighlightTagGroupORM) -> HighlightTagGroup:
        """Convert ORM model to domain entity."""
        return HighlightTagGroup.create_with_id(
            id=HighlightTagGroupId(orm_model.id),
            book_id=BookId(orm_model.book_id),
            name=orm_model.name,
        )

    def to_orm(
        self,
        entity: HighlightTagGroup,
        orm_model: HighlightTagGroupORM | None = None,
    ) -> HighlightTagGroupORM:
        """Convert domain entity to ORM model."""
        if orm_model:
            # Update existing
            orm_model.name = entity.name
            return orm_model

        # Create new
        return HighlightTagGroupORM(
            id=entity.id.value if entity.id.value != 0 else None,
            book_id=entity.book_id.value,
            name=entity.name,
        )
