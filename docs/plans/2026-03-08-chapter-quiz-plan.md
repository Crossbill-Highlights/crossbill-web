# Chapter Quiz Feature Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a conversational quiz feature where users can test their recall of chapter contents through an AI-powered Q&A chat interface.

**Architecture:** Extends the existing DDD/hexagonal architecture with a new QuizSession entity, repository, and two use cases (start/continue). Uses pydantic-ai's `message_history` and `ModelMessagesTypeAdapter` for stateful conversations. Frontend adds a chat modal triggered from the ChapterDetailDialog.

**Tech Stack:** pydantic-ai (message_history, ModelMessagesTypeAdapter), FastAPI, SQLAlchemy, React, MUI, TanStack Query, Orval

**Design doc:** `docs/plans/2026-03-08-chapter-quiz-design.md`

---

### Task 1: Database Migration — quiz_sessions table

**Files:**
- Create: `backend/alembic/versions/045_add_quiz_sessions.py`

**Step 1: Create the migration file**

```python
"""Add quiz_sessions table.

Revision ID: 045
Revises: 044
"""

from alembic import op
import sqlalchemy as sa

revision = "045"
down_revision = "044"


def upgrade() -> None:
    op.create_table(
        "quiz_sessions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "chapter_id",
            sa.Integer(),
            sa.ForeignKey("chapters.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("message_history", sa.JSON(), nullable=False),
        sa.Column("question_count", sa.Integer(), nullable=False, server_default="5"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("quiz_sessions")
```

**Step 2: Run the migration**

Run: `cd backend && uv run alembic upgrade head`
Expected: Migration applies successfully.

**Step 3: Commit**

```bash
git add backend/alembic/versions/045_add_quiz_sessions.py
git commit -m "Add quiz_sessions database migration"
```

---

### Task 2: ORM Model — QuizSessionModel

**Files:**
- Modify: `backend/src/models.py` (append after AIUsageRecord class, ~line 643)

**Step 1: Add the ORM model**

Add to `backend/src/models.py` after the `AIUsageRecord` class:

```python
class QuizSession(Base):
    """ORM model for quiz sessions."""

    __tablename__ = "quiz_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chapter_id: Mapped[int] = mapped_column(
        ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    message_history: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    question_count: Mapped[int] = mapped_column(nullable=False, server_default="5")
    created_at: Mapped[dt] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[dt | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship()
    chapter: Mapped["Chapter"] = relationship()

    def __repr__(self) -> str:
        return f"<QuizSession(id={self.id}, chapter_id={self.chapter_id})>"
```

Also add `Any` to the typing imports at the top of models.py — add `from typing import Any` if not already present.

**Step 2: Run type check**

Run: `cd backend && uv run pyright src/models.py`
Expected: No errors.

**Step 3: Commit**

```bash
git add backend/src/models.py
git commit -m "Add QuizSession ORM model"
```

---

### Task 3: Domain Entity — QuizSession

**Files:**
- Create: `backend/src/domain/learning/entities/quiz_session.py`
- Modify: `backend/src/domain/common/value_objects/ids.py` (add QuizSessionId)

**Step 1: Add QuizSessionId to ids.py**

Add after `AIUsageRecordId` in `backend/src/domain/common/value_objects/ids.py`:

```python
@dataclass(frozen=True)
class QuizSessionId(EntityId):
    """Strongly-typed quiz session identifier."""

    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("QuizSessionId must be non-negative")

    @classmethod
    def generate(cls) -> "QuizSessionId":
        return cls(0)  # Database assigns real ID
```

**Step 2: Create the domain entity**

Create `backend/src/domain/learning/entities/quiz_session.py`:

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.domain.common.entity import Entity
from src.domain.common.value_objects.ids import ChapterId, QuizSessionId, UserId


@dataclass
class QuizSession(Entity[QuizSessionId]):
    """A quiz conversation session for a chapter."""

    id: QuizSessionId
    user_id: UserId
    chapter_id: ChapterId
    message_history: list[dict[str, Any]]
    question_count: int
    created_at: datetime
    completed_at: datetime | None

    @classmethod
    def create(
        cls,
        user_id: UserId,
        chapter_id: ChapterId,
        question_count: int,
        created_at: datetime,
    ) -> "QuizSession":
        return cls(
            id=QuizSessionId.generate(),
            user_id=user_id,
            chapter_id=chapter_id,
            message_history=[],
            question_count=question_count,
            created_at=created_at,
            completed_at=None,
        )

    @classmethod
    def create_with_id(
        cls,
        id: QuizSessionId,
        user_id: UserId,
        chapter_id: ChapterId,
        message_history: list[dict[str, Any]],
        question_count: int,
        created_at: datetime,
        completed_at: datetime | None,
    ) -> "QuizSession":
        return cls(
            id=id,
            user_id=user_id,
            chapter_id=chapter_id,
            message_history=message_history,
            question_count=question_count,
            created_at=created_at,
            completed_at=completed_at,
        )
```

**Step 3: Run type check**

Run: `cd backend && uv run pyright src/domain/learning/entities/quiz_session.py src/domain/common/value_objects/ids.py`
Expected: No errors.

**Step 4: Commit**

```bash
git add backend/src/domain/common/value_objects/ids.py backend/src/domain/learning/entities/quiz_session.py
git commit -m "Add QuizSession domain entity and QuizSessionId"
```

---

### Task 4: Quiz Session Repository — Protocol & Implementation

**Files:**
- Create: `backend/src/application/learning/protocols/quiz_session_repository.py`
- Create: `backend/src/infrastructure/learning/mappers/quiz_session_mapper.py`
- Create: `backend/src/infrastructure/learning/repositories/quiz_session_repository.py`

**Step 1: Create the repository protocol**

Create `backend/src/application/learning/protocols/quiz_session_repository.py`:

```python
from datetime import datetime
from typing import Any, Protocol

from src.domain.common.value_objects.ids import QuizSessionId, UserId
from src.domain.learning.entities.quiz_session import QuizSession


class QuizSessionRepositoryProtocol(Protocol):
    def create(self, session: QuizSession) -> QuizSession: ...

    def find_by_id(self, session_id: QuizSessionId, user_id: UserId) -> QuizSession | None: ...

    def update_message_history(
        self,
        session_id: QuizSessionId,
        message_history: list[dict[str, Any]],
        completed_at: datetime | None,
    ) -> None: ...
```

**Step 2: Create the mapper**

Create `backend/src/infrastructure/learning/mappers/quiz_session_mapper.py`:

```python
from src.domain.common.value_objects.ids import ChapterId, QuizSessionId, UserId
from src.domain.learning.entities.quiz_session import QuizSession
from src.models import QuizSession as QuizSessionModel


class QuizSessionMapper:
    @staticmethod
    def to_domain(model: QuizSessionModel) -> QuizSession:
        return QuizSession.create_with_id(
            id=QuizSessionId(model.id),
            user_id=UserId(model.user_id),
            chapter_id=ChapterId(model.chapter_id),
            message_history=model.message_history,
            question_count=model.question_count,
            created_at=model.created_at,
            completed_at=model.completed_at,
        )

    @staticmethod
    def to_orm(entity: QuizSession) -> QuizSessionModel:
        model = QuizSessionModel(
            user_id=entity.user_id.value,
            chapter_id=entity.chapter_id.value,
            message_history=entity.message_history,
            question_count=entity.question_count,
            created_at=entity.created_at,
            completed_at=entity.completed_at,
        )
        if entity.id.value != 0:
            model.id = entity.id.value
        return model
```

**Step 3: Create the repository**

Create `backend/src/infrastructure/learning/repositories/quiz_session_repository.py`:

```python
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.common.value_objects.ids import QuizSessionId, UserId
from src.domain.learning.entities.quiz_session import QuizSession
from src.infrastructure.learning.mappers.quiz_session_mapper import QuizSessionMapper
from src.models import QuizSession as QuizSessionModel


class QuizSessionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.mapper = QuizSessionMapper()

    def create(self, session: QuizSession) -> QuizSession:
        orm_model = self.mapper.to_orm(session)
        self.db.add(orm_model)
        self.db.commit()
        self.db.refresh(orm_model)
        return self.mapper.to_domain(orm_model)

    def find_by_id(self, session_id: QuizSessionId, user_id: UserId) -> QuizSession | None:
        result = self.db.execute(
            select(QuizSessionModel).where(
                QuizSessionModel.id == session_id.value,
                QuizSessionModel.user_id == user_id.value,
            )
        ).scalar_one_or_none()
        if result is None:
            return None
        return self.mapper.to_domain(result)

    def update_message_history(
        self,
        session_id: QuizSessionId,
        message_history: list[dict[str, Any]],
        completed_at: datetime | None,
    ) -> None:
        result = self.db.execute(
            select(QuizSessionModel).where(QuizSessionModel.id == session_id.value)
        ).scalar_one_or_none()
        if result is None:
            return
        result.message_history = message_history
        result.completed_at = completed_at
        self.db.commit()
```

**Step 4: Run type check**

Run: `cd backend && uv run pyright src/application/learning/protocols/quiz_session_repository.py src/infrastructure/learning/mappers/quiz_session_mapper.py src/infrastructure/learning/repositories/quiz_session_repository.py`
Expected: No errors.

**Step 5: Commit**

```bash
git add backend/src/application/learning/protocols/quiz_session_repository.py backend/src/infrastructure/learning/mappers/quiz_session_mapper.py backend/src/infrastructure/learning/repositories/quiz_session_repository.py
git commit -m "Add QuizSession repository protocol and implementation"
```

---

### Task 5: AI Agent & Service — Quiz Methods

**Files:**
- Modify: `backend/src/infrastructure/ai/ai_agents.py` (add `get_quiz_agent`)
- Modify: `backend/src/infrastructure/ai/ai_service.py` (add `start_quiz`, `continue_quiz`)
- Create: `backend/src/application/learning/protocols/ai_quiz_service.py`

**Step 1: Create the protocol**

Create `backend/src/application/learning/protocols/ai_quiz_service.py`:

```python
from typing import Any, Protocol

from src.application.ai.ai_usage_context import AIUsageContext


class AIQuizServiceProtocol(Protocol):
    async def start_quiz(
        self, chapter_content: str, question_count: int, usage_context: AIUsageContext
    ) -> tuple[str, list[dict[str, Any]]]: ...

    async def continue_quiz(
        self, user_message: str, message_history: list[dict[str, Any]], usage_context: AIUsageContext
    ) -> tuple[str, list[dict[str, Any]]]: ...
```

**Step 2: Add the quiz agent**

Add to `backend/src/infrastructure/ai/ai_agents.py` after `get_flashcard_agent`:

```python
QUIZ_INSTRUCTIONS = """
You are a reading comprehension tutor. Your goal is to help the reader recall and
solidify their understanding of a book chapter they have previously read.

BEHAVIOR:
- You will receive the chapter text as your first message. Read it carefully.
- Ask one question at a time about the chapter content.
- After the reader answers, evaluate their response:
  - If correct: briefly acknowledge and move to the next question.
  - If partially correct: acknowledge what they got right, gently correct what they missed,
    and reference the relevant part of the chapter.
  - If incorrect: explain the correct answer with context from the chapter, without being
    condescending.
- If the reader asks for clarification or a follow-up question, answer helpfully.
  These do NOT count toward the question total.
- After asking all questions, provide a brief summary:
  - What the reader remembered well
  - Areas that might benefit from re-reading
  - End with an encouraging note.

QUESTION STYLE:
- Mix question types: factual recall, conceptual understanding, connections between ideas.
- Start with broader questions and progress to more specific ones.
- Frame questions naturally, not as a formal exam.
- Questions should test understanding, not trivial details.

FORMAT:
- Keep responses concise and conversational.
- Use markdown formatting when helpful (bold for emphasis, lists for summaries).
- When you ask question N of the total, prefix it with **Question N/{total}:** so the
  reader knows their progress.
"""


def get_quiz_agent() -> Agent[None, str]:
    return Agent(
        get_ai_model(),
        output_type=str,
        instructions=QUIZ_INSTRUCTIONS,
    )
```

**Step 3: Add quiz methods to AIService**

Add these imports to the top of `backend/src/infrastructure/ai/ai_service.py`:

```python
from typing import Any

from pydantic_ai import ModelMessagesTypeAdapter
from pydantic_core import to_jsonable_python
```

Add the import for the new agent in the existing import block:

```python
from src.infrastructure.ai.ai_agents import (
    get_flashcard_agent,
    get_prereading_agent,
    get_quiz_agent,
    get_summary_agent,
)
```

Add these methods to the `AIService` class:

```python
    async def start_quiz(
        self, chapter_content: str, question_count: int, usage_context: AIUsageContext
    ) -> tuple[str, list[dict[str, Any]]]:
        agent = get_quiz_agent()
        prompt = f"The reader wants to be quizzed on this chapter. Ask {question_count} questions total.\n\n--- CHAPTER CONTENT ---\n{chapter_content}"
        result = await agent.run(prompt)
        usage = result.usage()
        self._save_usage(
            usage_context, result.response.model_name, usage.input_tokens, usage.output_tokens
        )
        serialized = to_jsonable_python(result.all_messages())
        return result.output, serialized

    async def continue_quiz(
        self, user_message: str, message_history: list[dict[str, Any]], usage_context: AIUsageContext
    ) -> tuple[str, list[dict[str, Any]]]:
        agent = get_quiz_agent()
        restored = ModelMessagesTypeAdapter.validate_python(message_history)
        result = await agent.run(user_message, message_history=restored)
        usage = result.usage()
        self._save_usage(
            usage_context, result.response.model_name, usage.input_tokens, usage.output_tokens
        )
        serialized = to_jsonable_python(result.all_messages())
        return result.output, serialized
```

**Step 4: Run type check**

Run: `cd backend && uv run pyright src/infrastructure/ai/ai_agents.py src/infrastructure/ai/ai_service.py src/application/learning/protocols/ai_quiz_service.py`
Expected: No errors.

**Step 5: Commit**

```bash
git add backend/src/infrastructure/ai/ai_agents.py backend/src/infrastructure/ai/ai_service.py backend/src/application/learning/protocols/ai_quiz_service.py
git commit -m "Add quiz AI agent and service methods"
```

---

### Task 6: Use Cases — StartQuizSession & SendQuizMessage

**Files:**
- Create: `backend/src/application/learning/use_cases/quiz/start_quiz_session_use_case.py`
- Create: `backend/src/application/learning/use_cases/quiz/send_quiz_message_use_case.py`
- Create: `backend/src/application/learning/use_cases/quiz/__init__.py`

**Step 1: Create the __init__.py**

Create empty `backend/src/application/learning/use_cases/quiz/__init__.py`.

**Step 2: Create StartQuizSessionUseCase**

Create `backend/src/application/learning/use_cases/quiz/start_quiz_session_use_case.py`:

```python
from datetime import UTC, datetime

import structlog

from src.application.ai.ai_usage_context import AIUsageContext
from src.application.learning.protocols.ai_quiz_service import AIQuizServiceProtocol
from src.application.learning.protocols.quiz_session_repository import (
    QuizSessionRepositoryProtocol,
)
from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.library.protocols.chapter_repository import ChapterRepositoryProtocol
from src.application.library.protocols.file_repository import FileRepositoryProtocol
from src.application.reading.protocols.ebook_text_extraction_service import (
    EbookTextExtractionServiceProtocol,
)
from src.domain.common.exceptions import DomainError
from src.domain.common.value_objects.ids import ChapterId, UserId
from src.domain.learning.entities.quiz_session import QuizSession
from src.exceptions import BookNotFoundError, NotFoundError

logger = structlog.get_logger(__name__)

QUIZ_DEFAULT_QUESTION_COUNT = 5


class StartQuizSessionUseCase:
    def __init__(
        self,
        quiz_session_repository: QuizSessionRepositoryProtocol,
        chapter_repo: ChapterRepositoryProtocol,
        book_repo: BookRepositoryProtocol,
        file_repo: FileRepositoryProtocol,
        text_extraction_service: EbookTextExtractionServiceProtocol,
        ai_quiz_service: AIQuizServiceProtocol,
    ) -> None:
        self.quiz_session_repo = quiz_session_repository
        self.chapter_repo = chapter_repo
        self.book_repo = book_repo
        self.file_repo = file_repo
        self.text_extraction = text_extraction_service
        self.ai_quiz_service = ai_quiz_service

    async def start(self, chapter_id: int, user_id: int) -> tuple[int, str]:
        """Start a new quiz session for a chapter.

        Returns:
            Tuple of (session_id, first_question)
        """
        chapter_id_vo = ChapterId(chapter_id)
        user_id_vo = UserId(user_id)

        # 1. Verify chapter exists and user owns it
        chapter = self.chapter_repo.find_by_id(chapter_id_vo, user_id_vo)
        if not chapter:
            raise NotFoundError(f"Chapter {chapter_id} not found")

        # 2. Extract chapter content
        if not chapter.start_xpoint:
            raise DomainError(
                "Chapter does not have position data. EPUB must be uploaded with chapter positions."
            )

        book = self.book_repo.find_by_id(chapter.book_id, user_id_vo)
        if not book or not book.file_path or book.file_type != "epub":
            raise BookNotFoundError(
                chapter.book_id.value, message="EPUB file not found for this book"
            )

        epub_path = self.file_repo.find_epub(book.id)
        if not epub_path or not epub_path.exists():
            raise BookNotFoundError(chapter.book_id.value, message="EPUB file not found on disk")

        content = self.text_extraction.extract_chapter_text(
            epub_path=epub_path,
            start_xpoint=chapter.start_xpoint,
            end_xpoint=chapter.end_xpoint,
        )

        # 3. Create quiz session
        session = QuizSession.create(
            user_id=user_id_vo,
            chapter_id=chapter_id_vo,
            question_count=QUIZ_DEFAULT_QUESTION_COUNT,
            created_at=datetime.now(UTC),
        )

        # 4. Run AI to get first question
        usage_context = AIUsageContext(
            user_id=user_id_vo,
            task_type="quiz",
            entity_type="chapter",
            entity_id=chapter_id,
        )
        first_question, message_history = await self.ai_quiz_service.start_quiz(
            content, QUIZ_DEFAULT_QUESTION_COUNT, usage_context
        )

        # 5. Persist session with message history
        session.message_history = message_history
        saved_session = self.quiz_session_repo.create(session)

        logger.info(
            "quiz_session_started",
            session_id=saved_session.id.value,
            chapter_id=chapter_id,
        )

        return saved_session.id.value, first_question
```

**Step 3: Create SendQuizMessageUseCase**

Create `backend/src/application/learning/use_cases/quiz/send_quiz_message_use_case.py`:

```python
import structlog

from src.application.ai.ai_usage_context import AIUsageContext
from src.application.learning.protocols.ai_quiz_service import AIQuizServiceProtocol
from src.application.learning.protocols.quiz_session_repository import (
    QuizSessionRepositoryProtocol,
)
from src.domain.common.value_objects.ids import QuizSessionId, UserId
from src.exceptions import NotFoundError

logger = structlog.get_logger(__name__)


class SendQuizMessageUseCase:
    def __init__(
        self,
        quiz_session_repository: QuizSessionRepositoryProtocol,
        ai_quiz_service: AIQuizServiceProtocol,
    ) -> None:
        self.quiz_session_repo = quiz_session_repository
        self.ai_quiz_service = ai_quiz_service

    async def send(self, session_id: int, user_message: str, user_id: int) -> tuple[str, bool]:
        """Send a message to an existing quiz session.

        Returns:
            Tuple of (ai_response, is_complete)
        """
        session_id_vo = QuizSessionId(session_id)
        user_id_vo = UserId(user_id)

        # 1. Load session
        session = self.quiz_session_repo.find_by_id(session_id_vo, user_id_vo)
        if not session:
            raise NotFoundError(f"Quiz session {session_id} not found")

        if session.completed_at is not None:
            raise NotFoundError(f"Quiz session {session_id} is already completed")

        # 2. Run AI with message history
        usage_context = AIUsageContext(
            user_id=user_id_vo,
            task_type="quiz",
            entity_type="chapter",
            entity_id=session.chapter_id.value,
        )
        ai_response, updated_history = await self.ai_quiz_service.continue_quiz(
            user_message, session.message_history, usage_context
        )

        # 3. Check if quiz is complete (AI includes final summary)
        # We detect completion by checking if the AI response contains summary-like patterns
        # after enough messages have been exchanged. The AI is instructed to provide a summary
        # after all questions are answered.
        # A simple heuristic: count ModelRequest messages (user turns) in history.
        # Each quiz answer is one user turn. We need question_count answers.
        from pydantic_ai import ModelMessagesTypeAdapter
        restored = ModelMessagesTypeAdapter.validate_python(updated_history)
        from pydantic_ai.messages import ModelRequest
        user_turn_count = sum(1 for msg in restored if isinstance(msg, ModelRequest))
        # Subtract 1 for the initial chapter content message
        answer_count = user_turn_count - 1
        is_complete = answer_count >= session.question_count

        # 4. Update session
        completed_at = None
        if is_complete:
            from datetime import UTC, datetime
            completed_at = datetime.now(UTC)

        self.quiz_session_repo.update_message_history(
            session_id_vo, updated_history, completed_at
        )

        logger.info(
            "quiz_message_sent",
            session_id=session_id,
            is_complete=is_complete,
            answer_count=answer_count,
        )

        return ai_response, is_complete
```

**Step 4: Run type check**

Run: `cd backend && uv run pyright src/application/learning/use_cases/quiz/`
Expected: No errors.

**Step 5: Commit**

```bash
git add backend/src/application/learning/use_cases/quiz/
git commit -m "Add StartQuizSession and SendQuizMessage use cases"
```

---

### Task 7: DI Container & Router

**Files:**
- Modify: `backend/src/core.py` (add quiz session registrations)
- Create: `backend/src/infrastructure/learning/routers/quiz_sessions.py`
- Create: `backend/src/infrastructure/learning/schemas/quiz_schemas.py`
- Modify: `backend/src/main.py` (register router)

**Step 1: Create Pydantic schemas**

Create `backend/src/infrastructure/learning/schemas/quiz_schemas.py`:

```python
from pydantic import BaseModel, Field


class CreateQuizSessionResponse(BaseModel):
    session_id: int
    message: str


class SendQuizMessageRequest(BaseModel):
    message: str = Field(..., min_length=1)


class SendQuizMessageResponse(BaseModel):
    message: str
    is_complete: bool
```

**Step 2: Create the router**

Create `backend/src/infrastructure/learning/routers/quiz_sessions.py`:

```python
"""Quiz session endpoints for chapter-based AI quizzes."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from src.application.learning.use_cases.quiz.send_quiz_message_use_case import (
    SendQuizMessageUseCase,
)
from src.application.learning.use_cases.quiz.start_quiz_session_use_case import (
    StartQuizSessionUseCase,
)
from src.core import container
from src.domain.common.exceptions import DomainError
from src.domain.identity.entities.user import User
from src.exceptions import CrossbillError, ValidationError
from src.infrastructure.common.dependencies import require_ai_enabled
from src.infrastructure.common.di import inject_use_case
from src.infrastructure.identity.dependencies import get_current_user
from src.infrastructure.learning.schemas.quiz_schemas import (
    CreateQuizSessionResponse,
    SendQuizMessageRequest,
    SendQuizMessageResponse,
)

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["quiz"])


@router.post(
    "/chapters/{chapter_id}/quiz-sessions",
    response_model=CreateQuizSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
@require_ai_enabled
async def create_quiz_session(
    chapter_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: StartQuizSessionUseCase = Depends(
        inject_use_case(container.start_quiz_session_use_case)
    ),
) -> CreateQuizSessionResponse:
    """Start a new quiz session for a chapter."""
    try:
        session_id, first_question = await use_case.start(chapter_id, current_user.id.value)
        return CreateQuizSessionResponse(session_id=session_id, message=first_question)
    except (CrossbillError, DomainError, ValidationError):
        raise
    except Exception as e:
        logger.error(
            "failed_to_create_quiz_session",
            chapter_id=chapter_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.post(
    "/quiz-sessions/{session_id}/messages",
    response_model=SendQuizMessageResponse,
    status_code=status.HTTP_200_OK,
)
@require_ai_enabled
async def send_quiz_message(
    session_id: int,
    body: SendQuizMessageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: SendQuizMessageUseCase = Depends(
        inject_use_case(container.send_quiz_message_use_case)
    ),
) -> SendQuizMessageResponse:
    """Send a message to an existing quiz session."""
    try:
        ai_response, is_complete = await use_case.send(
            session_id, body.message, current_user.id.value
        )
        return SendQuizMessageResponse(message=ai_response, is_complete=is_complete)
    except (CrossbillError, DomainError, ValidationError):
        raise
    except Exception as e:
        logger.error(
            "failed_to_send_quiz_message",
            session_id=session_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e
```

**Step 3: Register in DI container**

Add these imports to `backend/src/core.py`:

```python
from src.application.learning.use_cases.quiz.start_quiz_session_use_case import (
    StartQuizSessionUseCase,
)
from src.application.learning.use_cases.quiz.send_quiz_message_use_case import (
    SendQuizMessageUseCase,
)
from src.infrastructure.learning.repositories.quiz_session_repository import QuizSessionRepository
```

Add these registrations to the `Container` class in `backend/src/core.py`, after the existing learning use cases (after `get_chapter_flashcard_suggestions_use_case`):

```python
    # Quiz session
    quiz_session_repository = providers.Factory(QuizSessionRepository, db=db)

    start_quiz_session_use_case = providers.Factory(
        StartQuizSessionUseCase,
        quiz_session_repository=quiz_session_repository,
        chapter_repo=chapter_repository,
        book_repo=book_repository,
        file_repo=file_repository,
        text_extraction_service=ebook_text_extraction_service,
        ai_quiz_service=ai_service,
    )

    send_quiz_message_use_case = providers.Factory(
        SendQuizMessageUseCase,
        quiz_session_repository=quiz_session_repository,
        ai_quiz_service=ai_service,
    )
```

**Step 4: Register router in main.py**

Add the import to `backend/src/main.py` alongside the other learning router imports:

```python
from src.infrastructure.learning.routers import quiz_sessions
```

Add the router registration after the other learning routers:

```python
app.include_router(quiz_sessions.router, prefix=settings.API_V1_PREFIX)
```

**Step 5: Run type check**

Run: `cd backend && uv run pyright src/infrastructure/learning/routers/quiz_sessions.py src/infrastructure/learning/schemas/quiz_schemas.py src/core.py`
Expected: No errors.

**Step 6: Run tests**

Run: `cd backend && uv run pytest`
Expected: All existing tests pass.

**Step 7: Commit**

```bash
git add backend/src/infrastructure/learning/schemas/quiz_schemas.py backend/src/infrastructure/learning/routers/quiz_sessions.py backend/src/core.py backend/src/main.py
git commit -m "Add quiz session router, schemas, and DI wiring"
```

---

### Task 8: Backend Tests

**Files:**
- Create: `backend/tests/test_quiz_sessions.py`

**Step 1: Write the test file**

Create `backend/tests/test_quiz_sessions.py`:

```python
"""Tests for quiz session endpoints."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models import Book, Chapter, QuizSession


def create_test_chapter_with_xpoints(db_session: Session, book: Book) -> Chapter:
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
    @patch("src.infrastructure.ai.ai_service.AIService.start_quiz", new_callable=AsyncMock)
    @patch(
        "src.infrastructure.library.services.epub_text_extraction_service.EpubTextExtractionService.extract_chapter_text"
    )
    @patch(
        "src.infrastructure.library.repositories.file_repository.FileRepository.find_epub"
    )
    def test_create_quiz_session_returns_first_question(
        self,
        mock_find_epub,
        mock_extract,
        mock_start_quiz,
        client: TestClient,
        db_session: Session,
        test_book: Book,
    ):
        # Set up book with epub
        test_book.file_path = "/path/to/test.epub"
        test_book.file_type = "epub"
        db_session.commit()

        chapter = create_test_chapter_with_xpoints(db_session, test_book)

        # Mock the file and extraction
        mock_epub_path = AsyncMock()
        mock_epub_path.exists.return_value = True
        mock_find_epub.return_value = mock_epub_path
        mock_extract.return_value = "Chapter content here"

        # Mock AI response
        mock_start_quiz.return_value = (
            "**Question 1/5:** What is the main topic of this chapter?",
            [{"role": "user", "content": "chapter text"}, {"role": "assistant", "content": "question"}],
        )

        response = client.post(f"/api/v1/chapters/{chapter.id}/quiz-sessions")
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert "message" in data
        assert "Question 1/5" in data["message"]

    def test_create_quiz_session_chapter_not_found(self, client: TestClient):
        response = client.post("/api/v1/chapters/99999/quiz-sessions")
        assert response.status_code == 404


class TestSendQuizMessage:
    def test_send_message_session_not_found(self, client: TestClient):
        response = client.post(
            "/api/v1/quiz-sessions/99999/messages",
            json={"message": "My answer"},
        )
        assert response.status_code == 404

    @patch("src.infrastructure.ai.ai_service.AIService.continue_quiz", new_callable=AsyncMock)
    def test_send_message_returns_ai_response(
        self,
        mock_continue_quiz,
        client: TestClient,
        db_session: Session,
        test_book: Book,
    ):
        chapter = create_test_chapter_with_xpoints(db_session, test_book)

        # Create a quiz session directly in DB
        quiz_session = QuizSession(
            user_id=1,
            chapter_id=chapter.id,
            message_history=[{"some": "history"}],
            question_count=5,
        )
        db_session.add(quiz_session)
        db_session.commit()
        db_session.refresh(quiz_session)

        # Mock AI response with minimal message history
        # Need enough ModelRequest messages to not trigger completion (< 5 answers)
        mock_continue_quiz.return_value = (
            "Good answer! **Question 2/5:** What happened next?",
            [{"some": "updated_history"}],
        )

        # Patch the completion detection to avoid needing real pydantic-ai messages
        with patch(
            "src.application.learning.use_cases.quiz.send_quiz_message_use_case.ModelMessagesTypeAdapter"
        ) as mock_adapter:
            mock_adapter.validate_python.return_value = [
                type("Msg", (), {})(),  # initial chapter content
                type("Msg", (), {})(),  # first answer
            ]
            with patch(
                "src.application.learning.use_cases.quiz.send_quiz_message_use_case.ModelRequest",
                type("Msg", (), {}).__class__,
            ):
                response = client.post(
                    f"/api/v1/quiz-sessions/{quiz_session.id}/messages",
                    json={"message": "The main topic is testing"},
                )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "is_complete" in data

    def test_send_empty_message_rejected(self, client: TestClient):
        response = client.post(
            "/api/v1/quiz-sessions/1/messages",
            json={"message": ""},
        )
        assert response.status_code == 422
```

**Step 2: Run the tests**

Run: `cd backend && uv run pytest tests/test_quiz_sessions.py -v`
Expected: All tests pass.

**Step 3: Run full test suite**

Run: `cd backend && uv run pytest`
Expected: All tests pass.

**Step 4: Commit**

```bash
git add backend/tests/test_quiz_sessions.py
git commit -m "Add quiz session endpoint tests"
```

---

### Task 9: Generate Frontend API Client

**Step 1: Start the backend server**

Run: `cd backend && uv run uvicorn src.main:app --reload &`
Expected: Server starts on port 8000.

**Step 2: Run Orval to generate API hooks**

Run: `cd frontend && npm run generate-api`
Expected: New files generated in `src/api/generated/` including quiz-related hooks and model types.

**Step 3: Stop the backend server**

**Step 4: Verify generated files**

Check that the generated files include:
- Quiz-related mutation hooks (look for `quiz` in generated files)
- Model types for `CreateQuizSessionResponse`, `SendQuizMessageRequest`, `SendQuizMessageResponse`

**Step 5: Commit**

```bash
git add frontend/src/api/generated/
git commit -m "Generate frontend API client with quiz session endpoints"
```

---

### Task 10: Frontend — QuizChatDialog Component

**Files:**
- Create: `frontend/src/pages/BookPage/Structure/ChapterDetailDialog/QuizChatDialog.tsx`

**Step 1: Create the component**

Create `frontend/src/pages/BookPage/Structure/ChapterDetailDialog/QuizChatDialog.tsx`:

```tsx
import CloseIcon from '@mui/icons-material/Close';
import SendIcon from '@mui/icons-material/Send';
import {
  Box,
  CircularProgress,
  Dialog,
  IconButton,
  InputAdornment,
  TextField,
  Typography,
  useTheme,
} from '@mui/material';
import { useCallback, useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';

import {
  useCreateQuizSessionApiV1ChaptersChapterIdQuizSessionsPost,
  useSendQuizMessageApiV1QuizSessionsSessionIdMessagesPost,
} from '@/api/generated/quiz/quiz';
import { markdownStyles } from '@/theme/theme';

// NOTE: The exact import paths for the generated hooks above may differ
// based on the OpenAPI tag. After running Orval (Task 9), check the actual
// generated file paths and adjust the imports accordingly.

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface QuizChatDialogProps {
  open: boolean;
  onClose: () => void;
  chapterId: number;
  chapterName: string;
}

export function QuizChatDialog({ open, onClose, chapterId, chapterName }: QuizChatDialogProps) {
  const theme = useTheme();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { mutate: createSession, isPending: isCreating } =
    useCreateQuizSessionApiV1ChaptersChapterIdQuizSessionsPost({
      mutation: {
        onSuccess: (data) => {
          setSessionId(data.session_id);
          setMessages([{ role: 'assistant', content: data.message }]);
        },
      },
    });

  const { mutate: sendMessage, isPending: isSending } =
    useSendQuizMessageApiV1QuizSessionsSessionIdMessagesPost({
      mutation: {
        onSuccess: (data) => {
          setMessages((prev) => [...prev, { role: 'assistant', content: data.message }]);
          setIsComplete(data.is_complete);
        },
      },
    });

  // Start session when dialog opens
  useEffect(() => {
    if (open && sessionId === null && !isCreating) {
      createSession({ chapterId });
    }
  }, [open, sessionId, isCreating, createSession, chapterId]);

  // Reset state when dialog closes
  useEffect(() => {
    if (!open) {
      setMessages([]);
      setInput('');
      setSessionId(null);
      setIsComplete(false);
    }
  }, [open]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = useCallback(() => {
    if (!input.trim() || !sessionId || isSending) return;

    const userMessage = input.trim();
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setInput('');

    sendMessage({ sessionId, data: { message: userMessage } });
  }, [input, sessionId, isSending, sendMessage]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  return (
    <Dialog fullScreen open={open} onClose={onClose}>
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          p: 2,
          borderBottom: 1,
          borderColor: 'divider',
        }}
      >
        <Typography variant="h6" noWrap sx={{ flex: 1 }}>
          Quiz: {chapterName}
        </Typography>
        <IconButton onClick={onClose} edge="end">
          <CloseIcon />
        </IconButton>
      </Box>

      {/* Messages */}
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          p: 2,
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
        }}
      >
        {isCreating && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {messages.map((msg, i) => (
          <Box
            key={i}
            sx={{
              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '80%',
              p: 1.5,
              borderRadius: 2,
              bgcolor: msg.role === 'user' ? 'primary.main' : 'grey.100',
              color: msg.role === 'user' ? 'primary.contrastText' : 'text.primary',
              ...((theme.palette.mode === 'dark' && msg.role === 'assistant')
                ? { bgcolor: 'grey.800' }
                : {}),
            }}
          >
            {msg.role === 'assistant' ? (
              <Box sx={markdownStyles(theme)}>
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </Box>
            ) : (
              <Typography variant="body1">{msg.content}</Typography>
            )}
          </Box>
        ))}

        {isSending && (
          <Box sx={{ alignSelf: 'flex-start' }}>
            <CircularProgress size={24} />
          </Box>
        )}

        <div ref={messagesEndRef} />
      </Box>

      {/* Input */}
      <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
        <TextField
          fullWidth
          placeholder={isComplete ? 'Quiz complete!' : 'Type your answer...'}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isSending || isCreating || isComplete}
          multiline
          maxRows={3}
          slotProps={{
            input: {
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={handleSend}
                    disabled={!input.trim() || isSending || isCreating || isComplete}
                    color="primary"
                  >
                    <SendIcon />
                  </IconButton>
                </InputAdornment>
              ),
            },
          }}
        />
      </Box>
    </Dialog>
  );
}
```

**Step 2: Run type check**

Run: `cd frontend && npm run type-check`
Expected: No errors (import paths may need adjustment based on Orval output from Task 9).

**Step 3: Commit**

```bash
git add frontend/src/pages/BookPage/Structure/ChapterDetailDialog/QuizChatDialog.tsx
git commit -m "Add QuizChatDialog component"
```

---

### Task 11: Frontend — Wire Quiz Button into ChapterDetailDialog

**Files:**
- Modify: `frontend/src/pages/BookPage/Structure/ChapterDetailDialog/ChapterDetailDialog.tsx`

**Step 1: Add quiz button to ChapterDetailDialog**

Import the new components at the top of `ChapterDetailDialog.tsx`:

```tsx
import { useState } from 'react';
import { AIActionButton } from '@/components/buttons/AIActionButton';
import { AIFeature } from '@/components/features/AIFeature';
import { QuizChatDialog } from './QuizChatDialog';
```

Inside the component, add state for the quiz dialog:

```tsx
const [quizOpen, setQuizOpen] = useState(false);
```

In the JSX, add the quiz button after the `PrereadingSummarySection` and before `HighlightsSection`. Also add the `QuizChatDialog`:

```tsx
<PrereadingSummarySection ... />

<AIFeature>
  <Box sx={{ px: 2, pb: 1 }}>
    <AIActionButton text="Quiz me" onClick={() => setQuizOpen(true)} />
  </Box>
</AIFeature>

<HighlightsSection ... />

{/* Quiz dialog */}
<QuizChatDialog
  open={quizOpen}
  onClose={() => setQuizOpen(false)}
  chapterId={chapter.id}
  chapterName={chapter.name}
/>
```

**Step 2: Run type check**

Run: `cd frontend && npm run type-check`
Expected: No errors.

**Step 3: Run lint**

Run: `cd frontend && npm run lint`
Expected: No errors.

**Step 4: Commit**

```bash
git add frontend/src/pages/BookPage/Structure/ChapterDetailDialog/ChapterDetailDialog.tsx
git commit -m "Add Quiz Me button to ChapterDetailDialog"
```

---

### Task 12: Manual Testing & Polish

**Step 1: Start the backend**

Run: `cd backend && uv run uvicorn src.main:app --reload`

**Step 2: Run the migration**

Run: `cd backend && uv run alembic upgrade head`

**Step 3: Start the frontend**

Run: `cd frontend && npm run dev`

**Step 4: Manual test checklist**

- [ ] Open a book's structure view
- [ ] Click on a chapter to open ChapterDetailDialog
- [ ] Verify "Quiz me" button appears near the prereading summary (only when AI is enabled)
- [ ] Click "Quiz me" — quiz modal opens with loading spinner
- [ ] First question appears from the AI
- [ ] Type an answer and press Enter — AI responds with feedback + next question
- [ ] Complete all 5 questions — AI provides summary
- [ ] Input is disabled after quiz completion
- [ ] Close the modal
- [ ] Verify no console errors

**Step 5: Fix any issues found during manual testing**

**Step 6: Final commit if needed**

```bash
git add -A
git commit -m "Polish quiz feature after manual testing"
```
