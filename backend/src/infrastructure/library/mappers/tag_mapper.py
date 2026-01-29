"""Mapper for Tag ORM ↔ Domain conversion."""

from src.domain.common.value_objects.ids import TagId, UserId
from src.domain.library.entities.tag import Tag
from src.models import Tag as TagORM


class TagMapper:
    """Mapper for Tag ORM ↔ Domain conversion."""

    def to_domain(self, orm_model: TagORM) -> Tag:
        """Convert ORM model to domain entity."""
        return Tag.create_with_id(
            id=TagId(orm_model.id),
            user_id=UserId(orm_model.user_id),
            name=orm_model.name,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at,
        )

    def to_orm(self, domain_entity: Tag, orm_model: TagORM | None = None) -> TagORM:
        """Convert domain entity to ORM model."""
        if orm_model:
            # Update existing
            orm_model.user_id = domain_entity.user_id.value
            orm_model.name = domain_entity.name
            return orm_model

        # Create new
        return TagORM(
            id=domain_entity.id.value if domain_entity.id.value != 0 else None,
            user_id=domain_entity.user_id.value,
            name=domain_entity.name,
            created_at=domain_entity.created_at,
            updated_at=domain_entity.updated_at,
        )
