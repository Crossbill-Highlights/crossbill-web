from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.common.value_objects.ids import BookId, UserId
from src.domain.library.entities.book import Book
from src.infrastructure.library.mappers.book_mapper import BookMapper
from src.models import Book as BookORM


class BookRepository:
    """Domain-centric repository for Book persistence."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.mapper = BookMapper()

    def find_by_client_book_id(self, client_book_id: str, user_id: UserId) -> Book | None:
        """
        Find book by client-provided book ID.

        Used during highlight upload to check if book already exists.
        """
        stmt = (
            select(BookORM)
            .where(BookORM.client_book_id == client_book_id)
            .where(BookORM.user_id == user_id.value)
        )
        orm_model = self.db.execute(stmt).scalar_one_or_none()

        if not orm_model:
            return None

        return self.mapper.to_domain(orm_model)

    def find_by_id(self, book_id: BookId, user_id: UserId) -> Book | None:
        """Find book by ID with user ownership check."""
        stmt = (
            select(BookORM)
            .where(BookORM.id == book_id.value)
            .where(BookORM.user_id == user_id.value)
        )
        orm_model = self.db.execute(stmt).scalar_one_or_none()

        if not orm_model:
            return None

        return self.mapper.to_domain(orm_model)

    def save(self, book: Book) -> Book:
        """Persist book to database."""
        if book.id.value == 0:
            # Create new
            orm_model = self.mapper.to_orm(book)
            self.db.add(orm_model)
            self.db.flush()
            return self.mapper.to_domain(orm_model)
        # Update existing
        stmt = select(BookORM).where(BookORM.id == book.id.value)
        existing_orm = self.db.execute(stmt).scalar_one()
        self.mapper.to_orm(book, existing_orm)
        self.db.flush()
        return self.mapper.to_domain(existing_orm)
