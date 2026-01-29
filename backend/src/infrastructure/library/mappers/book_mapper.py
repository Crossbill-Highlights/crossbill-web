from src.domain.common.value_objects.ids import BookId, UserId
from src.domain.library.entities.book import Book
from src.models import Book as BookORM


class BookMapper:
    """Mapper for Book ORM ↔ Domain conversion."""

    def to_domain(self, orm_model: BookORM) -> Book:
        """Convert ORM model to domain entity."""
        return Book.create_with_id(
            id=BookId(orm_model.id),
            user_id=UserId(orm_model.user_id),
            title=orm_model.title,
            created_at=orm_model.created_at,
            client_book_id=orm_model.client_book_id,
            author=orm_model.author,
            isbn=orm_model.isbn,
            description=orm_model.description,
            language=orm_model.language,
            page_count=orm_model.page_count,
            cover=orm_model.cover,
            file_path=orm_model.file_path,
            file_type=orm_model.file_type,
            last_viewed=orm_model.last_viewed,
        )

    def to_orm(self, domain_entity: Book, orm_model: BookORM | None = None) -> BookORM:
        """Convert domain entity to ORM model."""
        if orm_model:
            # Update existing
            orm_model.user_id = domain_entity.user_id.value
            orm_model.title = domain_entity.title
            orm_model.client_book_id = domain_entity.client_book_id
            orm_model.author = domain_entity.author
            orm_model.isbn = domain_entity.isbn
            orm_model.description = domain_entity.description
            orm_model.language = domain_entity.language
            orm_model.page_count = domain_entity.page_count
            orm_model.cover = domain_entity.cover
            orm_model.file_path = domain_entity.file_path
            orm_model.file_type = domain_entity.file_type
            orm_model.last_viewed = domain_entity.last_viewed
            return orm_model

        # Create new
        return BookORM(
            id=domain_entity.id.value if domain_entity.id.value != 0 else None,
            user_id=domain_entity.user_id.value,
            title=domain_entity.title,
            client_book_id=domain_entity.client_book_id,
            author=domain_entity.author,
            isbn=domain_entity.isbn,
            description=domain_entity.description,
            language=domain_entity.language,
            page_count=domain_entity.page_count,
            cover=domain_entity.cover,
            file_path=domain_entity.file_path,
            file_type=domain_entity.file_type,
            created_at=domain_entity.created_at,
            last_viewed=domain_entity.last_viewed,
        )
