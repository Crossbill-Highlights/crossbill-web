"""Integration tests for batch job endpoints."""

from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import container
from src.models import BatchJob, Book, Chapter, User
from tests.conftest import create_test_book


@pytest.fixture(autouse=True)
def mock_batch_queue() -> Generator[MagicMock, None, None]:
    """Override container.batch_queue with a mock SAQ Queue for all tests in this module."""
    mock_queue = MagicMock()
    mock_queue.enqueue = AsyncMock()
    with container.batch_queue.override(mock_queue):
        yield mock_queue


async def create_test_chapters(db_session: AsyncSession, book: Book, count: int) -> list[Chapter]:
    """Create multiple test chapters for a book."""
    chapters = []
    for i in range(count):
        chapter = Chapter(
            book_id=book.id,
            name=f"Chapter {i + 1}",
        )
        db_session.add(chapter)
        chapters.append(chapter)
    await db_session.commit()
    for chapter in chapters:
        await db_session.refresh(chapter)
    return chapters


async def create_test_batch_job(
    db_session: AsyncSession,
    user_id: int,
    book_id: int,
    status: str = "pending",
    job_type: str = "prereading",
    total_items: int = 3,
    completed_items: int = 0,
    failed_items: int = 0,
) -> BatchJob:
    """Insert a BatchJob ORM model directly into the database."""
    job = BatchJob(
        user_id=user_id,
        book_id=book_id,
        job_type=job_type,
        status=status,
        total_items=total_items,
        completed_items=completed_items,
        failed_items=failed_items,
        created_at=datetime.now(UTC),
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    return job


class TestCreateBatchPrereading:
    @patch("src.infrastructure.common.dependencies.is_ai_enabled", return_value=True)
    async def test_creates_batch_job(
        self,
        mock_ai_enabled: MagicMock,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        mock_batch_queue: MagicMock,
    ) -> None:
        """Creating prereading for a book with 3 chapters returns 201 with correct fields."""
        book = await create_test_book(db_session, test_user.id, "Test Book for Prereading")
        await create_test_chapters(db_session, book, 3)

        response = await client.post(f"/api/v1/books/{book.id}/batch/prereading")

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"
        assert data["total_items"] == 3
        assert "job_id" in data
        mock_batch_queue.enqueue.assert_called_once()

    @patch("src.infrastructure.common.dependencies.is_ai_enabled", return_value=True)
    async def test_409_when_active_job_exists(
        self,
        mock_ai_enabled: MagicMock,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ) -> None:
        """Returns 409 when a processing job already exists for the book."""
        book = await create_test_book(db_session, test_user.id, "Book With Active Job")
        await create_test_chapters(db_session, book, 2)

        # Insert an existing active (processing) job
        await create_test_batch_job(
            db_session,
            user_id=test_user.id,
            book_id=book.id,
            status="processing",
        )

        response = await client.post(f"/api/v1/books/{book.id}/batch/prereading")

        assert response.status_code == 409


class TestGetBatchJobStatus:
    @patch("src.infrastructure.common.dependencies.is_ai_enabled", return_value=True)
    async def test_returns_job_status(
        self,
        mock_ai_enabled: MagicMock,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ) -> None:
        """GET batch-jobs/{job_id} returns 200 with correct fields."""
        book = await create_test_book(db_session, test_user.id, "Book for Status Check")

        job = await create_test_batch_job(
            db_session,
            user_id=test_user.id,
            book_id=book.id,
            status="processing",
            total_items=5,
            completed_items=2,
            failed_items=1,
        )

        response = await client.get(f"/api/v1/batch-jobs/{job.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job.id
        assert data["status"] == "processing"
        assert data["total_items"] == 5
        assert data["completed_items"] == 2
        assert data["failed_items"] == 1
        assert data["job_type"] == "prereading"
        assert "created_at" in data

    @patch("src.infrastructure.common.dependencies.is_ai_enabled", return_value=True)
    async def test_404_for_other_users_job(
        self,
        mock_ai_enabled: MagicMock,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Returns 404 when fetching a batch job belonging to another user."""
        # Create another user and a book owned by that user
        other_user = User(id=2, email="other@test.com")
        db_session.add(other_user)
        await db_session.commit()

        book = await create_test_book(db_session, 2, "Other User's Book")

        job = await create_test_batch_job(
            db_session,
            user_id=2,
            book_id=book.id,
            status="pending",
        )

        # Request as user 1 (mocked auth)
        response = await client.get(f"/api/v1/batch-jobs/{job.id}")

        assert response.status_code == 404


class TestCancelBatchJob:
    @patch("src.infrastructure.common.dependencies.is_ai_enabled", return_value=True)
    async def test_cancels_active_job(
        self,
        mock_ai_enabled: MagicMock,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ) -> None:
        """POST cancel on a processing job returns 200 with status=cancelled."""
        book = await create_test_book(db_session, test_user.id, "Book to Cancel")

        job = await create_test_batch_job(
            db_session,
            user_id=test_user.id,
            book_id=book.id,
            status="processing",
        )

        response = await client.post(f"/api/v1/batch-jobs/{job.id}/cancel")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"
        assert data["job_id"] == job.id

    @patch("src.infrastructure.common.dependencies.is_ai_enabled", return_value=True)
    async def test_409_for_completed_job(
        self,
        mock_ai_enabled: MagicMock,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ) -> None:
        """POST cancel on a completed job returns 409."""
        book = await create_test_book(db_session, test_user.id, "Completed Book")

        job = await create_test_batch_job(
            db_session,
            user_id=test_user.id,
            book_id=book.id,
            status="completed",
        )

        response = await client.post(f"/api/v1/batch-jobs/{job.id}/cancel")

        assert response.status_code == 409
