"""ReadingSession repository for database operations."""

import logging
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, selectinload

from src import models
from src.exceptions import ServiceError
from src.schemas.reading_session_schemas import ReadingSessionBase

logger = logging.getLogger(__name__)


@dataclass
class BulkCreateResult:
    """Result of bulk create operation for reading sessions."""

    created_count: int
    created_sessions: list[models.ReadingSession]


class ReadingSessionRepository:
    """Repository for ReadingSession database operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def bulk_create(
        self,
        user_id: int,
        sessions: list[ReadingSessionBase],
    ) -> BulkCreateResult:
        """
        Bulk create reading sessions with deduplication.

        Args:
            user_id: ID of the user
            sessions: List of ReadingSessionBase instances.

        Returns:
            BulkCreateResult with created count and created session objects
        """
        if not sessions:
            return BulkCreateResult(created_count=0, created_sessions=[])

        # Map content_hash -> session data for later retrieval
        session_by_hash = {s.content_hash: s for s in sessions}

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
            result = self.db.execute(stmt)
            created_ids = [row[0] for row in result.fetchall()]

            # Fetch the created sessions
            if created_ids:
                created_sessions = list(
                    self.db.execute(
                        select(models.ReadingSession).where(
                            models.ReadingSession.id.in_(created_ids)
                        )
                    )
                    .scalars()
                    .all()
                )
            else:
                created_sessions = []

            return BulkCreateResult(
                created_count=len(created_ids), created_sessions=created_sessions
            )

        # Sqlite - count before and after to determine how many were inserted
        count_before = (
            self.db.execute(
                select(func.count(models.ReadingSession.id)).where(
                    models.ReadingSession.user_id == user_id
                )
            ).scalar()
            or 0
        )

        stmt = insert(models.ReadingSession).values(values).prefix_with("OR IGNORE")
        self.db.execute(stmt)

        count_after = (
            self.db.execute(
                select(func.count(models.ReadingSession.id)).where(
                    models.ReadingSession.user_id == user_id
                )
            ).scalar()
            or 0
        )

        created_count = count_after - count_before

        # For SQLite, fetch created sessions by content_hash
        if created_count > 0:
            content_hashes = list(session_by_hash.keys())
            created_sessions = list(
                self.db.execute(
                    select(models.ReadingSession).where(
                        models.ReadingSession.user_id == user_id,
                        models.ReadingSession.content_hash.in_(content_hashes),
                    )
                )
                .scalars()
                .all()
            )
            # Filter to only include sessions that were actually created (not pre-existing)
            # We can't be 100% sure which were new, so we return all matching ones
            # The caller will handle deduplication when linking highlights
        else:
            created_sessions = []

        return BulkCreateResult(created_count=created_count, created_sessions=created_sessions)

    def get_by_book_id(
        self, book_id: int, user_id: int, limit: int = 30, offset: int = 0
    ) -> Sequence[models.ReadingSession]:
        """Get reading sessions for a specific book, ordered by start_time descending.

        Eagerly loads highlights with their flashcards and highlight_tags relationships.
        """
        stmt = (
            select(models.ReadingSession)
            .options(
                selectinload(models.ReadingSession.highlights).selectinload(
                    models.Highlight.flashcards
                ),
                selectinload(models.ReadingSession.highlights).selectinload(
                    models.Highlight.highlight_tags
                ),
            )
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

    def get_by_id(self, session_id: int, user_id: int) -> models.ReadingSession | None:
        """Get a reading session by its ID for a specific user.

        Args:
            session_id: ID of the reading session
            user_id: ID of the user (for ownership verification)

        Returns:
            Reading session if found and owned by user, None otherwise
        """
        stmt = select(models.ReadingSession).where(
            models.ReadingSession.id == session_id,
            models.ReadingSession.user_id == user_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def update_ai_summary(
        self, session_id: int, user_id: int, ai_summary: str
    ) -> models.ReadingSession | None:
        """Update the ai_summary field of a reading session.

        Args:
            session_id: ID of the reading session
            user_id: ID of the user (for ownership verification)
            ai_summary: Generated AI summary text

        Returns:
            Updated reading session or None if not found
        """
        session = self.get_by_id(session_id, user_id)
        if session is None:
            return None

        session.ai_summary = ai_summary
        self.db.flush()
        self.db.refresh(session)
        return session
