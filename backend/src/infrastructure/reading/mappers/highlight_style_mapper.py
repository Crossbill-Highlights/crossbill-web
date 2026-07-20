"""Mapper for converting between HighlightStyle ORM models and domain entities."""

from src.domain.common.value_objects import BookId, HighlightStyleId, UserId
from src.domain.reading.entities.highlight_style import HighlightStyle
from src.infrastructure.common.mappers import orm_id
from src.infrastructure.reading.orm.highlight_style_model import HighlightStyle as HighlightStyleORM


class HighlightStyleMapper:
    """Mapper for HighlightStyle ORM <-> Domain conversion."""

    def to_domain(self, orm_model: HighlightStyleORM) -> HighlightStyle:
        """Convert ORM model to domain entity."""
        return HighlightStyle.create_with_id(
            id=HighlightStyleId(orm_model.id),
            user_id=UserId(orm_model.user_id),
            book_id=BookId(orm_model.book_id) if orm_model.book_id else None,
            device_color=orm_model.device_color,
            device_style=orm_model.device_style,
            label=orm_model.label,
            ui_color=orm_model.ui_color,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at,
        )

    def to_orm(
        self,
        domain_entity: HighlightStyle,
        orm_model: HighlightStyleORM | None = None,
    ) -> HighlightStyleORM:
        """Convert domain entity to ORM model."""
        if orm_model is None:
            orm_model = HighlightStyleORM(
                id=orm_id(domain_entity.id),
                user_id=domain_entity.user_id.value,
                book_id=domain_entity.book_id.value if domain_entity.book_id else None,
                device_color=domain_entity.device_color,
                device_style=domain_entity.device_style,
                created_at=domain_entity.created_at,
            )
        else:
            orm_model.updated_at = domain_entity.updated_at
        orm_model.label = domain_entity.label
        orm_model.ui_color = domain_entity.ui_color
        return orm_model
