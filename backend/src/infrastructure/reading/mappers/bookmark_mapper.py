"""Mapper for Bookmark ORM ↔ Domain conversion."""

from src.domain.common.value_objects.ids import BookId, BookmarkId, HighlightId
from src.domain.reading.entities.bookmark import Bookmark
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
        if orm_model:
            # Update existing (bookmarks are immutable except cascade deletes)
            # No fields to update for bookmarks
            return orm_model

        # Create new
        return BookmarkORM(
            id=domain_entity.id.value if domain_entity.id.value != 0 else None,
            book_id=domain_entity.book_id.value,
            highlight_id=domain_entity.highlight_id.value,
        )
