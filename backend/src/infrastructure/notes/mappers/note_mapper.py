"""Mapper for Note ORM ↔ Domain conversion."""

from src.domain.common.value_objects import NoteId, UserId
from src.domain.notes.entities.note import Note, NoteKind
from src.models import Note as NoteORM


class NoteMapper:
    """Mapper for Note ORM ↔ Domain conversion."""

    def to_domain(self, orm_model: NoteORM) -> Note:
        """Convert ORM model to domain entity."""
        return Note.create_with_id(
            id=NoteId(orm_model.id),
            user_id=UserId(orm_model.user_id),
            title=orm_model.title,
            body=orm_model.body,
            kind=NoteKind(orm_model.kind) if orm_model.kind else None,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at,
            book_ids=[book.id for book in orm_model.books],
            chapter_ids=[chapter.id for chapter in orm_model.chapters],
            highlight_ids=[highlight.id for highlight in orm_model.highlights],
            tag_ids=[tag.id for tag in orm_model.tags],
        )

    def to_orm(self, domain_entity: Note, orm_model: NoteORM | None = None) -> NoteORM:
        """Convert domain entity scalar fields to ORM model.

        Association collections are synced separately by the repository,
        which loads the referenced ORM rows.
        """
        if orm_model:
            orm_model.user_id = domain_entity.user_id.value
            orm_model.title = domain_entity.title
            orm_model.body = domain_entity.body
            orm_model.kind = domain_entity.kind.value if domain_entity.kind else None
            return orm_model

        return NoteORM(
            id=domain_entity.id.value if domain_entity.id.value != 0 else None,
            user_id=domain_entity.user_id.value,
            title=domain_entity.title,
            body=domain_entity.body,
            kind=domain_entity.kind.value if domain_entity.kind else None,
        )
