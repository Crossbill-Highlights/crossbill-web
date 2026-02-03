from dependency_injector import containers, providers
from sqlalchemy.orm import Session

from src.application.reading.services.bookmark_service import BookmarkService
from src.infrastructure.library.repositories import BookRepository
from src.infrastructure.reading.repositories import BookmarkRepository, HighlightRepository


class Container(containers.DeclarativeContainer):
    """Dependency injection container."""

    # Declare db as a dependency that will be provided at runtime
    db = providers.Dependency(instance_of=Session)

    # Repositories
    book_repository = providers.Factory(BookRepository, db=db)
    bookmark_repository = providers.Factory(BookmarkRepository, db=db)
    highlight_repository = providers.Factory(HighlightRepository, db=db)

    # Application services
    bookmark_service = providers.Factory(
        BookmarkService,
        book_repository=book_repository,
        bookmark_repository=bookmark_repository,
        highlight_repository=highlight_repository,
    )


# Initialize container
container = Container()
