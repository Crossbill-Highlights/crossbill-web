# Prereading Answer Persistence Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist user answers to pre-reading questions via auto-save with debounce.

**Architecture:** Add `user_answer` field through all DDD layers (domain → infrastructure → API → frontend). New PUT endpoint for saving answers. Frontend debounces and sends all answers on change.

**Tech Stack:** Python/FastAPI, SQLAlchemy (JSONB), React/TypeScript, TanStack Query, orval (API codegen)

---

## File Structure

**Backend — New files:**
- `backend/src/application/reading/use_cases/chapter_prereading/update_prereading_answers_use_case.py` — use case for updating user answers

**Backend — Modified files:**
- `backend/src/domain/reading/entities/chapter_prereading_content.py` — add `user_answer` to `PrereadingQuestion`, add `update_user_answers` method
- `backend/src/infrastructure/reading/mappers/chapter_prereading_mapper.py` — read/write `user_answer` in JSONB
- `backend/src/infrastructure/reading/schemas/chapter_prereading_schemas.py` — add request/response schemas for answers
- `backend/src/infrastructure/reading/routers/chapter_prereading.py` — add PUT endpoint
- `backend/src/containers/reading.py` — wire up new use case

**Backend — Test files:**
- `backend/tests/unit/domain/reading/entities/test_chapter_prereading_content.py` — test `user_answer` field and `update_user_answers` method

**Frontend — Modified files:**
- `frontend/src/pages/BookPage/Structure/ChapterDetailDialog/PrereadingQuestionsSection.tsx` — debounced auto-save, init from persisted answers

**Frontend — Regenerated files (via orval):**
- `frontend/src/api/generated/prereading/prereading.ts` — new mutation hook
- `frontend/src/api/generated/model/prereadingQuestionResponse.ts` — adds `user_answer`

---

## Chunk 1: Backend Domain + Infrastructure

### Task 1: Add `user_answer` to `PrereadingQuestion` dataclass

**Files:**
- Modify: `backend/src/domain/reading/entities/chapter_prereading_content.py:9-12`

- [ ] **Step 1: Update `PrereadingQuestion` dataclass**

Add `user_answer` field with default empty string:

```python
@dataclass(frozen=True)
class PrereadingQuestion:
    question: str
    answer: str
    user_answer: str = ""
```

- [ ] **Step 2: Add `update_user_answers` method to `ChapterPrereadingContent`**

Add after `__post_init__` (around line 49), before the factory methods:

```python
def update_user_answers(self, answers: dict[int, str]) -> None:
    """Update user answers by question index. Mutates in place."""
    for index, answer_text in answers.items():
        if 0 <= index < len(self.questions):
            old_q = self.questions[index]
            self.questions[index] = PrereadingQuestion(
                question=old_q.question,
                answer=old_q.answer,
                user_answer=answer_text,
            )
```

Note: `ChapterPrereadingContent` is a non-frozen dataclass and `questions` is a mutable list, so in-place mutation is valid. `PrereadingQuestion` is frozen, so we replace the item.

- [ ] **Step 3: Update existing tests and add new tests**

**File:** `backend/tests/unit/domain/reading/entities/test_chapter_prereading_content.py`

Update the existing `_create` helper's `PrereadingQuestion` usage (already works since `user_answer` has a default). Add new tests:

```python
def test_prereading_question_default_user_answer() -> None:
    q = PrereadingQuestion(question="What?", answer="This.")
    assert q.user_answer == ""


def test_prereading_question_with_user_answer() -> None:
    q = PrereadingQuestion(question="What?", answer="This.", user_answer="My answer")
    assert q.user_answer == "My answer"


def test_update_user_answers() -> None:
    content = _create(
        questions=[
            PrereadingQuestion(question="Q1?", answer="A1"),
            PrereadingQuestion(question="Q2?", answer="A2"),
            PrereadingQuestion(question="Q3?", answer="A3"),
        ]
    )
    content.update_user_answers({0: "User A1", 2: "User A3"})
    assert content.questions[0].user_answer == "User A1"
    assert content.questions[1].user_answer == ""
    assert content.questions[2].user_answer == "User A3"


def test_update_user_answers_ignores_out_of_range() -> None:
    content = _create(
        questions=[PrereadingQuestion(question="Q1?", answer="A1")]
    )
    content.update_user_answers({0: "Valid", 5: "Invalid", -1: "Also invalid"})
    assert content.questions[0].user_answer == "Valid"
    assert len(content.questions) == 1
```

- [ ] **Step 4: Run domain tests**

Run: `cd backend && uv run pytest tests/unit/domain/reading/entities/test_chapter_prereading_content.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/domain/reading/entities/chapter_prereading_content.py backend/tests/unit/domain/reading/entities/test_chapter_prereading_content.py
git commit -m "feat: add user_answer field to PrereadingQuestion and update_user_answers method"
```

---

### Task 2: Update mapper to handle `user_answer`

**Files:**
- Modify: `backend/src/infrastructure/reading/mappers/chapter_prereading_mapper.py`

- [ ] **Step 1: Update `to_domain` to read `user_answer`**

Change line 20 from:
```python
PrereadingQuestion(question=q["question"], answer=q["answer"])
```
to:
```python
PrereadingQuestion(
    question=q["question"],
    answer=q["answer"],
    user_answer=q.get("user_answer", ""),
)
```

- [ ] **Step 2: Update `to_orm` to write `user_answer`**

Change line 33 from:
```python
questions = [{"question": q.question, "answer": q.answer} for q in entity.questions]
```
to:
```python
questions = [
    {"question": q.question, "answer": q.answer, "user_answer": q.user_answer}
    for q in entity.questions
]
```

- [ ] **Step 3: Run type check**

Run: `cd backend && uv run pyright src/infrastructure/reading/mappers/chapter_prereading_mapper.py`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add backend/src/infrastructure/reading/mappers/chapter_prereading_mapper.py
git commit -m "feat: update prereading mapper to handle user_answer field"
```

---

### Task 3: Update Pydantic schemas

**Files:**
- Modify: `backend/src/infrastructure/reading/schemas/chapter_prereading_schemas.py`

- [ ] **Step 1: Add `user_answer` to response schema and add request schemas**

```python
"""Pydantic schemas for chapter prereading content API."""

from datetime import datetime

from pydantic import BaseModel


class PrereadingQuestionResponse(BaseModel):
    """Response schema for a pre-reading question/answer pair."""

    question: str
    answer: str
    user_answer: str

class PrereadingAnswerUpdate(BaseModel):
    """Schema for a single answer update."""

    question_index: int
    user_answer: str


class UpdatePrereadingAnswersRequest(BaseModel):
    """Request schema for updating prereading answers."""

    answers: list[PrereadingAnswerUpdate]


class ChapterPrereadingResponse(BaseModel):
    """Response schema for chapter prereading content."""

    id: int
    chapter_id: int
    summary: str
    keypoints: list[str]
    questions: list[PrereadingQuestionResponse]
    generated_at: datetime

    model_config = {"from_attributes": True}


class BookPrereadingResponse(BaseModel):
    """Response schema for batch prereading content for a book."""

    items: list[ChapterPrereadingResponse]
```

- [ ] **Step 2: Update all router locations that construct `PrereadingQuestionResponse`**

In `backend/src/infrastructure/reading/routers/chapter_prereading.py`, update every place that creates `PrereadingQuestionResponse` to include `user_answer`. There are 3 locations (lines 64, 99, 145):

Change from:
```python
PrereadingQuestionResponse(question=q.question, answer=q.answer)
```
to:
```python
PrereadingQuestionResponse(question=q.question, answer=q.answer, user_answer=q.user_answer)
```

- [ ] **Step 3: Run type check**

Run: `cd backend && uv run pyright src/infrastructure/reading/schemas/chapter_prereading_schemas.py src/infrastructure/reading/routers/chapter_prereading.py`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add backend/src/infrastructure/reading/schemas/chapter_prereading_schemas.py backend/src/infrastructure/reading/routers/chapter_prereading.py
git commit -m "feat: add user_answer to prereading schemas and update router responses"
```

---

## Chunk 2: Backend Use Case + Endpoint

### Task 4: Create `UpdatePrereadingAnswersUseCase`

**Files:**
- Create: `backend/src/application/reading/use_cases/chapter_prereading/update_prereading_answers_use_case.py`

- [ ] **Step 1: Create the use case file**

```python
"""Use case for updating user answers on prereading questions."""

from src.application.library.protocols.chapter_repository import (
    ChapterRepositoryProtocol,
)
from src.application.reading.protocols.chapter_prereading_repository import (
    ChapterPrereadingRepositoryProtocol,
)
from src.domain.common.value_objects.ids import ChapterId, UserId
from src.domain.reading.entities.chapter_prereading_content import (
    ChapterPrereadingContent,
)
from src.exceptions import NotFoundError


class UpdatePrereadingAnswersUseCase:
    """Use case for updating user answers on prereading questions."""

    def __init__(
        self,
        prereading_repo: ChapterPrereadingRepositoryProtocol,
        chapter_repo: ChapterRepositoryProtocol,
    ) -> None:
        self.prereading_repo = prereading_repo
        self.chapter_repo = chapter_repo

    async def update_answers(
        self,
        chapter_id: ChapterId,
        user_id: UserId,
        answers: dict[int, str],
    ) -> ChapterPrereadingContent:
        """Update user answers for a chapter's prereading questions."""
        # Verify chapter exists and user owns it
        chapter = await self.chapter_repo.find_by_id(chapter_id, user_id)
        if not chapter:
            raise NotFoundError(f"Chapter {chapter_id.value} not found")

        # Load existing prereading content
        content = await self.prereading_repo.find_by_chapter_id(chapter_id)
        if not content:
            raise NotFoundError(
                f"No prereading content found for chapter {chapter_id.value}"
            )

        # Update answers and save
        content.update_user_answers(answers)
        return await self.prereading_repo.save(content)
```

- [ ] **Step 2: Run type check**

Run: `cd backend && uv run pyright src/application/reading/use_cases/chapter_prereading/update_prereading_answers_use_case.py`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add backend/src/application/reading/use_cases/chapter_prereading/update_prereading_answers_use_case.py
git commit -m "feat: add UpdatePrereadingAnswersUseCase"
```

---

### Task 5: Wire up DI container

**Files:**
- Modify: `backend/src/containers/reading.py`

- [ ] **Step 1: Add import for the new use case**

Add after the existing prereading use case imports (around line 22):

```python
from src.application.reading.use_cases.chapter_prereading.update_prereading_answers_use_case import (
    UpdatePrereadingAnswersUseCase,
)
```

- [ ] **Step 2: Add factory provider**

Add after `generate_chapter_prereading_use_case` (around line 289):

```python
    update_prereading_answers_use_case = providers.Factory(
        UpdatePrereadingAnswersUseCase,
        prereading_repo=chapter_prereading_repository,
        chapter_repo=chapter_repository,
    )
```

- [ ] **Step 3: Run type check**

Run: `cd backend && uv run pyright src/containers/reading.py`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add backend/src/containers/reading.py
git commit -m "feat: wire UpdatePrereadingAnswersUseCase into DI container"
```

---

### Task 6: Add PUT endpoint

**Files:**
- Modify: `backend/src/infrastructure/reading/routers/chapter_prereading.py`

- [ ] **Step 1: Add import for the new use case and request schema**

Add to the use case imports:
```python
from src.application.reading.use_cases.chapter_prereading.update_prereading_answers_use_case import (
    UpdatePrereadingAnswersUseCase,
)
```

Add to the schema imports (line 25-29):
```python
from src.infrastructure.reading.schemas.chapter_prereading_schemas import (
    BookPrereadingResponse,
    ChapterPrereadingResponse,
    PrereadingQuestionResponse,
    UpdatePrereadingAnswersRequest,
)
```

- [ ] **Step 2: Add the PUT endpoint**

Add after the `generate_chapter_prereading` endpoint (after line 112), before `book_prereading_router`:

```python
@router.put(
    "/{chapter_id}/prereading/answers",
    response_model=ChapterPrereadingResponse,
    status_code=status.HTTP_200_OK,
)
async def update_prereading_answers(
    chapter_id: int,
    body: UpdatePrereadingAnswersRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: UpdatePrereadingAnswersUseCase = Depends(
        inject_use_case(container.reading.update_prereading_answers_use_case)
    ),
) -> ChapterPrereadingResponse:
    """Update user answers for prereading questions."""
    try:
        answers = {a.question_index: a.user_answer for a in body.answers}
        result = await use_case.update_answers(
            chapter_id=ChapterId(chapter_id),
            user_id=UserId(current_user.id.value),
            answers=answers,
        )

        return ChapterPrereadingResponse(
            id=result.id.value,
            chapter_id=result.chapter_id.value,
            summary=result.summary,
            keypoints=result.keypoints,
            questions=[
                PrereadingQuestionResponse(
                    question=q.question, answer=q.answer, user_answer=q.user_answer
                )
                for q in result.questions
            ],
            generated_at=result.generated_at,
        )
    except DomainError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
```

Also add import for `NotFoundError` and handle it:

```python
from src.exceptions import NotFoundError
```

Update the except clause to also catch `NotFoundError`:
```python
    except (DomainError, NotFoundError) as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
```

- [ ] **Step 3: Run type check**

Run: `cd backend && uv run pyright src/infrastructure/reading/routers/chapter_prereading.py`
Expected: No errors

- [ ] **Step 4: Run full test suite**

Run: `cd backend && uv run pytest -x -q`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/infrastructure/reading/routers/chapter_prereading.py
git commit -m "feat: add PUT endpoint for updating prereading answers"
```

---

## Chunk 3: Frontend

### Task 7: Regenerate API types

- [ ] **Step 1: Regenerate orval types**

Run: `cd frontend && npm run generate-api`

This regenerates TypeScript types from the OpenAPI spec. The new endpoint and `user_answer` field will appear in generated files.

- [ ] **Step 2: Verify generated types include `user_answer`**

Check that `frontend/src/api/generated/model/prereadingQuestionResponse.ts` now includes `user_answer: string`.
Check that a new mutation hook exists for the PUT endpoint.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/generated/
git commit -m "chore: regenerate API types with prereading answer endpoint"
```

---

### Task 8: Update `PrereadingQuestionsSection` with auto-save

**Files:**
- Modify: `frontend/src/pages/BookPage/Structure/ChapterDetailDialog/PrereadingQuestionsSection.tsx`

- [ ] **Step 1: Add debounced auto-save logic**

Replace the full component implementation. Key changes:
- Initialize `answers` state from `prereadingSummary.questions[].user_answer`
- Use `useEffect` + `useRef` for debounced saving
- Call the new PUT mutation on debounced changes

```tsx
import type { ChapterPrereadingResponse } from '@/api/generated/model';
import {
  getGetBookPrereadingApiV1BooksBookIdPrereadingGetQueryKey,
  useGenerateChapterPrereadingApiV1ChaptersChapterIdPrereadingGeneratePost,
} from '@/api/generated/prereading/prereading';
// Import the new mutation hook — exact name depends on orval output.
// It will follow the pattern: useUpdatePrereadingAnswers...
// Check the generated file for the exact name after Task 7.
import { AIActionButton } from '@/components/buttons/AIActionButton.tsx';
import { AIFeature } from '@/components/features/AIFeature.tsx';
import { Box, CircularProgress, Stack, TextField, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useRef, useState } from 'react';
import { CollapsibleSection } from './CollapsibleSection.tsx';

interface PrereadingQuestionsSectionProps {
  chapterId: number;
  bookId: number;
  prereadingSummary?: ChapterPrereadingResponse;
}

export const PrereadingQuestionsSection = ({
  chapterId,
  bookId,
  prereadingSummary,
}: PrereadingQuestionsSectionProps) => {
  const queryClient = useQueryClient();
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const initializedRef = useRef(false);

  // Initialize answers from server data
  useEffect(() => {
    if (prereadingSummary && !initializedRef.current) {
      const serverAnswers: Record<number, string> = {};
      prereadingSummary.questions.forEach((q, index) => {
        if (q.user_answer) {
          serverAnswers[index] = q.user_answer;
        }
      });
      setAnswers(serverAnswers);
      initializedRef.current = true;
    }
  }, [prereadingSummary]);

  // Reset initialization when chapter changes
  useEffect(() => {
    initializedRef.current = false;
  }, [chapterId]);

  const { mutate: generate, isPending } =
    useGenerateChapterPrereadingApiV1ChaptersChapterIdPrereadingGeneratePost({
      mutation: {
        onSuccess: () => {
          initializedRef.current = false;
          void queryClient.invalidateQueries({
            queryKey: getGetBookPrereadingApiV1BooksBookIdPrereadingGetQueryKey(bookId),
          });
        },
      },
    });

  // Use the generated mutation hook for the PUT endpoint
  // The exact hook name will be generated by orval — update after Task 7
  const { mutate: saveAnswers } = useUpdatePrereadingAnswersApiV1ChaptersChapterIdPrereadingAnswersPut();

  const debouncedSave = useCallback(
    (updatedAnswers: Record<number, string>) => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
      debounceRef.current = setTimeout(() => {
        const answersList = Object.entries(updatedAnswers).map(([index, userAnswer]) => ({
          questionIndex: Number(index),
          userAnswer,
        }));
        if (answersList.length > 0) {
          saveAnswers({ chapterId, data: { answers: answersList } });
        }
      }, 1000);
    },
    [chapterId, saveAnswers]
  );

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  const handleAnswerChange = (index: number, value: string) => {
    setAnswers((prev) => {
      const updated = { ...prev, [index]: value };
      debouncedSave(updated);
      return updated;
    });
  };

  const handleGenerate = () => {
    generate({ chapterId });
  };

  return (
    <AIFeature>
      {isPending && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
          <CircularProgress size={24} />
        </Box>
      )}

      {!isPending && !prereadingSummary && (
        <Box sx={{ py: 1 }}>
          <AIActionButton text="Generate questions" onClick={handleGenerate} />
        </Box>
      )}

      {!isPending && prereadingSummary && prereadingSummary.questions.length === 0 && (
        <Typography variant="body2" color="text.secondary">
          No pre-reading questions available.
        </Typography>
      )}

      {!isPending && prereadingSummary && prereadingSummary.questions.length > 0 && (
        <CollapsibleSection title="Questions to think while reading" defaultExpanded>
          <Stack gap={1}>
            {prereadingSummary.questions.map((q, index) => (
              <Box key={index} sx={{ py: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 600, mb: 1.5 }}>
                  {q.question}
                </Typography>
                <TextField
                  multiline
                  minRows={2}
                  fullWidth
                  size="small"
                  placeholder="Write your answer..."
                  value={answers[index] ?? ''}
                  onChange={(e) => handleAnswerChange(index, e.target.value)}
                />
              </Box>
            ))}
          </Stack>
        </CollapsibleSection>
      )}
    </AIFeature>
  );
};
```

**Important:** The exact mutation hook name and its parameter shape depend on what orval generates in Task 7. After regenerating, check the generated file and adjust the import name and call signature accordingly.

- [ ] **Step 2: Run type check**

Run: `cd frontend && npm run type-check`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/BookPage/Structure/ChapterDetailDialog/PrereadingQuestionsSection.tsx
git commit -m "feat: add debounced auto-save for prereading answers"
```

---

### Task 9: Manual verification

- [ ] **Step 1: Start the backend**

Run: `cd backend && uv run uvicorn src.main:app --reload`

- [ ] **Step 2: Start the frontend**

Run: `cd frontend && npm run dev`

- [ ] **Step 3: Test the flow**

1. Open a book with chapters that have prereading content generated
2. Open chapter details, go to the "Before reading" tab
3. Type answers in the text fields
4. Navigate away and back — answers should persist
5. Check browser network tab — PUT requests should fire ~1s after typing stops

- [ ] **Step 4: Final commit if any adjustments needed**
