"""Pytest configuration and fixtures."""

import os
from collections.abc import Generator
from datetime import datetime as dt
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base, get_db
from src.main import app
from src.models import (
    Book,
    Flashcard,
    Highlight,
    HighlightTag,
    HighlightTagGroup,
    User,
)
from src.services.auth_service import get_current_user
from src.utils import compute_book_hash, compute_highlight_hash


def create_test_book(
    db_session: Session,
    user_id: int,
    title: str,
    author: str | None = None,
    isbn: str | None = None,
    cover: str | None = None,
    description: str | None = None,
    language: str | None = None,
    page_count: int | None = None,
) -> Book:
    """Create a test book with properly computed content_hash.

    This helper ensures all test books have valid content_hash values.
    """
    content_hash = compute_book_hash(title=title, author=author)
    book = Book(
        user_id=user_id,
        title=title,
        author=author,
        isbn=isbn,
        cover=cover,
        description=description,
        language=language,
        page_count=page_count,
        content_hash=content_hash,
    )
    db_session.add(book)
    db_session.commit()
    db_session.refresh(book)
    return book


def create_test_highlight(
    db_session: Session,
    book: Book,
    user_id: int,
    text: str,
    datetime_str: str,
    page: int | None = None,
    note: str | None = None,
    chapter_id: int | None = None,
    deleted_at: dt | None = None,
) -> Highlight:
    """Create a test highlight with properly computed content_hash.

    This helper ensures all test highlights have valid content_hash values.
    """
    content_hash = compute_highlight_hash(
        text=text,
        book_title=book.title,
        book_author=book.author,
    )
    highlight = Highlight(
        book_id=book.id,
        user_id=user_id,
        chapter_id=chapter_id,
        text=text,
        page=page,
        note=note,
        datetime=datetime_str,
        content_hash=content_hash,
        deleted_at=deleted_at,
    )
    db_session.add(highlight)
    db_session.commit()
    db_session.refresh(highlight)
    return highlight


# Set TESTING environment variable to skip database initialization in main.py
os.environ["TESTING"] = "1"

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
    user = db_session.query(User).filter_by(id=1).first()
    assert user is not None
    return user


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


@pytest.fixture
def test_book(db_session: Session, test_user: User) -> Book:
    """Create a standard test book."""
    return create_test_book(
        db_session=db_session,
        user_id=test_user.id,
        title="Test Book",
        author="Test Author",
    )


@pytest.fixture
def test_highlight(db_session: Session, test_book: Book, test_user: User) -> Highlight:
    """Create a standard test highlight attached to test_book."""
    return create_test_highlight(
        db_session=db_session,
        book=test_book,
        user_id=test_user.id,
        text="Test highlight text",
        page=10,
        datetime_str="2024-01-15 14:30:22",
    )


@pytest.fixture
def test_flashcard(db_session: Session, test_book: Book, test_user: User) -> Flashcard:
    """Create a standard test flashcard attached to test_book."""
    flashcard = Flashcard(
        user_id=test_user.id,
        book_id=test_book.id,
        question="Test question",
        answer="Test answer",
    )
    db_session.add(flashcard)
    db_session.commit()
    db_session.refresh(flashcard)
    return flashcard


@pytest.fixture
def test_tag_group(db_session: Session, test_book: Book) -> HighlightTagGroup:
    """Create a standard test tag group attached to test_book."""
    tag_group = HighlightTagGroup(book_id=test_book.id, name="Test Group")
    db_session.add(tag_group)
    db_session.commit()
    db_session.refresh(tag_group)
    return tag_group


@pytest.fixture
def test_highlight_tag(db_session: Session, test_book: Book, test_user: User) -> HighlightTag:
    """Create a standard test highlight tag attached to test_book."""
    tag = HighlightTag(
        book_id=test_book.id,
        user_id=test_user.id,
        name="Test Tag",
    )
    db_session.add(tag)
    db_session.commit()
    db_session.refresh(tag)
    return tag
