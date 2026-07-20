"""Mapper for Bookmark ORM ↔ Domain conversion."""

from src.domain.common.value_objects.ids import BookId, BookmarkId, HighlightId
from src.domain.reading.entities.bookmark import Bookmark
from src.infrastructure.common.mappers import orm_id
from src.models import Bookmark as BookmarkORM


class BookmarkMapper:
    """Mapper for Bookmark ORM ↔ Domain conversion."""

    def to_domain(self, orm_model: BookmarkORM) -> Bookmark:
        """Convert ORM model to domain entity."""
        return Bookmark.create_with_id(
            id=BookmarkId(orm_model.id),
            book_id=BookId(orm_model.book_id),
            highlight_id=HighlightId(orm_model.highlight_id),
            created_at=orm_model.created_at,
        )

    def to_orm(self, domain_entity: Bookmark, orm_model: BookmarkORM | None = None) -> BookmarkORM:
        """Convert domain entity to ORM model."""
        # Bookmarks are immutable except cascade deletes — no mutable fields.
        if orm_model is None:
            orm_model = BookmarkORM(
                id=orm_id(domain_entity.id),
                book_id=domain_entity.book_id.value,
                highlight_id=domain_entity.highlight_id.value,
            )
        return orm_model
