"""Tests for quiz session endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models import Book, Chapter
from src.models import QuizSession as QuizSessionModel


def create_quiz_chapter(db_session: Session, book: Book) -> Chapter:
    """Create a chapter with xpoint data needed for content extraction."""
    chapter = Chapter(
        book_id=book.id,
        name="Quiz Test Chapter",
        start_xpoint="/body/text/chapter[1]",
        end_xpoint="/body/text/chapter[2]",
    )
    db_session.add(chapter)
    db_session.commit()
    db_session.refresh(chapter)
    return chapter


class TestCreateQuizSession:
    @patch("src.feature_flags.is_ai_enabled", return_value=True)
    @patch("src.infrastructure.ai.ai_service.AIService.start_quiz", new_callable=AsyncMock)
    @patch(
        "src.infrastructure.library.services.epub_text_extraction_service"
        ".EpubTextExtractionService.extract_chapter_text"
    )
    @patch("src.infrastructure.library.repositories.file_repository.FileRepository.find_epub")
    def test_create_quiz_session_success(
        self,
        mock_find_epub: MagicMock,
        mock_extract: MagicMock,
        mock_start_quiz: AsyncMock,
        mock_ai_enabled: MagicMock,
        client: TestClient,
        db_session: Session,
        test_book: Book,
    ) -> None:
        test_book.file_path = "/path/to/test.epub"
        test_book.file_type = "epub"
        db_session.commit()

        chapter = create_quiz_chapter(db_session, test_book)

        mock_epub_path = MagicMock()
        mock_epub_path.exists.return_value = True
        mock_find_epub.return_value = mock_epub_path
        mock_extract.return_value = "Chapter content here"

        mock_start_quiz.return_value = (
            "**Question 1/5:** What is the main topic?",
            [{"some": "history"}],
        )

        response = client.post(f"/api/v1/chapters/{chapter.id}/quiz-sessions")
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert "message" in data
        assert "Question 1/5" in data["message"]

    @patch("src.feature_flags.is_ai_enabled", return_value=True)
    def test_create_quiz_session_chapter_not_found(
        self, mock_ai_enabled: MagicMock, client: TestClient
    ) -> None:
        response = client.post("/api/v1/chapters/99999/quiz-sessions")
        assert response.status_code == 404


class TestSendQuizMessage:
    @patch("src.feature_flags.is_ai_enabled", return_value=True)
    def test_send_message_session_not_found(
        self, mock_ai_enabled: MagicMock, client: TestClient
    ) -> None:
        response = client.post(
            "/api/v1/quiz-sessions/99999/messages",
            json={"message": "My answer"},
        )
        assert response.status_code == 404

    @patch("src.feature_flags.is_ai_enabled", return_value=True)
    def test_send_empty_message_rejected(
        self, mock_ai_enabled: MagicMock, client: TestClient
    ) -> None:
        response = client.post(
            "/api/v1/quiz-sessions/1/messages",
            json={"message": ""},
        )
        assert response.status_code == 422

    @patch("src.feature_flags.is_ai_enabled", return_value=True)
    @patch(
        "src.infrastructure.ai.ai_service.AIService.continue_quiz",
        new_callable=AsyncMock,
    )
    def test_send_message_success(
        self,
        mock_continue_quiz: AsyncMock,
        mock_ai_enabled: MagicMock,
        client: TestClient,
        db_session: Session,
        test_book: Book,
    ) -> None:
        chapter = create_quiz_chapter(db_session, test_book)

        quiz_session = QuizSessionModel(
            user_id=1,
            chapter_id=chapter.id,
            message_history=[{"some": "history"}],
        )
        db_session.add(quiz_session)
        db_session.commit()
        db_session.refresh(quiz_session)

        mock_continue_quiz.return_value = (
            "Good answer! **Question 2/5:** What happened next?",
            [{"updated": "history"}],
        )

        response = client.post(
            f"/api/v1/quiz-sessions/{quiz_session.id}/messages",
            json={"message": "The main topic is testing"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Question 2/5" in data["message"]
