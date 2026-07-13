"""Tests for notes API endpoints."""

from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src import models


class TestCreateNote:
    """Test suite for POST /notes endpoint."""

    async def test_create_note_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_book: models.Book,
        test_chapter: models.Chapter,
        test_user: models.User,
    ) -> None:
        response = await client.post(
            "/api/v1/notes",
            json={
                "title": "Raskolnikov",
                "body": "Main character",
                "kind": "character",
                "book_id": test_book.id,
                "chapter_ids": [test_chapter.id],
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        note = data["note"]
        assert note["title"] == "Raskolnikov"
        assert note["kind"] == "character"
        assert note["book_ids"] == [test_book.id]
        assert note["chapter_ids"] == [test_chapter.id]
        assert note["user_id"] == test_user.id
        result = await db_session.execute(select(models.Note).filter_by(id=note["id"]))
        assert result.scalar_one_or_none() is not None

    async def test_create_note_minimal(self, client: AsyncClient, test_book: models.Book) -> None:
        response = await client.post(
            "/api/v1/notes",
            json={"title": "Stoicism", "book_id": test_book.id},
        )
        assert response.status_code == status.HTTP_201_CREATED
        note = response.json()["note"]
        assert note["body"] == ""
        assert note["kind"] is None
        assert note["chapter_ids"] == []

    async def test_create_note_book_not_found(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/notes", json={"title": "Orphan", "book_id": 99999})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_create_note_empty_title(
        self, client: AsyncClient, test_book: models.Book
    ) -> None:
        response = await client.post("/api/v1/notes", json={"title": "", "book_id": test_book.id})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    async def test_create_note_invalid_kind(
        self, client: AsyncClient, test_book: models.Book
    ) -> None:
        response = await client.post(
            "/api/v1/notes",
            json={"title": "X", "book_id": test_book.id, "kind": "villain"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    async def test_create_note_chapter_not_found(
        self, client: AsyncClient, test_book: models.Book
    ) -> None:
        response = await client.post(
            "/api/v1/notes",
            json={"title": "X", "book_id": test_book.id, "chapter_ids": [99999]},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_create_note_chapter_from_other_book_rejected(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_book: models.Book,
        test_user: models.User,
    ) -> None:
        other_book = models.Book(user_id=test_user.id, title="Other book")
        db_session.add(other_book)
        await db_session.commit()
        await db_session.refresh(other_book)
        other_chapter = models.Chapter(book_id=other_book.id, name="Other chapter")
        db_session.add(other_chapter)
        await db_session.commit()
        await db_session.refresh(other_chapter)

        response = await client.post(
            "/api/v1/notes",
            json={"title": "X", "book_id": test_book.id, "chapter_ids": [other_chapter.id]},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestGetNote:
    """Test suite for GET /notes/{note_id} endpoint."""

    async def test_get_note_with_links(
        self,
        client: AsyncClient,
        test_book: models.Book,
        test_chapter: models.Chapter,
    ) -> None:
        create = await client.post(
            "/api/v1/notes",
            json={
                "title": "Raskolnikov",
                "book_id": test_book.id,
                "chapter_ids": [test_chapter.id],
            },
        )
        note_id = create.json()["note"]["id"]

        response = await client.get(f"/api/v1/notes/{note_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Raskolnikov"
        assert data["chapters"] == [{"id": test_chapter.id, "name": test_chapter.name}]
        assert data["highlights"] == []
        assert data["highlight_tags"] == []

    async def test_get_note_not_found(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/notes/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
