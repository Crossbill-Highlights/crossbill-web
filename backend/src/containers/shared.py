from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.reading.services.deduplication_service import HighlightDeduplicationService
from src.domain.reading.services.highlight_grouping_service import HighlightGroupingService
from src.domain.reading.services.highlight_style_resolver import HighlightStyleResolver
from src.infrastructure.ai.ai_service import AIService
from src.infrastructure.ai.repositories.ai_usage_repository import AIUsageRepository
from src.infrastructure.identity.repositories.refresh_token_repository import RefreshTokenRepository
from src.infrastructure.identity.repositories.user_repository import UserRepository
from src.infrastructure.identity.services.password_service_adapter import PasswordServiceAdapter
from src.infrastructure.identity.services.token_service_adapter import TokenServiceAdapter
from src.infrastructure.jobs.repositories.job_batch_repository import JobBatchRepository
from src.infrastructure.learning.repositories.ai_chat_session_repository import (
    AIChatSessionRepository,
)
from src.infrastructure.learning.repositories.flashcard_repository import FlashcardRepository
from src.infrastructure.library.repositories import BookRepository
from src.infrastructure.library.repositories.chapter_repository import ChapterRepository
from src.infrastructure.library.repositories.file_repository import FileRepository
from src.infrastructure.library.repositories.tag_repository import TagRepository
from src.infrastructure.library.services.epub_parser_service import EpubParserService
from src.infrastructure.library.services.epub_position_index_service import (
    EpubPositionIndexService,
)
from src.infrastructure.library.services.epub_text_extraction_service import (
    EpubTextExtractionService,
)
from src.infrastructure.reading.repositories import (
    BookmarkRepository,
    HighlightRepository,
    HighlightStyleRepository,
    HighlightTagRepository,
)
from src.infrastructure.reading.repositories.chapter_prereading_repository import (
    ChapterPrereadingRepository,
)
from src.infrastructure.reading.repositories.reading_session_repository import (
    ReadingSessionRepository,
)
from src.infrastructure.reading.services.highlight_label_resolver import HighlightLabelResolver


class SharedContainer(containers.DeclarativeContainer):
    """Shared repositories, infrastructure services, and domain services."""

    db = providers.Dependency(instance_of=AsyncSession)

    # Repositories
    book_repository = providers.Factory(BookRepository, db=db)
    bookmark_repository = providers.Factory(BookmarkRepository, db=db)
    highlight_repository = providers.Factory(HighlightRepository, db=db)
    highlight_tag_repository = providers.Factory(HighlightTagRepository, db=db)
    chapter_repository = providers.Factory(ChapterRepository, db=db)
    reading_session_repository = providers.Factory(ReadingSessionRepository, db=db)
    tag_repository = providers.Factory(TagRepository, db=db)
    flashcard_repository = providers.Factory(FlashcardRepository, db=db)
    chapter_prereading_repository = providers.Factory(ChapterPrereadingRepository, db=db)
    highlight_style_repository = providers.Factory(HighlightStyleRepository, db=db)
    file_repository = providers.Factory(FileRepository)

    # AI
    ai_usage_repository = providers.Factory(AIUsageRepository, db=db)
    ai_service = providers.Factory(AIService, usage_repository=ai_usage_repository)

    # Infrastructure services (no db dependency)
    epub_parser_service = providers.Factory(EpubParserService)
    epub_position_index_service = providers.Factory(EpubPositionIndexService)
    ebook_text_extraction_service = providers.Factory(EpubTextExtractionService)

    # Identity services
    user_repository = providers.Factory(UserRepository, db=db)
    password_service = providers.Singleton(PasswordServiceAdapter)
    token_service = providers.Singleton(TokenServiceAdapter)
    refresh_token_repository = providers.Factory(RefreshTokenRepository, db=db)

    # Domain services
    highlight_deduplication_service = providers.Factory(HighlightDeduplicationService)
    highlight_grouping_service = providers.Factory(HighlightGroupingService)
    highlight_style_resolver = providers.Factory(HighlightStyleResolver)

    # Infrastructure services (with deps)
    highlight_label_resolver = providers.Factory(
        HighlightLabelResolver,
        highlight_style_repository=highlight_style_repository,
        resolver=highlight_style_resolver,
    )

    # Learning repositories
    ai_chat_session_repository = providers.Factory(AIChatSessionRepository, db=db)

    # Jobs
    job_batch_repository = providers.Factory(JobBatchRepository, db=db)
