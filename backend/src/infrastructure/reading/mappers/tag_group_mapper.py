"""Mapper for TagGroup ORM ↔ Domain conversion."""

from src.domain.common.value_objects.ids import BookId, TagGroupId
from src.domain.reading.entities.tag_group import TagGroup
from src.models import TagGroup as TagGroupORM


class TagGroupMapper:
    """Mapper for TagGroup ORM ↔ Domain conversion."""

    def to_domain(self, orm_model: TagGroupORM) -> TagGroup:
        """Convert ORM model to domain entity."""
        return TagGroup.create_with_id(
            id=TagGroupId(orm_model.id),
            book_id=BookId(orm_model.book_id),
            name=orm_model.name,
        )

    def to_orm(
        self,
        entity: TagGroup,
        orm_model: TagGroupORM | None = None,
    ) -> TagGroupORM:
        """Convert domain entity to ORM model."""
        if orm_model:
            # Update existing
            orm_model.name = entity.name
            return orm_model

        # Create new
        return TagGroupORM(
            id=entity.id.value if entity.id.value != 0 else None,
            book_id=entity.book_id.value,
            name=entity.name,
        )
