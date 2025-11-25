"""Pytest configuration and fixtures."""

from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base, get_db
from src.main import app
from src.models import (  # noqa: F401 - Import to register models
    Book,
    Chapter,
    Highlight,
    HighlightTag,
    HighlightTagGroup,
    User,
)
from src.services.auth_service import get_current_user

# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine with StaticPool to reuse the same connection
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    session = TestSessionLocal()
    try:
        # Create the default user that services expect
        default_user = User(id=1, email="admin@test.com")
        session.add(default_user)
        session.commit()
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Get the default test user."""
    return db_session.query(User).filter_by(id=1).first()


@pytest.fixture
def client(db_session: Session, test_user: User) -> Generator[TestClient, Any, None]:
    """Create a test client with database session and mocked authentication."""

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    async def override_get_current_user() -> User:
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
