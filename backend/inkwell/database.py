"""Database configuration and session management."""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from inkwell.config import Settings, get_settings


class Base(DeclarativeBase):
    """Base class for all database models."""



def get_engine(settings: Settings) -> Engine:
    """Create database engine."""
    return create_engine(
        settings.DATABASE_URL,
        connect_args=(
            {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
        ),
    )


def get_session_factory(
    settings: Annotated[Settings, Depends(get_settings)],
) -> sessionmaker[Session]:
    """Get session factory."""
    engine = get_engine(settings)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
