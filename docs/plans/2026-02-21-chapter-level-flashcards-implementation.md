# Chapter-Level Flashcards Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add optional `chapter_id` to flashcards so users can create flashcards tied to a chapter (with manual input or AI suggestions from prereading summaries) via the ChapterDetailDialog.

**Architecture:** Extends the existing DDD flashcard system by adding `chapter_id` through all layers (domain entity -> ORM -> mapper -> schemas -> use cases -> routers -> frontend). Adds a new AI suggestion endpoint for chapters that reuses the existing AI flashcard agent with prereading summary + keypoints as input.

**Tech Stack:** Python/FastAPI backend, SQLAlchemy ORM, Alembic migrations, React/TypeScript frontend with MUI, TanStack Query, orval-generated API hooks.

---

### Task 1: Alembic Migration -- Add `chapter_id` to flashcards table

**Files:**
- Create: `backend/alembic/versions/042_add_chapter_id_to_flashcards.py`

**Step 1: Create the migration file**

```python
"""Add chapter_id column to flashcards table.

Revision ID: 042
Revises: 041
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "042"
down_revision: str | Sequence[str] | None = "041"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "flashcards",
        sa.Column(
            "chapter_id",
            sa.Integer(),
            sa.ForeignKey("chapters.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("flashcards", "chapter_id")
```

**Step 2: Run the migration**

Run: `cd backend && .venv/bin/alembic upgrade head`

**Step 3: Commit**

```
feat: add chapter_id column to flashcards table
```

---

### Task 2: Domain Entity -- Add `chapter_id` to Flashcard

**Files:**
- Modify: `backend/src/domain/learning/entities/flashcard.py`

**Step 1: Add `chapter_id` field and update factory methods**

Add `chapter_id: ChapterId | None = None` field to the dataclass (after `highlight_id`).

Update `create()` classmethod to accept `chapter_id: ChapterId | None = None` parameter and pass it through.

Update `create_with_id()` classmethod to accept `chapter_id: ChapterId | None = None` parameter and pass it through.

Add `ChapterId` to the import from `src.domain.common.value_objects`.

**Step 2: Run type check**

Run: `cd backend && .venv/bin/pyright src/domain/learning/entities/flashcard.py`

**Step 3: Commit**

```
feat: add chapter_id to Flashcard domain entity
```

---

### Task 3: ORM Model -- Add `chapter_id` column

**Files:**
- Modify: `backend/src/models.py` (Flashcard class, around line 503-539)

**Step 1: Add `chapter_id` column and relationship**

Add after the `highlight_id` column (around line 516):

```python
chapter_id: Mapped[int | None] = mapped_column(
    ForeignKey("chapters.id", ondelete="CASCADE"), index=True, nullable=True
)
```

Add to the relationships section (after the `highlight` relationship):

```python
chapter: Mapped["Chapter | None"] = relationship()
```

**Step 2: Run type check**

Run: `cd backend && .venv/bin/pyright src/models.py`

**Step 3: Commit**

```
feat: add chapter_id column to Flashcard ORM model
```

---

### Task 4: Mapper -- Handle `chapter_id` conversion

**Files:**
- Modify: `backend/src/infrastructure/learning/mappers/flashcard_mapper.py`

**Step 1: Update imports**

Add `ChapterId` to the import from `src.domain.common.value_objects`.

**Step 2: Update `to_domain()`**

Add `chapter_id` parameter to the `Flashcard.create_with_id()` call:

```python
chapter_id=ChapterId(orm_model.chapter_id) if orm_model.chapter_id else None,
```

**Step 3: Update `to_orm()` -- update existing branch**

Add in the "Update existing" branch (after `highlight_id` assignment):

```python
orm_model.chapter_id = (
    domain_entity.chapter_id.value if domain_entity.chapter_id else None
)
```

**Step 4: Update `to_orm()` -- create new branch**

Add in the "Create new" `FlashcardORM()` constructor:

```python
chapter_id=domain_entity.chapter_id.value if domain_entity.chapter_id else None,
```

**Step 5: Run type check**

Run: `cd backend && .venv/bin/pyright src/infrastructure/learning/mappers/flashcard_mapper.py`

**Step 6: Commit**

```
feat: add chapter_id to FlashcardMapper
```

---

### Task 5: Pydantic Schemas -- Add `chapter_id`

**Files:**
- Modify: `backend/src/infrastructure/learning/schemas/flashcard_schemas.py`

**Step 1: Add `chapter_id` to `FlashcardCreateRequest`**

Add after the `answer` field (line 34):

```python
chapter_id: int | None = Field(None, description="Optional chapter ID to associate with")
```

**Step 2: Add `chapter_id` to `Flashcard` response schema**

Add after `highlight_id` (line 25):

```python
chapter_id: int | None = None
```

**Step 3: Run type check**

Run: `cd backend && .venv/bin/pyright src/infrastructure/learning/schemas/flashcard_schemas.py`

**Step 4: Commit**

```
feat: add chapter_id to flashcard Pydantic schemas
```

---

### Task 6: Use Case -- Update `CreateFlashcardForBookUseCase` to accept `chapter_id`

**Files:**
- Modify: `backend/src/application/learning/use_cases/flashcards/create_flashcard_for_book_use_case.py`

**Step 1: Add chapter repository dependency**

Add import:
```python
from src.application.library.protocols.chapter_repository import ChapterRepositoryProtocol
```

Add `ChapterId` to the ids import.

Add `chapter_repository` parameter to `__init__`:
```python
def __init__(
    self,
    flashcard_repository: FlashcardRepositoryProtocol,
    book_repository: BookRepositoryProtocol,
    chapter_repository: ChapterRepositoryProtocol,
) -> None:
    self.flashcard_repository = flashcard_repository
    self.book_repository = book_repository
    self.chapter_repository = chapter_repository
```

**Step 2: Update `create_flashcard` method signature and logic**

Add `chapter_id: int | None = None` parameter. Add validation after the book validation:

```python
chapter_id_vo: ChapterId | None = None
if chapter_id is not None:
    chapter_id_vo = ChapterId(chapter_id)
    chapter = self.chapter_repository.find_by_id(chapter_id_vo, user_id_vo)
    if not chapter:
        raise NotFoundError(f"Chapter with id {chapter_id} not found")
    if chapter.book_id != book_id_vo:
        raise ValidationError("Chapter does not belong to this book")
```

Add the relevant import for `NotFoundError` from `src.exceptions`.

Pass `chapter_id=chapter_id_vo` to `Flashcard.create()`.

**Step 3: Run type check**

Run: `cd backend && .venv/bin/pyright src/application/learning/use_cases/flashcards/create_flashcard_for_book_use_case.py`

**Step 4: Commit**

```
feat: add chapter_id support to CreateFlashcardForBookUseCase
```

---

### Task 7: DI Container -- Wire `chapter_repository` into `CreateFlashcardForBookUseCase`

**Files:**
- Modify: `backend/src/core.py` (around lines 505-509)

**Step 1: Add `chapter_repository` to the factory**

Update the `create_flashcard_for_book_use_case` registration:

```python
create_flashcard_for_book_use_case = providers.Factory(
    CreateFlashcardForBookUseCase,
    flashcard_repository=flashcard_repository,
    book_repository=book_repository,
    chapter_repository=chapter_repository,
)
```

**Step 2: Run type check**

Run: `cd backend && .venv/bin/pyright src/core.py`

**Step 3: Commit**

```
feat: wire chapter_repository into CreateFlashcardForBookUseCase DI
```

---

### Task 8: Router -- Update `POST /books/{book_id}/flashcards` to pass `chapter_id`

**Files:**
- Modify: `backend/src/infrastructure/learning/routers/book_flashcards.py`

**Step 1: Update the create endpoint**

Pass `chapter_id` from the request to the use case (around line 68-73):

```python
flashcard_entity = use_case.create_flashcard(
    book_id=book_id,
    user_id=current_user.id.value,
    question=request.question,
    answer=request.answer,
    chapter_id=request.chapter_id,
)
```

**Step 2: Update response schema construction**

Add `chapter_id` to the Flashcard schema construction (around line 75-84):

```python
flashcard = Flashcard(
    id=flashcard_entity.id.value,
    user_id=flashcard_entity.user_id.value,
    book_id=flashcard_entity.book_id.value,
    highlight_id=flashcard_entity.highlight_id.value
    if flashcard_entity.highlight_id
    else None,
    chapter_id=flashcard_entity.chapter_id.value
    if flashcard_entity.chapter_id
    else None,
    question=flashcard_entity.question,
    answer=flashcard_entity.answer,
)
```

**Step 3: Update the GET endpoint response construction**

In the `get_flashcards_for_book` function (around line 180-188), add `chapter_id` to the `FlashcardWithHighlight` construction:

```python
flashcard_schema = FlashcardWithHighlight(
    id=fc.id.value,
    user_id=fc.user_id.value,
    book_id=fc.book_id.value,
    highlight_id=fc.highlight_id.value if fc.highlight_id else None,
    chapter_id=fc.chapter_id.value if fc.chapter_id else None,
    question=fc.question,
    answer=fc.answer,
    highlight=highlight_schema,
)
```

**Step 4: Run type check**

Run: `cd backend && .venv/bin/pyright src/infrastructure/learning/routers/book_flashcards.py`

**Step 5: Commit**

```
feat: pass chapter_id through book flashcard router endpoints
```

---

### Task 9: Update BookDetails response -- Include `chapter_id` in flashcard serialization

**Files:**
- Modify: `backend/src/infrastructure/library/routers/books.py` (around lines 198-208)
- Modify: `backend/src/application/library/use_cases/book_management/get_book_details_use_case.py` (around lines 158-160)

**Step 1: Update `_build_book_details_schema` in `books.py`**

Add `chapter_id` to the book_flashcards mapping (around line 198-208):

```python
book_flashcards=[
    Flashcard(
        id=f.id.value,
        user_id=f.user_id.value,
        book_id=f.book_id.value,
        highlight_id=None,
        chapter_id=f.chapter_id.value if f.chapter_id else None,
        question=f.question,
        answer=f.answer,
    )
    for f in agg.book_flashcards
],
```

**Step 2: Update `_map_chapters_to_schemas` in `books.py`**

Add `chapter_id` to the highlight-level flashcard mapping (around line 102-112):

```python
flashcards=[
    Flashcard(
        id=fc.id.value,
        user_id=fc.user_id.value,
        book_id=fc.book_id.value,
        highlight_id=fc.highlight_id.value if fc.highlight_id else None,
        chapter_id=fc.chapter_id.value if fc.chapter_id else None,
        question=fc.question,
        answer=fc.answer,
    )
    for fc in hw.flashcards
],
```

**Step 3: Update `get_book_details_use_case.py` book_flashcards filter**

Currently at line 160:
```python
book_flashcards = [f for f in all_flashcards if f.highlight_id is None]
```

Change to exclude chapter-linked flashcards from book_flashcards (they should appear in their chapter):
```python
book_flashcards = [f for f in all_flashcards if f.highlight_id is None and f.chapter_id is None]
```

**Step 4: Handle chapter-linked flashcards in chapters**

Chapter-linked flashcards (those with `chapter_id` set but `highlight_id` is None) need to appear within their chapter's data. This requires adding them to the `ChapterWithHighlights` aggregation.

Look at how `HighlightGroupingService.group_by_chapter()` works and the `ChapterWithHighlights` domain dataclass. Chapter-linked flashcards should be included in the chapter data alongside highlight-sourced flashcards.

The simplest approach: after building `merged` chapters, inject chapter-linked flashcards into the matching chapter's flashcard list. Extract chapter-linked flashcards from `all_flashcards`:

```python
chapter_flashcards = [f for f in all_flashcards if f.chapter_id is not None and f.highlight_id is None]
```

Then for each, find the matching chapter in `merged` and append the flashcard to a new `chapter_flashcards` field on `BookDetailsAggregation`, or inject them into the response at the router level.

**Note:** The exact approach here depends on the `ChapterWithHighlights` structure. The chapter's highlights each carry their own flashcards. For chapter-level flashcards (not tied to a highlight), we need to decide where they go. The cleanest approach is to add a `chapter_flashcards` list to the `BookDetailsAggregation` and handle them in the router's `_build_book_details_schema`. Add `chapter_flashcards: list[Flashcard]` to `BookDetailsAggregation` at `backend/src/domain/library/services/book_details_aggregator.py`. In the router, when building each chapter schema, also include chapter-linked flashcards.

This needs careful investigation of the `ChapterWithHighlights` Pydantic schema at `backend/src/infrastructure/reading/schemas/highlight_schemas.py` to see if it has a top-level `flashcards` field or if flashcards are only nested inside highlights.

**Step 5: Run type check and tests**

Run: `cd backend && .venv/bin/pyright src/infrastructure/library/routers/books.py && .venv/bin/pytest tests/test_flashcards.py -v`

**Step 6: Commit**

```
feat: include chapter_id in BookDetails flashcard serialization
```

---

### Task 10: New Use Case -- `GetChapterFlashcardSuggestionsUseCase`

**Files:**
- Create: `backend/src/application/learning/use_cases/flashcards/get_chapter_flashcard_suggestions_use_case.py`

**Step 1: Create the use case**

```python
"""Use case for AI-generated flashcard suggestions from chapter prereading."""

import structlog

from src.application.learning.protocols.ai_flashcard_service import (
    AIFlashcardServiceProtocol,
)
from src.application.learning.use_cases.dtos import FlashcardSuggestion
from src.application.reading.protocols.chapter_prereading_repository import (
    ChapterPrereadingRepositoryProtocol,
)
from src.domain.common.value_objects.ids import ChapterId
from src.exceptions import NotFoundError

logger = structlog.get_logger(__name__)


class GetChapterFlashcardSuggestionsUseCase:
    """Use case for AI-generated flashcard suggestions from chapter prereading."""

    def __init__(
        self,
        chapter_prereading_repository: ChapterPrereadingRepositoryProtocol,
        ai_flashcard_service: AIFlashcardServiceProtocol,
    ) -> None:
        self.chapter_prereading_repository = chapter_prereading_repository
        self.ai_flashcard_service = ai_flashcard_service

    async def get_suggestions(self, chapter_id: int) -> list[FlashcardSuggestion]:
        """
        Get AI-generated flashcard suggestions from chapter prereading content.

        Args:
            chapter_id: ID of the chapter

        Returns:
            List of flashcard suggestions

        Raises:
            NotFoundError: If chapter prereading not found
        """
        chapter_id_vo = ChapterId(chapter_id)

        prereading = self.chapter_prereading_repository.find_by_chapter_id(chapter_id_vo)
        if not prereading:
            raise NotFoundError(
                f"No prereading content found for chapter {chapter_id}. "
                "Generate a pre-reading summary first."
            )

        # Combine summary and keypoints into a single text block
        content_parts = [prereading.summary]
        if prereading.keypoints:
            content_parts.append("\nKey Points:")
            content_parts.extend(f"- {kp}" for kp in prereading.keypoints)
        content = "\n".join(content_parts)

        ai_suggestions = await self.ai_flashcard_service.generate_flashcard_suggestions(content)

        suggestions = [
            FlashcardSuggestion(question=s.question, answer=s.answer)
            for s in ai_suggestions
        ]

        logger.info(
            "chapter_flashcard_suggestions_generated",
            chapter_id=chapter_id,
            suggestion_count=len(suggestions),
        )

        return suggestions
```

**Step 2: Run type check**

Run: `cd backend && .venv/bin/pyright src/application/learning/use_cases/flashcards/get_chapter_flashcard_suggestions_use_case.py`

**Step 3: Commit**

```
feat: add GetChapterFlashcardSuggestionsUseCase
```

---

### Task 11: New Router -- `GET /chapters/{chapter_id}/flashcard_suggestions`

**Files:**
- Create: `backend/src/infrastructure/learning/routers/ai_chapter_flashcard_suggestions.py`
- Modify: `backend/src/main.py` (around line 270)
- Modify: `backend/src/core.py` (around line 530-534)

**Step 1: Register use case in DI container**

Add after `get_flashcard_suggestions_use_case` in `core.py` (around line 534):

```python
get_chapter_flashcard_suggestions_use_case = providers.Factory(
    GetChapterFlashcardSuggestionsUseCase,
    chapter_prereading_repository=chapter_prereading_repository,
    ai_flashcard_service=ai_service,
)
```

Add the import for `GetChapterFlashcardSuggestionsUseCase` near the other flashcard use case imports.

**Step 2: Create the router**

```python
"""AI-powered flashcard suggestions for chapters."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from src.application.learning.use_cases.flashcards.get_chapter_flashcard_suggestions_use_case import (
    GetChapterFlashcardSuggestionsUseCase,
)
from src.core import container
from src.domain.common.exceptions import DomainError
from src.domain.identity.entities.user import User
from src.exceptions import CrossbillError, ValidationError
from src.infrastructure.common.dependencies import require_ai_enabled
from src.infrastructure.common.di import inject_use_case
from src.infrastructure.identity.dependencies import get_current_user
from src.infrastructure.learning.schemas import (
    FlashcardSuggestionItem,
    HighlightFlashcardSuggestionsResponse,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/chapters", tags=["flashcards"])


@router.get(
    "/{chapter_id}/flashcard_suggestions",
    response_model=HighlightFlashcardSuggestionsResponse,
    status_code=status.HTTP_200_OK,
)
@require_ai_enabled
async def get_chapter_flashcard_suggestions(
    chapter_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: GetChapterFlashcardSuggestionsUseCase = Depends(
        inject_use_case(container.get_chapter_flashcard_suggestions_use_case)
    ),
) -> HighlightFlashcardSuggestionsResponse:
    """
    Get AI-generated flashcard suggestions from chapter prereading content.

    Requires the chapter to have a generated pre-reading summary.
    """
    try:
        suggestions_data = await use_case.get_suggestions(chapter_id)

        suggestions = [
            FlashcardSuggestionItem(question=s.question, answer=s.answer)
            for s in suggestions_data
        ]

        return HighlightFlashcardSuggestionsResponse(suggestions=suggestions)
    except (CrossbillError, DomainError, ValidationError):
        raise
    except Exception as e:
        logger.error(
            "failed_to_generate_chapter_flashcard_suggestions",
            chapter_id=chapter_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e
```

**Step 3: Register router in `main.py`**

Add after line 270 (`ai_flashcard_suggestions`):

```python
app.include_router(ai_chapter_flashcard_suggestions.router, prefix=settings.API_V1_PREFIX)
```

Add the import at the top of `main.py`:
```python
from src.infrastructure.learning.routers import ai_chapter_flashcard_suggestions
```

**Step 4: Run type check and test**

Run: `cd backend && .venv/bin/pyright src/infrastructure/learning/routers/ai_chapter_flashcard_suggestions.py && .venv/bin/pytest tests/ -v`

**Step 5: Commit**

```
feat: add GET /chapters/{chapter_id}/flashcard_suggestions endpoint
```

---

### Task 12: Backend Tests -- Update existing and add new tests

**Files:**
- Modify: `backend/tests/test_flashcards.py`

**Step 1: Update `TestCreateFlashcardForBook` to test `chapter_id`**

Add a test for creating a flashcard with `chapter_id`:

```python
def test_create_flashcard_with_chapter_id(self, client, test_book, test_chapter):
    response = client.post(
        f"/api/v1/books/{test_book.id}/flashcards",
        json={
            "question": "Chapter question",
            "answer": "Chapter answer",
            "chapter_id": test_chapter.id,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["flashcard"]["chapter_id"] == test_chapter.id
    assert data["flashcard"]["highlight_id"] is None
```

Add a test for invalid `chapter_id`:

```python
def test_create_flashcard_with_invalid_chapter_id(self, client, test_book):
    response = client.post(
        f"/api/v1/books/{test_book.id}/flashcards",
        json={
            "question": "Q",
            "answer": "A",
            "chapter_id": 99999,
        },
    )
    assert response.status_code == 404
```

You may need to add a `test_chapter` fixture in `conftest.py` if one doesn't exist. Check for an existing chapter fixture first.

**Step 2: Update existing tests to verify `chapter_id` is None**

In existing flashcard creation tests, assert that `chapter_id` is `None` in the response.

**Step 3: Run tests**

Run: `cd backend && .venv/bin/pytest tests/test_flashcards.py -v`

**Step 4: Commit**

```
test: add chapter_id tests for flashcard creation
```

---

### Task 13: MCP Server -- Add `chapter_id` to `create_flashcard`

**Files:**
- Modify: `mcp-server/src/crossbill_mcp/tools/flashcards.py`
- Modify: `mcp-server/src/crossbill_mcp/client.py`

**Step 1: Update the MCP tool**

Add `chapter_id` parameter to `create_flashcard` in `tools/flashcards.py`:

```python
@server.tool()
async def create_flashcard(
    book_id: int,
    question: str,
    answer: str,
    highlight_id: int | None = None,
    chapter_id: int | None = None,
) -> str:
    """Create a new flashcard for a book, optionally linked to a highlight or chapter."""
    result = await client.create_flashcard(book_id, question, answer, highlight_id, chapter_id)
    return json.dumps(result, indent=2, default=str)
```

**Step 2: Update the client**

Add `chapter_id` parameter to `create_flashcard` in `client.py`:

```python
async def create_flashcard(
    self,
    book_id: int,
    question: str,
    answer: str,
    highlight_id: int | None = None,
    chapter_id: int | None = None,
) -> dict:
    """Create a flashcard for a book or linked to a highlight."""
    if highlight_id is not None:
        response = await self._request(
            "POST",
            f"/api/v1/highlights/{highlight_id}/flashcards",
            json={"question": question, "answer": answer},
        )
    else:
        body: dict[str, str | int] = {"question": question, "answer": answer}
        if chapter_id is not None:
            body["chapter_id"] = chapter_id
        response = await self._request(
            "POST",
            f"/api/v1/books/{book_id}/flashcards",
            json=body,
        )
    return response.json()
```

**Step 3: Commit**

```
feat: add chapter_id to MCP create_flashcard tool
```

---

### Task 14: Frontend -- Regenerate API types via orval

**Step 1: Start backend server if not running**

Run: `cd backend && .venv/bin/uvicorn src.main:app --reload` (in background)

**Step 2: Regenerate API types**

Run: `cd frontend && npx orval`

This regenerates all types in `frontend/src/api/generated/`. The `Flashcard` type should now include `chapter_id: number | null`, and `FlashcardCreateRequest` should include `chapter_id?: number | null`.

**Step 3: Verify types generated correctly**

Check that `frontend/src/api/generated/model/flashcard.ts` includes `chapter_id`.
Check that `frontend/src/api/generated/model/flashcardCreateRequest.ts` includes `chapter_id`.
Check that new hooks were generated for `GET /chapters/{chapter_id}/flashcard_suggestions`.

**Step 4: Run type check**

Run: `cd frontend && npm run type-check`

**Step 5: Commit**

```
feat: regenerate API types with chapter_id support
```

---

### Task 15: Frontend -- Update `FlashcardsTab` grouping logic

**Files:**
- Modify: `frontend/src/pages/BookPage/FlashcardsTab/FlashcardsTab.tsx` (lines 60-83)

**Step 1: Update `allFlashcardsWithContext` extraction**

Currently, `book.book_flashcards` are mapped with `chapterId: null`. After the backend change, `book_flashcards` will only contain flashcards with both `highlight_id` and `chapter_id` null. Chapter-linked flashcards will have `chapter_id` set.

Update the `bookLevelFlashcards` mapping (around line 74-80) to use `chapter_id` from the flashcard:

```typescript
const bookLevelFlashcards: FlashcardWithContext[] = (book.book_flashcards ?? []).map((fc) => ({
  ...fc,
  highlight: null,
  chapterName: fc.chapter_id ? 'Unknown Chapter' : 'Book Flashcards',
  chapterId: fc.chapter_id ?? null,
  highlightTags: [],
}));
```

However, the better approach is to ensure chapter-linked flashcards come through the chapters hierarchy in the BookDetails response. If they are included in the chapter data (via Task 9), they will naturally be grouped correctly. If they come through `book_flashcards`, they need the chapter name.

The implementation depends on how Task 9 resolves the chapter data inclusion. If chapter-linked flashcards are included in `chapters[].highlights[].flashcards[]`, no change is needed here. If they come through `book_flashcards`, this mapping handles them.

**Step 2: Run type check**

Run: `cd frontend && npm run type-check`

**Step 3: Commit**

```
feat: update FlashcardsTab grouping for chapter-linked flashcards
```

---

### Task 16: Frontend -- Enhance `ChapterDetailDialog/FlashcardsSection` with create form and AI suggestions

**Files:**
- Modify: `frontend/src/pages/BookPage/StructureTab/ChapterDetailDialog/FlashcardsSection.tsx`
- Modify: `frontend/src/pages/BookPage/StructureTab/ChapterDetailDialog/ChapterDetailDialog.tsx`

This is the largest frontend task. Model the implementation after `frontend/src/pages/BookPage/HighlightsTab/HighlightViewModal/components/FlashcardSection.tsx`.

**Step 1: Update `ChapterDetailDialog.tsx` to pass `prereadingSummary` to `FlashcardsSection`**

Add `prereadingSummary` prop from `prereadingByChapterId[chapter.id]`:

```tsx
<FlashcardsSection
  chapter={chapter}
  bookId={book.id}
  prereadingSummary={prereadingSummary}
/>
```

**Step 2: Rewrite `FlashcardsSection.tsx`**

The new `FlashcardsSection` needs:

1. **Props:** Add `prereadingSummary?: ChapterPrereadingResponse`
2. **Existing flashcards list** (keep current `flashcardsWithContext` logic, but also include chapter-linked flashcards)
3. **Create form** -- `CreateFlashcardForm` sub-component with question/answer TextFields and Add/Update button
4. **AI suggestions** -- `FlashcardSuggestions` sub-component gated by `<AIFeature>`, with "Suggest flashcards" button (only when `prereadingSummary` exists)
5. **Mutations** -- Use `useCreateFlashcardForBookApiV1BooksBookIdFlashcardsPost` with `chapter_id` set to the chapter's ID. Use `useUpdateFlashcardApiV1FlashcardsFlashcardIdPut` for editing. Invalidate book details query on success.
6. **AI suggestions hook** -- Use the newly generated query hook for `GET /chapters/{chapter_id}/flashcard_suggestions` with `enabled: false` and manual `refetch()`.

Key differences from the HighlightViewModal's FlashcardSection:
- Creates flashcards via `POST /books/{bookId}/flashcards` with `{ question, answer, chapter_id }` instead of `POST /highlights/{highlightId}/flashcards`
- AI suggestions come from `GET /chapters/{chapterId}/flashcard_suggestions` instead of `GET /highlights/{highlightId}/flashcard_suggestions`
- The "Suggest flashcards" button should only appear when `prereadingSummary` is available (if no prereading exists, AI can't generate suggestions)

Reference files for patterns:
- `FlashcardSection.tsx` (HighlightViewModal) -- create form, suggestions, mutations pattern
- `FlashcardSuggestionCard.tsx` -- reuse directly for suggestion display
- `FlashcardListCard.tsx` -- reuse directly for existing flashcard display
- `PrereadingSummarySection.tsx` -- pattern for chapter-level AI feature gating

**Step 3: Run type check and lint**

Run: `cd frontend && npm run type-check && npm run lint`

**Step 4: Commit**

```
feat: add flashcard creation and AI suggestions to ChapterDetailDialog
```

---

### Task 17: Frontend -- Final lint, format, and type check

**Step 1: Run all checks**

Run: `cd frontend && npm run lint:fix && npm run format && npm run type-check`

**Step 2: Run backend checks**

Run: `cd backend && .venv/bin/ruff check . && .venv/bin/pyright && .venv/bin/pytest`

**Step 3: Fix any issues found**

**Step 4: Final commit if needed**

```
chore: fix lint and type check issues
```

---

## Task Dependency Notes

- Tasks 1-5 (DB migration, domain, ORM, mapper, schemas) are foundational and must be done first in order
- Tasks 6-8 (use case, DI, router) depend on tasks 1-5
- Task 9 (BookDetails) depends on tasks 1-5 and requires careful investigation of the chapter data structure
- Tasks 10-11 (AI suggestions) are independent of tasks 6-9 but depend on tasks 1-5
- Task 12 (tests) depends on tasks 6-8
- Task 13 (MCP) depends on task 8
- Task 14 (orval) depends on all backend tasks being complete
- Tasks 15-16 (frontend) depend on task 14
- Task 17 is the final verification pass
