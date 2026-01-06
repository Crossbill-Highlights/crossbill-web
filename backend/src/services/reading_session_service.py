"""Service layer for reading session-related business logic."""

import structlog
from sqlalchemy.orm import Session

from src import repositories, schemas
from src.exceptions import BookNotFoundError
from src.repositories.reading_session_repository import ReadingSessionRepository
from src.schemas.book_schemas import BookCreate
from src.schemas.reading_session_schemas import (
    ReadingSessionBase,
    ReadingSessionUploadSessionItem,
)
from src.services.book_service import BookService
from src.utils import compute_book_hash, compute_reading_session_hash

logger = structlog.get_logger(__name__)


class ReadingSessionService:
    """Service for handling reading session-related operations."""

    def __init__(self, db: Session) -> None:
        """Initialize service with database session."""
        self.db = db
        self.book_repo = repositories.BookRepository(db)
        self.session_repo = ReadingSessionRepository(db)

    def upload_reading_sessions(
        self,
        book_data: BookCreate,
        sessions: list[ReadingSessionUploadSessionItem],
        user_id: int,
    ) -> schemas.ReadingSessionUploadResponse:
        """
        Process reading session upload from KOReader for a single book.

        This method:
        1. Gets or creates the book by content hash (with keywords as tags)
        2. Processes sessions and builds database objects
        3. Bulk creates sessions with deduplication
        4. Returns statistics

        Note: All validation is handled by FastAPI before reaching this method.
        If any session is invalid, the entire request fails with 422.

        Args:
            book_data: Book metadata for all sessions
            sessions: List of validated reading sessions for this book
            user_id: ID of the user

        Returns:
            ReadingSessionUploadResponse with upload statistics
        """
        logger.info(
            "processing_reading_session_upload",
            session_count=len(sessions),
            book_title=book_data.title,
        )

        book_hash = compute_book_hash(book_data.title, book_data.author)
        book = self.book_repo.find_by_content_hash(book_hash, user_id)

        if not book:
            book_service = BookService(self.db)
            book, _ = book_service.create_book(book_data, user_id)

        to_save: list[ReadingSessionBase] = []

        for session in sessions:
            session_hash = compute_reading_session_hash(
                book_title=book_data.title,
                book_author=book_data.author,
                start_time=session.start_time.isoformat(),
                device_id=session.device_id,
            )

            to_save.append(
                ReadingSessionBase(
                    book_id=book.id,
                    content_hash=session_hash,
                    device_id=session.device_id,
                    start_time=session.start_time,
                    end_time=session.end_time,
                    start_xpoint=session.start_xpoint,
                    end_xpoint=session.end_xpoint,
                    start_page=session.start_page,
                    end_page=session.end_page,
                )
            )

        created_count = self.session_repo.bulk_create(user_id, to_save)
        skipped_duplicate_count = len(to_save) - created_count

        self.db.commit()

        logger.info(
            "reading_session_upload_complete",
            created=created_count,
            skipped_duplicate=skipped_duplicate_count,
        )

        return schemas.ReadingSessionUploadResponse(
            success=True,
            message=self._build_upload_message(created_count, skipped_duplicate_count),
            book_id=book.id,
            created_count=created_count,
            skipped_duplicate_count=skipped_duplicate_count,
        )

    def _build_upload_message(
        self,
        created: int,
        skipped_duplicate: int,
    ) -> str:
        """Build a human-readable message summarizing the upload result."""
        parts = []

        if created > 0:
            parts.append(f"Created {created} session{'s' if created != 1 else ''}")

        if skipped_duplicate > 0:
            parts.append(f"{skipped_duplicate} skipped (duplicate)")

        if not parts:
            return "No sessions to process"

        return ". ".join(parts) + "."

    def get_reading_sessions_for_book(
        self,
        book_id: int,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> schemas.ReadingSessionsResponse:
        """Get reading sessions for a specific book."""
        # Validate book exists and belongs to user
        book = self.book_repo.get_by_id(book_id, user_id)
        if not book:
            raise BookNotFoundError(book_id)

        sessions = self.session_repo.get_by_book_id(book_id, user_id, limit, offset)
        total = self.session_repo.count_by_book_id(book_id, user_id)

        return schemas.ReadingSessionsResponse(
            sessions=[schemas.ReadingSession.model_validate(s) for s in sessions],
            total=total,
        )
