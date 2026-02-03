"""Repository for Bookmark domain entities."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.common.value_objects.ids import BookId, BookmarkId, HighlightId, UserId
from src.domain.reading.entities.bookmark import Bookmark
from src.infrastructure.reading.mappers.bookmark_mapper import BookmarkMapper
from src.models import Book as BookORM
from src.models import Bookmark as BookmarkORM


class BookmarkRepository:
    """Repository for Bookmark domain entities."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.mapper = BookmarkMapper()

    def find_by_id(self, bookmark_id: BookmarkId, user_id: UserId) -> Bookmark | None:
        """
        Find a bookmark by ID with user ownership check.

        Args:
            bookmark_id: The bookmark ID
            user_id: The user ID for ownership verification

        Returns:
            Bookmark entity if found and owned by user, None otherwise
        """
        stmt = (
            select(BookmarkORM)
            .join(BookORM, BookmarkORM.book_id == BookORM.id)
            .where(
                BookmarkORM.id == bookmark_id.value,
                BookORM.user_id == user_id.value,
            )
        )
        orm_model = self.db.execute(stmt).scalar_one_or_none()
        return self.mapper.to_domain(orm_model) if orm_model else None

    def find_by_book_and_highlight(
        self, book_id: BookId, highlight_id: HighlightId
    ) -> Bookmark | None:
        """
        Find a bookmark by book and highlight.

        Args:
            book_id: The book ID
            highlight_id: The highlight ID

        Returns:
            Bookmark entity if found, None otherwise
        """
        stmt = select(BookmarkORM).where(
            BookmarkORM.book_id == book_id.value,
            BookmarkORM.highlight_id == highlight_id.value,
        )
        orm_model = self.db.execute(stmt).scalar_one_or_none()
        return self.mapper.to_domain(orm_model) if orm_model else None

    def find_by_book(self, book_id: BookId, user_id: UserId) -> list[Bookmark]:
        """
        Get all bookmarks for a book.

        Args:
            book_id: The book ID
            user_id: The user ID for ownership verification

        Returns:
            List of bookmark entities ordered by created_at DESC
        """
        stmt = (
            select(BookmarkORM)
            .join(BookORM, BookmarkORM.book_id == BookORM.id)
            .where(
                BookmarkORM.book_id == book_id.value,
                BookORM.user_id == user_id.value,
            )
            .order_by(BookmarkORM.created_at.desc())
        )
        orm_models = self.db.execute(stmt).scalars().all()
        return [self.mapper.to_domain(orm) for orm in orm_models]

    def save(self, bookmark: Bookmark) -> Bookmark:
        """
        Save a bookmark entity.

        Args:
            bookmark: The bookmark entity to save

        Returns:
            Saved bookmark entity with database-generated values
        """
        if bookmark.id.value == 0:
            # Create new
            orm_model = self.mapper.to_orm(bookmark)
            self.db.add(orm_model)
            self.db.commit()
            self.db.refresh(orm_model)
            return self.mapper.to_domain(orm_model)
        # Bookmarks are immutable - no update case
        raise ValueError("Bookmarks cannot be updated")

    def delete(self, bookmark_id: BookmarkId, user_id: UserId) -> bool:
        """
        Delete a bookmark.

        Args:
            bookmark_id: The bookmark ID
            user_id: The user ID for ownership verification

        Returns:
            True if deleted, False if not found
        """
        # Find with ownership check
        stmt = (
            select(BookmarkORM)
            .join(BookORM, BookmarkORM.book_id == BookORM.id)
            .where(
                BookmarkORM.id == bookmark_id.value,
                BookORM.user_id == user_id.value,
            )
        )
        bookmark_orm = self.db.execute(stmt).scalar_one_or_none()

        if not bookmark_orm:
            return False

        self.db.delete(bookmark_orm)
        self.db.commit()
        return True
