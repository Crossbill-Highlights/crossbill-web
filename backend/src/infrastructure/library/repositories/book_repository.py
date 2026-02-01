from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.domain.common.value_objects.ids import BookId, UserId
from src.domain.library.entities.book import Book
from src.domain.library.entities.tag import Tag
from src.infrastructure.library.mappers.book_mapper import BookMapper
from src.infrastructure.library.mappers.tag_mapper import TagMapper
from src.models import Book as BookORM
from src.models import Flashcard as FlashcardORM
from src.models import Highlight as HighlightORM


class BookRepository:
    """Domain-centric repository for Book persistence."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.mapper = BookMapper()
        self.tag_mapper = TagMapper()

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

    def delete(self, book: Book) -> None:
        """
        Hard delete a book from the database.

        Cascading deletes handled by database foreign key constraints.
        """
        stmt = select(BookORM).where(BookORM.id == book.id.value)
        book_orm = self.db.execute(stmt).scalar_one()
        self.db.delete(book_orm)
        self.db.flush()

    def get_recently_viewed_books(
        self, user_id: UserId, limit: int = 10
    ) -> list[tuple[Book, int, int, list[Tag]]]:
        """
        Get recently viewed books with their highlight and flashcard counts.

        Only returns books that have been viewed (last_viewed is not NULL).

        Args:
            user_id: User ID for filtering books
            limit: Maximum number of books to return (default: 10)

        Returns:
            List of tuples containing (Book entity, highlight_count, flashcard_count, list[Tag])
            ordered by last_viewed DESC.
        """
        # Subquery for highlight counts (excluding soft-deleted highlights)
        highlight_count_subq = (
            select(func.count(HighlightORM.id))
            .where(
                HighlightORM.book_id == BookORM.id,
                HighlightORM.deleted_at.is_(None),
            )
            .correlate(BookORM)
            .scalar_subquery()
            .label("highlight_count")
        )

        # Subquery for flashcard counts
        flashcard_count_subq = (
            select(func.count(FlashcardORM.id))
            .where(FlashcardORM.book_id == BookORM.id)
            .correlate(BookORM)
            .scalar_subquery()
            .label("flashcard_count")
        )

        stmt = (
            select(BookORM, highlight_count_subq, flashcard_count_subq)
            .where(
                BookORM.user_id == user_id.value,
                BookORM.last_viewed.isnot(None),
            )
            .order_by(BookORM.last_viewed.desc())
            .limit(limit)
        )

        results = self.db.execute(stmt).all()

        # Convert ORM models to domain entities with counts and tags
        return [
            (
                self.mapper.to_domain(book_orm),
                highlight_count,
                flashcard_count,
                [self.tag_mapper.to_domain(tag_orm) for tag_orm in book_orm.tags],
            )
            for book_orm, highlight_count, flashcard_count in results
        ]

    def get_books_with_counts(
        self,
        user_id: UserId,
        offset: int = 0,
        limit: int = 100,
        include_only_with_flashcards: bool = False,
        search_text: str | None = None,
    ) -> tuple[list[tuple[Book, int, int, list[Tag]]], int]:
        """
        Get books with their highlight and flashcard counts for a specific user.

        Books are sorted alphabetically by title.

        Args:
            user_id: ID of the user whose books to retrieve
            offset: Number of books to skip (default: 0)
            limit: Maximum number of books to return (default: 100)
            include_only_with_flashcards: Include only books which have flashcards
            search_text: Optional text to search for in book title or author (case-insensitive)

        Returns:
            tuple[list[tuple[Book, highlight_count, flashcard_count, list[Tag]]], total_count]:
                (list of (book, highlight_count, flashcard_count, tags) tuples, total count)
        """
        # Build base filter conditions - always filter by user
        filters = [BookORM.user_id == user_id.value]
        if search_text:
            search_pattern = f"%{search_text}%"
            filters.append(
                (BookORM.title.ilike(search_pattern)) | (BookORM.author.ilike(search_pattern))
            )

        if include_only_with_flashcards:
            # Use EXISTS to efficiently check if book has any flashcards
            flashcard_exists = select(1).where(FlashcardORM.book_id == BookORM.id).exists()
            filters.append(flashcard_exists)

        # Count query for total number of books
        total_stmt = select(func.count(BookORM.id)).where(*filters)
        total = self.db.execute(total_stmt).scalar() or 0

        # Subquery for highlight counts (excluding soft-deleted highlights)
        highlight_count_subq = (
            select(func.count(HighlightORM.id))
            .where(
                HighlightORM.book_id == BookORM.id,
                HighlightORM.deleted_at.is_(None),
            )
            .correlate(BookORM)
            .scalar_subquery()
            .label("highlight_count")
        )

        # Subquery for flashcard counts
        flashcard_count_subq = (
            select(func.count(FlashcardORM.id))
            .where(FlashcardORM.book_id == BookORM.id)
            .correlate(BookORM)
            .scalar_subquery()
            .label("flashcard_count")
        )

        # Main query for books with both counts
        stmt = (
            select(BookORM, highlight_count_subq, flashcard_count_subq)
            .where(*filters)
            .order_by(BookORM.title)
            .offset(offset)
            .limit(limit)
        )

        results = self.db.execute(stmt).all()

        # Convert ORM models to domain entities with counts and tags
        return (
            [
                (
                    self.mapper.to_domain(book_orm),
                    highlight_count,
                    flashcard_count,
                    [self.tag_mapper.to_domain(tag_orm) for tag_orm in book_orm.tags],
                )
                for book_orm, highlight_count, flashcard_count in results
            ],
            total,
        )
