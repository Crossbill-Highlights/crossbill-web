# Prereading Answer Persistence

## Problem

Users can type answers to pre-reading questions in the UI, but answers are lost on navigation because they only live in React state. Answers should persist to the database.

## Design

### Storage

The `questions` JSONB column in `chapter_prereading_contents` already stores `[{"question": "...", "answer": "..."}]`. We add a `user_answer` key to each dict: `{"question": "...", "answer": "...", "user_answer": "..."}`. No migration needed — JSONB accepts the new key naturally. The existing `answer` field is reserved for AI example answers.

### Domain Layer

Add `user_answer: str = ""` to the `PrereadingQuestion` dataclass. Add a method on `ChapterPrereadingContent` to update user answers by index.

### Infrastructure Layer

Update `ChapterPrereadingMapper` to read/write `user_answer` from JSONB dicts (defaulting to `""` when absent).

### Application Layer

New `UpdatePrereadingAnswersUseCase`:
- Input: chapter_id, user_id, list of `(question_index, user_answer)` pairs
- Loads existing prereading content, validates chapter ownership
- Updates `user_answer` on matching questions, ignores out-of-range indices
- Saves and returns updated entity

### API Layer

New endpoint: `PUT /api/v1/chapters/{chapter_id}/prereading/answers`

Request body:
```json
{
  "answers": [
    {"question_index": 0, "user_answer": "My thoughts on..."},
    {"question_index": 2, "user_answer": "I think..."}
  ]
}
```

Response: `ChapterPrereadingResponse` (existing schema, updated to include `user_answer` in each question).

New Pydantic schemas:
- `PrereadingAnswerUpdate`: `question_index: int`, `user_answer: str`
- `UpdatePrereadingAnswersRequest`: `answers: list[PrereadingAnswerUpdate]`

Update `PrereadingQuestionResponse` to include `user_answer: str`.

### Frontend

After regenerating API types with orval:
- Initialize `answers` state from `prereadingSummary.questions[].userAnswer`
- Add debounced (~1 second) mutation that calls the new PUT endpoint when answers change
- Send only changed answers or all answers (payload is small enough that sending all is fine)

### Error Handling

- 404 if chapter has no prereading content
- 400 if question_index is out of range
- Standard auth checks via existing patterns

## What's NOT Changing

- Generate endpoint behavior (sets `user_answer: ""` on new questions)
- Existing `answer` field semantics
- Database schema (no migration)
