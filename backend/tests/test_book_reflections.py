"""Tests for book reflection API endpoints."""

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src import models
from tests.conftest import create_test_book

DEFAULT_USER_ID = 1


class TestGetBookReflection:
    """Test suite for GET /books/{book_id}/reflection endpoint."""

    async def test_get_returns_empty_default_when_none(
        self, client: AsyncClient, test_book: models.Book
    ) -> None:
        response = await client.get(f"/api/v1/books/{test_book.id}/reflection")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == {
            "book_id": test_book.id,
            "what_is_it_about": "",
            "what_does_it_say": "",
            "do_i_agree": "",
            "so_what": "",
            "note_ids": [],
        }

    async def test_get_book_not_found(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/books/99999/reflection")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpsertBookReflection:
    """Test suite for PUT /books/{book_id}/reflection endpoint."""

    async def test_put_creates_reflection(
        self, client: AsyncClient, db_session: AsyncSession, test_book: models.Book
    ) -> None:
        response = await client.put(
            f"/api/v1/books/{test_book.id}/reflection",
            json={
                "what_is_it_about": "A method for demanding reading.",
                "what_does_it_say": "Four questions.",
                "do_i_agree": "Yes.",
                "so_what": "I will read more actively.",
                "note_ids": [],
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["what_is_it_about"] == "A method for demanding reading."
        assert data["so_what"] == "I will read more actively."

        result = await db_session.execute(
            select(models.BookReflection).filter_by(book_id=test_book.id)
        )
        rows = result.scalars().all()
        assert len(rows) == 1

    async def test_second_put_updates_same_row(
        self, client: AsyncClient, db_session: AsyncSession, test_book: models.Book
    ) -> None:
        await client.put(
            f"/api/v1/books/{test_book.id}/reflection",
            json={
                "what_is_it_about": "First draft.",
                "what_does_it_say": "",
                "do_i_agree": "",
                "so_what": "",
                "note_ids": [],
            },
        )
        response = await client.put(
            f"/api/v1/books/{test_book.id}/reflection",
            json={
                "what_is_it_about": "Revised.",
                "what_does_it_say": "",
                "do_i_agree": "",
                "so_what": "",
                "note_ids": [],
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["what_is_it_about"] == "Revised."

        result = await db_session.execute(
            select(models.BookReflection).filter_by(book_id=test_book.id)
        )
        assert len(result.scalars().all()) == 1

    async def test_note_linking_round_trips(
        self, client: AsyncClient, test_book: models.Book
    ) -> None:
        note = await client.post(
            "/api/v1/notes",
            json={"title": "Proposition", "kind": "concept", "book_id": test_book.id},
        )
        note_id = note.json()["note"]["id"]

        response = await client.put(
            f"/api/v1/books/{test_book.id}/reflection",
            json={
                "what_is_it_about": "",
                "what_does_it_say": "See linked notes.",
                "do_i_agree": "",
                "so_what": "",
                "note_ids": [note_id],
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["note_ids"] == [note_id]

        fetched = await client.get(f"/api/v1/books/{test_book.id}/reflection")
        assert fetched.json()["note_ids"] == [note_id]

    async def test_unlinking_notes_persists(
        self, client: AsyncClient, test_book: models.Book
    ) -> None:
        note = await client.post(
            "/api/v1/notes",
            json={"title": "Term", "kind": "term", "book_id": test_book.id},
        )
        note_id = note.json()["note"]["id"]
        await client.put(
            f"/api/v1/books/{test_book.id}/reflection",
            json={
                "what_is_it_about": "",
                "what_does_it_say": "",
                "do_i_agree": "",
                "so_what": "",
                "note_ids": [note_id],
            },
        )
        response = await client.put(
            f"/api/v1/books/{test_book.id}/reflection",
            json={
                "what_is_it_about": "",
                "what_does_it_say": "",
                "do_i_agree": "",
                "so_what": "",
                "note_ids": [],
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["note_ids"] == []

    async def test_linking_note_from_other_book_rejected(
        self, client: AsyncClient, db_session: AsyncSession, test_book: models.Book
    ) -> None:
        other_book = await create_test_book(
            db_session=db_session, user_id=DEFAULT_USER_ID, title="Other Book"
        )
        other_note = await client.post(
            "/api/v1/notes",
            json={"title": "Elsewhere", "book_id": other_book.id},
        )
        other_note_id = other_note.json()["note"]["id"]

        response = await client.put(
            f"/api/v1/books/{test_book.id}/reflection",
            json={
                "what_is_it_about": "",
                "what_does_it_say": "",
                "do_i_agree": "",
                "so_what": "",
                "note_ids": [other_note_id],
            },
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_reflection_is_per_book(
        self, client: AsyncClient, db_session: AsyncSession, test_book: models.Book
    ) -> None:
        second_book = await create_test_book(
            db_session=db_session, user_id=DEFAULT_USER_ID, title="Second Book"
        )
        await client.put(
            f"/api/v1/books/{test_book.id}/reflection",
            json={
                "what_is_it_about": "Book one.",
                "what_does_it_say": "",
                "do_i_agree": "",
                "so_what": "",
                "note_ids": [],
            },
        )
        response = await client.get(f"/api/v1/books/{second_book.id}/reflection")
        assert response.json()["what_is_it_about"] == ""

    async def test_upsert_book_not_found(self, client: AsyncClient) -> None:
        response = await client.put(
            "/api/v1/books/99999/reflection",
            json={
                "what_is_it_about": "",
                "what_does_it_say": "",
                "do_i_agree": "",
                "so_what": "",
                "note_ids": [],
            },
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
