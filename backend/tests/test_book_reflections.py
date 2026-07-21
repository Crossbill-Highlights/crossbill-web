"""Tests for book reflection API endpoints."""

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src import models
from tests.conftest import create_test_book

DEFAULT_USER_ID = 1

EMPTY_PAYLOAD: dict[str, object] = {
    "what_is_it_about_note_id": None,
    "what_does_it_say_note_id": None,
    "do_i_agree_note_id": None,
    "so_what_note_id": None,
    "note_ids": [],
}


async def _create_note(
    client: AsyncClient, book_id: int, title: str, kind: str = "reflection"
) -> int:
    response = await client.post(
        "/api/v1/notes",
        json={"title": title, "kind": kind, "book_id": book_id},
    )
    return response.json()["note"]["id"]


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
            "what_is_it_about_note_id": None,
            "what_does_it_say_note_id": None,
            "do_i_agree_note_id": None,
            "so_what_note_id": None,
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
        note_id = await _create_note(client, test_book.id, "What it is about")
        response = await client.put(
            f"/api/v1/books/{test_book.id}/reflection",
            json={**EMPTY_PAYLOAD, "what_is_it_about_note_id": note_id},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["what_is_it_about_note_id"] == note_id

        result = await db_session.execute(
            select(models.BookReflection).filter_by(book_id=test_book.id)
        )
        rows = result.scalars().all()
        assert len(rows) == 1

    async def test_answer_note_round_trips(
        self, client: AsyncClient, test_book: models.Book
    ) -> None:
        note_id = await _create_note(client, test_book.id, "Do I agree")
        await client.put(
            f"/api/v1/books/{test_book.id}/reflection",
            json={**EMPTY_PAYLOAD, "do_i_agree_note_id": note_id},
        )
        fetched = await client.get(f"/api/v1/books/{test_book.id}/reflection")
        assert fetched.json()["do_i_agree_note_id"] == note_id

    async def test_second_put_updates_same_row(
        self, client: AsyncClient, db_session: AsyncSession, test_book: models.Book
    ) -> None:
        first = await _create_note(client, test_book.id, "First")
        second = await _create_note(client, test_book.id, "Second")
        await client.put(
            f"/api/v1/books/{test_book.id}/reflection",
            json={**EMPTY_PAYLOAD, "what_is_it_about_note_id": first},
        )
        response = await client.put(
            f"/api/v1/books/{test_book.id}/reflection",
            json={**EMPTY_PAYLOAD, "what_is_it_about_note_id": second},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["what_is_it_about_note_id"] == second

        result = await db_session.execute(
            select(models.BookReflection).filter_by(book_id=test_book.id)
        )
        assert len(result.scalars().all()) == 1

    async def test_deleting_answer_note_unanswers_question(
        self, client: AsyncClient, test_book: models.Book
    ) -> None:
        note_id = await _create_note(client, test_book.id, "So what")
        await client.put(
            f"/api/v1/books/{test_book.id}/reflection",
            json={**EMPTY_PAYLOAD, "so_what_note_id": note_id},
        )

        deleted = await client.delete(f"/api/v1/notes/{note_id}")
        assert deleted.status_code == status.HTTP_200_OK

        fetched = await client.get(f"/api/v1/books/{test_book.id}/reflection")
        assert fetched.json()["so_what_note_id"] is None

    async def test_note_linking_round_trips(
        self, client: AsyncClient, test_book: models.Book
    ) -> None:
        note_id = await _create_note(client, test_book.id, "Proposition", kind="concept")

        response = await client.put(
            f"/api/v1/books/{test_book.id}/reflection",
            json={**EMPTY_PAYLOAD, "note_ids": [note_id]},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["note_ids"] == [note_id]

        fetched = await client.get(f"/api/v1/books/{test_book.id}/reflection")
        assert fetched.json()["note_ids"] == [note_id]

    async def test_unlinking_notes_persists(
        self, client: AsyncClient, test_book: models.Book
    ) -> None:
        note_id = await _create_note(client, test_book.id, "Term", kind="term")
        await client.put(
            f"/api/v1/books/{test_book.id}/reflection",
            json={**EMPTY_PAYLOAD, "note_ids": [note_id]},
        )
        response = await client.put(
            f"/api/v1/books/{test_book.id}/reflection",
            json={**EMPTY_PAYLOAD, "note_ids": []},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["note_ids"] == []

    async def test_linking_note_from_other_book_rejected(
        self, client: AsyncClient, db_session: AsyncSession, test_book: models.Book
    ) -> None:
        other_book = await create_test_book(
            db_session=db_session, user_id=DEFAULT_USER_ID, title="Other Book"
        )
        other_note_id = await _create_note(client, other_book.id, "Elsewhere")

        response = await client.put(
            f"/api/v1/books/{test_book.id}/reflection",
            json={**EMPTY_PAYLOAD, "note_ids": [other_note_id]},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_answer_note_from_other_book_rejected(
        self, client: AsyncClient, db_session: AsyncSession, test_book: models.Book
    ) -> None:
        other_book = await create_test_book(
            db_session=db_session, user_id=DEFAULT_USER_ID, title="Other Book"
        )
        other_note_id = await _create_note(client, other_book.id, "Elsewhere")

        response = await client.put(
            f"/api/v1/books/{test_book.id}/reflection",
            json={**EMPTY_PAYLOAD, "what_is_it_about_note_id": other_note_id},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_reflection_is_per_book(
        self, client: AsyncClient, db_session: AsyncSession, test_book: models.Book
    ) -> None:
        second_book = await create_test_book(
            db_session=db_session, user_id=DEFAULT_USER_ID, title="Second Book"
        )
        note_id = await _create_note(client, test_book.id, "Book one")
        await client.put(
            f"/api/v1/books/{test_book.id}/reflection",
            json={**EMPTY_PAYLOAD, "what_is_it_about_note_id": note_id},
        )
        response = await client.get(f"/api/v1/books/{second_book.id}/reflection")
        assert response.json()["what_is_it_about_note_id"] is None

    async def test_upsert_book_not_found(self, client: AsyncClient) -> None:
        response = await client.put(
            "/api/v1/books/99999/reflection",
            json=EMPTY_PAYLOAD,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
