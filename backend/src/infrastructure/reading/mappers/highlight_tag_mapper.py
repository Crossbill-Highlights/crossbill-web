"""Mapper for HighlightTag ORM ↔ Domain conversion."""

from src.domain.common.value_objects import BookId, HighlightTagId, UserId
from src.domain.reading.entities.highlight_tag import HighlightTag
from src.models import HighlightTag as HighlightTagORM


class HighlightTagMapper:
    """Mapper for HighlightTag ORM ↔ Domain conversion."""

    def to_domain(self, orm_model: HighlightTagORM) -> HighlightTag:
        """Convert ORM model to domain entity."""
        # Get tag_group_id from ORM
        tag_group_id = orm_model.tag_group_id

        # Get group name from tag_group relationship if it exists and is loaded
        group_name = None
        if hasattr(orm_model, "tag_group") and orm_model.tag_group:
            group_name = orm_model.tag_group.name

        return HighlightTag(
            id=HighlightTagId(orm_model.id),
            user_id=UserId(orm_model.user_id),
            book_id=BookId(orm_model.book_id),
            name=orm_model.name,
            tag_group_id=tag_group_id,
            group_name=group_name,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at,
        )

    def to_orm(
        self, domain_entity: HighlightTag, orm_model: HighlightTagORM | None = None
    ) -> HighlightTagORM:
        """Convert domain entity to ORM model."""
        if orm_model:
            # Update existing
            orm_model.user_id = domain_entity.user_id.value
            orm_model.book_id = domain_entity.book_id.value
            orm_model.name = domain_entity.name
            orm_model.tag_group_id = domain_entity.tag_group_id
            return orm_model

        # Create new
        return HighlightTagORM(
            id=domain_entity.id.value if domain_entity.id.value != 0 else None,
            user_id=domain_entity.user_id.value,
            book_id=domain_entity.book_id.value,
            name=domain_entity.name,
            tag_group_id=domain_entity.tag_group_id,
            created_at=domain_entity.created_at,
            updated_at=domain_entity.updated_at,
        )
