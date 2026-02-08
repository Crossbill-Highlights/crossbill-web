"""Use case for generating and retrieving chapter prereading content."""

from datetime import UTC, datetime

import structlog

from src.application.library.protocols.book_repository import (
    BookRepositoryProtocol,
)
from src.application.library.protocols.chapter_repository import (
    ChapterRepositoryProtocol,
)
from src.application.library.protocols.file_repository import (
    FileRepositoryProtocol,
)
from src.application.reading.protocols.ai_prereading_service import (
    AIPrereadingServiceProtocol,
)
from src.application.reading.protocols.chapter_prereading_repository import (
    ChapterPrereadingRepositoryProtocol,
)
from src.application.reading.protocols.ebook_text_extraction_service import (
    EbookTextExtractionServiceProtocol,
)
from src.domain.common.exceptions import DomainError
from src.domain.common.value_objects.ids import BookId, ChapterId, UserId
from src.domain.reading.entities.chapter_prereading_content import (
    ChapterPrereadingContent,
)
from src.exceptions import BookNotFoundError, NotFoundError

logger = structlog.get_logger(__name__)


class ChapterPrereadingUseCase:
    """Use case for managing chapter prereading content."""

    def __init__(
        self,
        prereading_repo: ChapterPrereadingRepositoryProtocol,
        chapter_repo: ChapterRepositoryProtocol,
        text_extraction_service: EbookTextExtractionServiceProtocol,
        book_repo: BookRepositoryProtocol,
        file_repo: FileRepositoryProtocol,
        ai_prereading_service: AIPrereadingServiceProtocol,
    ) -> None:
        self.prereading_repo = prereading_repo
        self.chapter_repo = chapter_repo
        self.text_extraction = text_extraction_service
        self.book_repo = book_repo
        self.file_repo = file_repo
        self.ai_prereading_service = ai_prereading_service

    def get_all_prereading_for_book(
        self, book_id: BookId, user_id: UserId
    ) -> list[ChapterPrereadingContent]:
        """Get all prereading content for chapters in a book."""
        # Verify book ownership by checking chapters exist for this user
        chapters = self.chapter_repo.find_all_by_book(book_id, user_id)
        if not chapters:
            raise NotFoundError(f"Book {book_id.value} not found or has no chapters")

        return self.prereading_repo.find_all_by_book_id(book_id)

    def get_prereading_content(
        self, chapter_id: ChapterId, user_id: UserId
    ) -> ChapterPrereadingContent | None:
        """Get existing prereading content for a chapter."""
        chapter = self.chapter_repo.find_by_id(chapter_id, user_id)
        if not chapter:
            raise NotFoundError(f"Chapter {chapter_id.value} not found")

        return self.prereading_repo.find_by_chapter_id(chapter_id)

    async def generate_prereading_content(
        self, chapter_id: ChapterId, user_id: UserId
    ) -> ChapterPrereadingContent:
        """Generate new prereading content for a chapter."""
        # 1. Verify chapter exists and user owns it
        chapter = self.chapter_repo.find_by_id(chapter_id, user_id)
        if not chapter:
            raise NotFoundError(f"Chapter {chapter_id.value} not found")

        # 2. Check if chapter has XPoint data
        if not chapter.start_xpoint:
            raise DomainError(
                "Chapter does not have position data. "
                "EPUB must be re-uploaded to extract chapter positions."
            )

        # 3. Resolve epub path
        book = self.book_repo.find_by_id(chapter.book_id, user_id)
        if not book or not book.file_path or book.file_type != "epub":
            raise BookNotFoundError(
                chapter.book_id.value, message="EPUB file not found for this book"
            )

        epub_path = self.file_repo.find_epub(book.id)
        if not epub_path or not epub_path.exists():
            raise BookNotFoundError(chapter.book_id.value, message="EPUB file not found on disk")

        # 4. Extract chapter text
        try:
            chapter_text = self.text_extraction.extract_chapter_text(
                epub_path=epub_path,
                start_xpoint=chapter.start_xpoint,
                end_xpoint=chapter.end_xpoint,
            )
        except Exception as e:
            logger.error("failed_to_extract_chapter_text", error=str(e))
            raise DomainError(f"Failed to extract chapter content: {e}") from e

        min_chapter_length = 50
        if not chapter_text or len(chapter_text.strip()) < min_chapter_length:
            raise DomainError(
                "Chapter content is too short to generate meaningful prereading content"
            )

        # 5. Call AI service
        try:
            ai_result = await self.ai_prereading_service.generate_prereading(chapter_text)
        except Exception as e:
            logger.error("ai_service_failed", error=str(e))
            raise DomainError(f"Failed to generate prereading content: {e}") from e

        # 6. Create entity
        entity = ChapterPrereadingContent.create(
            chapter_id=chapter_id,
            summary=ai_result.summary,
            keypoints=ai_result.keypoints,
            generated_at=datetime.now(UTC),
            ai_model="ai-configured-model",
        )

        # 7. Save and return
        logger.info(
            "prereading_content_generated",
            chapter_id=chapter_id.value,
            keypoints_count=len(ai_result.keypoints),
        )
        return self.prereading_repo.save(entity)
