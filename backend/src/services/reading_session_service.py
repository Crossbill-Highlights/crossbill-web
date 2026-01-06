"""Service layer for reading session-related business logic."""

from typing import Any

import structlog
from pydantic import ValidationError
from sqlalchemy.orm import Session

from src import repositories, schemas
from src.exceptions import BookNotFoundError
from src.repositories.reading_session_repository import ReadingSessionRepository
from src.schemas.reading_session_schemas import (
    FailedSessionItem,
    ReadingSessionBase,
    ReadingSessionUploadItem,
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
        sessions: list[dict[str, Any]],
        user_id: int,
    ) -> schemas.ReadingSessionUploadResponse:
        """
        Process reading session upload from KOReader with per-item error handling.

        This method:
        1. Validates each session individually
        2. Groups valid sessions by book (title+author)
        3. Gets or creates books by content hash (with keywords as tags)
        4. Bulk creates sessions with deduplication
        5. Returns detailed statistics including failures

        Args:
            sessions: list of raw session dicts (validated per-item)
            user_id: ID of the user

        Returns:
            ReadingSessionUploadResponse with upload statistics and failures
        """
        logger.info(
            "processing_reading_session_upload",
            session_count=len(sessions),
        )

        failed_sessions: list[FailedSessionItem] = []
        validated_sessions: list[tuple[int, ReadingSessionUploadItem]] = []

        # Step 1: Validate each session individually
        for index, raw_session in enumerate(sessions):
            try:
                session = ReadingSessionUploadItem.model_validate(raw_session)
                validated_sessions.append((index, session))
            except ValidationError as e:
                book_data = (
                    raw_session.get("book", {}) if isinstance(raw_session.get("book"), dict) else {}
                )
                failed_sessions.append(
                    FailedSessionItem(
                        index=index,
                        error=self._format_validation_error(e),
                        book_title=book_data.get("title"),
                        book_author=book_data.get("author"),
                    )
                )

        # Step 2: Group validated sessions by book hash and track book data for creation
        sessions_by_book: dict[str, list[tuple[int, ReadingSessionUploadItem]]] = {}
        book_data_by_hash: dict[str, schemas.BookCreate] = {}
        for index, session in validated_sessions:
            book_hash = compute_book_hash(session.book.title, session.book.author)
            if book_hash not in sessions_by_book:
                sessions_by_book[book_hash] = []
                book_data_by_hash[book_hash] = session.book  # Store first occurrence
            sessions_by_book[book_hash].append((index, session))

        # Step 3: Look up existing books
        book_hashes = list(sessions_by_book.keys())
        books = self.book_repo.find_by_content_hashes(book_hashes, user_id)
        books_by_hash = {b.content_hash: b for b in books}

        # Step 4: Process each book group
        to_save: list[ReadingSessionBase] = []
        book_service = BookService(self.db)

        for book_hash, book_sessions in sessions_by_book.items():
            # Get or create book
            if book_hash in books_by_hash:
                book = books_by_hash[book_hash]
            else:
                book_data = book_data_by_hash[book_hash]
                book, _ = book_service.create_book(book_data, user_id)
                books_by_hash[book_hash] = book  # Cache for later

            for index, session in book_sessions:
                try:
                    # Compute session hash for deduplication
                    session_hash = compute_reading_session_hash(
                        book_title=session.book.title,
                        book_author=session.book.author,
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
                except ValidationError as e:
                    failed_sessions.append(
                        FailedSessionItem(
                            index=index,
                            error=self._format_validation_error(e),
                            book_title=session.book.title,
                            book_author=session.book.author,
                        )
                    )

        # Step 5: Bulk create sessions and get actual created count
        created_count = self.session_repo.bulk_create(user_id, to_save)
        skipped_duplicate_count = len(to_save) - created_count

        self.db.commit()

        logger.info(
            "reading_session_upload_complete",
            created=created_count,
            skipped_duplicate=skipped_duplicate_count,
            failed=len(failed_sessions),
        )

        return schemas.ReadingSessionUploadResponse(
            success=len(failed_sessions) == 0,
            message=self._build_upload_message(
                created_count,
                skipped_duplicate_count,
                len(failed_sessions),
            ),
            created_count=created_count,
            skipped_duplicate_count=skipped_duplicate_count,
            failed_count=len(failed_sessions),
            failed_sessions=failed_sessions,
        )

    def _format_validation_error(self, error: ValidationError) -> str:
        """Format a Pydantic validation error into a human-readable string."""
        errors = error.errors()
        if len(errors) == 1:
            err = errors[0]
            loc = ".".join(str(x) for x in err["loc"])
            return f"{loc}: {err['msg']}"
        return "; ".join(f"{'.'.join(str(x) for x in e['loc'])}: {e['msg']}" for e in errors)

    def _build_upload_message(
        self,
        created: int,
        skipped_duplicate: int,
        failed: int,
    ) -> str:
        """Build a human-readable message summarizing the upload result."""
        parts = []

        if created > 0:
            parts.append(f"Created {created} session{'s' if created != 1 else ''}")

        if skipped_duplicate > 0:
            parts.append(f"{skipped_duplicate} skipped (duplicate)")

        if failed > 0:
            parts.append(f"{failed} failed")

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
