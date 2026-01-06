"""ReadingSession repository for database operations."""

import logging
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src import models
from src.exceptions import ServiceError
from src.schemas.reading_session_schemas import ReadingSessionBase

logger = logging.getLogger(__name__)


class ReadingSessionRepository:
    """Repository for ReadingSession database operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def bulk_create(
        self,
        user_id: int,
        sessions: list[ReadingSessionBase],
    ) -> None:
        """
        Bulk create reading sessions with deduplication.

        Args:
            user_id: ID of the user
            sessions: List of ReadingSessionBase instances.

        Returns:
            tuple[int, int]: (created_count, skipped_count)
        """
        values = [
            {
                "book_id": s.book_id,
                "user_id": user_id,
                "content_hash": s.content_hash,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "start_xpoint": s.start_xpoint,
                "end_xpoint": s.end_xpoint,
                "start_page": s.start_page,
                "end_page": s.end_page,
                "device_id": s.device_id,
            }
            for s in sessions
        ]

        if self.db.bind is None:
            raise ServiceError("Database not bound!")

        dialect = self.db.bind.dialect.name

        if dialect == "postgresql":
            stmt = (
                insert(models.ReadingSession)
                .values(values)
                .on_conflict_do_nothing(index_elements=["user_id", "content_hash"])
                .returning(models.ReadingSession.id)
            )

            self.db.execute(stmt)
        elif dialect == "sqlite":
            # Sqlite
            stmt = insert(models.ReadingSession).values(values).prefix_with("OR IGNORE")
            self.db.execute(stmt)

    def get_by_book_id(
        self, book_id: int, user_id: int, limit: int = 100, offset: int = 0
    ) -> Sequence[models.ReadingSession]:
        """Get reading sessions for a specific book, ordered by start_time descending."""
        stmt = (
            select(models.ReadingSession)
            .where(
                models.ReadingSession.book_id == book_id,
                models.ReadingSession.user_id == user_id,
            )
            .order_by(models.ReadingSession.start_time.desc())
            .offset(offset)
            .limit(limit)
        )
        return self.db.execute(stmt).scalars().all()

    def count_by_book_id(self, book_id: int, user_id: int) -> int:
        """Count all reading sessions for a book owned by the user."""
        stmt = select(func.count(models.ReadingSession.id)).where(
            models.ReadingSession.book_id == book_id,
            models.ReadingSession.user_id == user_id,
        )
        return self.db.execute(stmt).scalar() or 0
