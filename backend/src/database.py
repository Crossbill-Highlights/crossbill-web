"""Database configuration and session management."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool

from src.config import Settings, get_settings


class Base(DeclarativeBase):
    """Base class for all database models."""


# Module-level singletons (application-scoped)
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _make_async_url(url: str) -> str:
    """Convert a database URL to its async-compatible dialect."""
    if url.startswith("sqlite://"):
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    # Already async-compatible or custom dialect
    return url


def initialize_database(settings: Settings) -> None:
    """Initialize database engine and session factory once at startup."""
    global _engine, _session_factory  # noqa: PLW0603

    async_url = _make_async_url(settings.DATABASE_URL)

    # Connection pool configuration
    if async_url.startswith("sqlite"):
        _engine = create_async_engine(
            async_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        _engine = create_async_engine(
            async_url,
            pool_size=20,  # Base pool size
            max_overflow=30,  # Allow 10 extra connections under load
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=3600,  # Recycle connections after 1 hour
        )

    _session_factory = async_sessionmaker(
        autocommit=False, autoflush=False, expire_on_commit=False, bind=_engine
    )


def get_engine() -> AsyncEngine:
    """Get the singleton database engine."""
    if _engine is None:
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
    return _engine


def get_session_factory(
    settings: Annotated[Settings, Depends(get_settings)],
) -> async_sessionmaker[AsyncSession]:
    """Get session factory (returns singleton)."""
    if _session_factory is None:
        # Fallback for backwards compatibility
        initialize_database(settings)

    if _session_factory is None:
        raise RuntimeError("Failed to initialize database session factory.")

    return _session_factory


async def dispose_engine() -> None:
    """Dispose database engine on shutdown."""
    global _engine, _session_factory  # noqa: PLW0603
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None


async def get_db(
    session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with session_factory() as db:
        yield db


# Type alias for database dependency
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]
