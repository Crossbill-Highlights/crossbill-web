"""Service layer for reading session-related business logic."""

import structlog
from sqlalchemy.orm import Session

from src import repositories, schemas
from src.exceptions import BookNotFoundError
from src.repositories.reading_session_repository import ReadingSessionRepository
from src.schemas.reading_session_schemas import ReadingSessionBase
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
        sessions: list[schemas.ReadingSessionUploadItem],
        user_id: int,
    ) -> schemas.ReadingSessionUploadResponse:
        """
        Process reading session upload from KOReader.

        This method:
        1. Groups sessions by book (title+author)
        2. Finds existing books by content hash (skips sessions for unknown books)
        3. Bulk creates sessions with deduplication

        Note: Books are NOT created by this method. Sessions for books that don't
        exist yet are skipped. Books are created via highlight upload.

        Args:
            sessions: list of reading sessions
            user_id: ID of the user

        Returns:
            ReadingSessionUploadResponse with upload statistics
        """
        logger.info(
            "processing_reading_session_upload",
            session_count=len(sessions),
        )

        # Group sessions by book hash
        sessions_by_book: dict[str, list[schemas.ReadingSessionUploadItem]] = {}
        for session in sessions:
            book_hash = compute_book_hash(session.book_title, session.book_author)
            if book_hash not in sessions_by_book:
                sessions_by_book[book_hash] = []
            sessions_by_book[book_hash].append(session)

        book_hashes = [hash for hash, _ in sessions_by_book.items()]
        books = self.book_repo.find_by_content_hashes(book_hashes, user_id)
        books_by_hash = {b.content_hash: b for b in books}

        # Process each book group
        sessions_skipped_no_book = 0

        to_save: list[ReadingSessionBase] = []

        for book_hash, book_sessions in sessions_by_book.items():
            # Skip sessions for books that don't exist yet
            if book_hash not in books_by_hash:
                sessions_skipped_no_book += len(book_sessions)
                first_session = book_sessions[0]
                logger.debug(
                    "skipping_sessions_no_book",
                    book_title=first_session.book_title,
                    book_author=first_session.book_author,
                    session_count=len(book_sessions),
                )
                continue

            book = books_by_hash[book_hash]

            for session in book_sessions:
                # Compute session hash for deduplication
                # Use ISO format string for start_time in hash
                session_hash = compute_reading_session_hash(
                    book_title=session.book_title,
                    book_author=session.book_author,
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

        # Bulk create sessions
        self.session_repo.bulk_create(user_id, to_save)

        self.db.commit()

        logger.info(
            "reading_session_upload_complete",
        )

        return schemas.ReadingSessionUploadResponse(
            success=True,
            message="Uploading reading sessions succeeded",
        )

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
