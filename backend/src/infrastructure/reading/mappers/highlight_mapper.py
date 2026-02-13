"""
Mapper for converting between Highlight ORM models and domain entities.

Handles bidirectional conversion:
- ORM model → Domain entity (when loading from database)
- Domain entity → ORM model (when persisting to database)
"""

from src.domain.common.value_objects import (
    BookId,
    ChapterId,
    HighlightId,
    UserId,
    XPointRange,
)
from src.domain.common.value_objects.position import Position
from src.domain.reading.entities.highlight import Highlight
from src.models import Highlight as HighlightORM


class HighlightMapper:
    """Mapper for Highlight ORM ↔ Domain conversion."""

    def to_domain(self, orm_model: HighlightORM) -> Highlight:
        """
        Convert ORM model to domain entity.

        Used when loading highlights from database.

        Args:
            orm_model: SQLAlchemy Highlight model

        Returns:
            Highlight domain entity
        """
        # Parse XPointRange if both start and end exist
        xpoints = None
        if orm_model.start_xpoint and orm_model.end_xpoint:
            xpoints = XPointRange.parse(orm_model.start_xpoint, orm_model.end_xpoint)

        position = Position.from_json(orm_model.position) if orm_model.position else None

        # Convert to domain entity using reconstitution factory
        return Highlight.create_with_id(
            id=HighlightId(orm_model.id),
            user_id=UserId(orm_model.user_id),
            book_id=BookId(orm_model.book_id),
            text=orm_model.text,
            datetime_str=orm_model.datetime,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at,
            chapter_id=ChapterId(orm_model.chapter_id) if orm_model.chapter_id else None,
            xpoints=xpoints,
            page=orm_model.page,
            position=position,
            note=orm_model.note,
            deleted_at=orm_model.deleted_at,
        )

    def to_orm(
        self, domain_entity: Highlight, orm_model: HighlightORM | None = None
    ) -> HighlightORM:
        """
        Convert domain entity to ORM model.

        Used when persisting highlights to database.

        Args:
            domain_entity: Highlight domain entity
            orm_model: Optional existing ORM model to update (for updates)

        Returns:
            SQLAlchemy Highlight model
        """
        # Extract xpoint strings if present
        start_xpoint = None
        end_xpoint = None
        if domain_entity.xpoints:
            start_xpoint = domain_entity.xpoints.start.to_string()
            end_xpoint = domain_entity.xpoints.end.to_string()

        # Use datetime string from entity (already formatted)
        datetime_str = domain_entity.datetime

        # Update existing ORM model or create new one
        if orm_model:
            # Update existing model
            orm_model.user_id = domain_entity.user_id.value
            orm_model.book_id = domain_entity.book_id.value
            orm_model.chapter_id = (
                domain_entity.chapter_id.value if domain_entity.chapter_id else None
            )
            orm_model.text = domain_entity.text
            orm_model.content_hash = domain_entity.content_hash.value
            orm_model.page = domain_entity.page
            orm_model.note = domain_entity.note
            orm_model.start_xpoint = start_xpoint
            orm_model.end_xpoint = end_xpoint
            orm_model.position = (
                domain_entity.position.to_json() if domain_entity.position else None
            )
            orm_model.deleted_at = domain_entity.deleted_at
            return orm_model
        # Create new model
        return HighlightORM(
            id=domain_entity.id.value if domain_entity.id.value != 0 else None,
            user_id=domain_entity.user_id.value,
            book_id=domain_entity.book_id.value,
            chapter_id=domain_entity.chapter_id.value if domain_entity.chapter_id else None,
            text=domain_entity.text,
            content_hash=domain_entity.content_hash.value,
            page=domain_entity.page,
            position=domain_entity.position.to_json() if domain_entity.position else None,
            note=domain_entity.note,
            start_xpoint=start_xpoint,
            end_xpoint=end_xpoint,
            datetime=datetime_str,
            created_at=domain_entity.created_at,
            deleted_at=domain_entity.deleted_at,
        )
