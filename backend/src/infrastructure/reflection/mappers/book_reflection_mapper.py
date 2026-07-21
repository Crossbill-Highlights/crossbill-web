"""Mapper for BookReflection ORM ↔ Domain conversion."""

from src.domain.common.value_objects import BookId, BookReflectionId, UserId
from src.domain.reflection.entities.book_reflection import BookReflection
from src.infrastructure.common.mappers import orm_id
from src.infrastructure.reflection.orm.book_reflection_model import (
    BookReflection as BookReflectionORM,
)


class BookReflectionMapper:
    """Mapper for BookReflection ORM ↔ Domain conversion."""

    def to_domain(self, orm_model: BookReflectionORM) -> BookReflection:
        """Convert ORM model to domain entity."""
        return BookReflection.create_with_id(
            id=BookReflectionId(orm_model.id),
            user_id=UserId(orm_model.user_id),
            book_id=BookId(orm_model.book_id),
            what_is_it_about=orm_model.what_is_it_about,
            what_does_it_say=orm_model.what_does_it_say,
            do_i_agree=orm_model.do_i_agree,
            so_what=orm_model.so_what,
            note_ids=[note.id for note in orm_model.notes],
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at,
        )

    def to_orm(
        self,
        domain_entity: BookReflection,
        orm_model: BookReflectionORM | None = None,
    ) -> BookReflectionORM:
        """Convert domain entity scalar fields to ORM model.

        The notes association collection is synced separately by the repository,
        which loads the referenced ORM rows.
        """
        if orm_model is None:
            orm_model = BookReflectionORM(id=orm_id(domain_entity.id))
        orm_model.user_id = domain_entity.user_id.value
        orm_model.book_id = domain_entity.book_id.value
        orm_model.what_is_it_about = domain_entity.what_is_it_about
        orm_model.what_does_it_say = domain_entity.what_does_it_say
        orm_model.do_i_agree = domain_entity.do_i_agree
        orm_model.so_what = domain_entity.so_what
        return orm_model
