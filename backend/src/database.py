"""Database configuration and session management."""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.config import Settings, get_settings


class Base(DeclarativeBase):
    """Base class for all database models."""


# Module-level singletons (application-scoped)
_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def initialize_database(settings: Settings) -> None:
    """Initialize database engine and session factory once at startup."""
    global _engine, _session_factory  # noqa: PLW0603

    # Connection pool configuration
    if settings.DATABASE_URL.startswith("sqlite"):
        _engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        _engine = create_engine(
            settings.DATABASE_URL,
            pool_size=20,  # Base pool size
            max_overflow=30,  # Allow 10 extra connections under load
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=3600,  # Recycle connections after 1 hour
        )

    _session_factory = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def get_engine() -> Engine:
    """Get the singleton database engine."""
    if _engine is None:
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
    return _engine


def get_session_factory(
    settings: Annotated[Settings, Depends(get_settings)],
) -> sessionmaker[Session]:
    """Get session factory (returns singleton)."""
    if _session_factory is None:
        # Fallback for backwards compatibility
        initialize_database(settings)

    if _session_factory is None:
        raise RuntimeError("Failed to initialize database session factory.")

    return _session_factory


def dispose_engine() -> None:
    """Dispose database engine on shutdown."""
    global _engine, _session_factory  # noqa: PLW0603
    if _engine is not None:
        _engine.dispose()
        _engine = None
        _session_factory = None


def get_db(
    session_factory: Annotated[sessionmaker[Session], Depends(get_session_factory)],
) -> Generator[Session, None, None]:
    """Get database session."""
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


# Type alias for database dependency
DatabaseSession = Annotated[Session, Depends(get_db)]
