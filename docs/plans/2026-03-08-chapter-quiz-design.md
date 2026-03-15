# Chapter Quiz Feature Design

## Overview

A conversational quiz feature that helps users recall chapter contents after reading. The AI asks questions about the chapter, evaluates answers, corrects misunderstandings, and provides a summary at the end.

## User Flow

1. User opens a chapter in the `ChapterDetailDialog` (structure view)
2. Near the prereading summary, user clicks "Quiz Me" button
3. A full-screen chat modal (`QuizChatDialog`) opens
4. Backend creates a quiz session, loads the full chapter text, and generates the first question
5. User answers in free text; AI evaluates, explains, and asks the next question
6. After 5 questions (configurable in backend code), AI provides a brief summary of how the user did
7. User can request clarifications at any point without it counting as a quiz question
8. User closes the modal when done — session is fire-and-forget (stored but not surfaced in UI)

## Backend

### Data Model

**New ORM model: `QuizSessionModel`** (`models.py`)

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | Auto-increment |
| `user_id` | Integer FK → users | Indexed |
| `chapter_id` | Integer FK → chapters | Indexed |
| `message_history` | JSON | Pydantic-ai messages serialized via `ModelMessagesTypeAdapter` |
| `question_count` | Integer | Target number of questions (default 5) |
| `created_at` | DateTime(tz) | server_default=now |
| `completed_at` | DateTime(tz) | Nullable, set when quiz finishes |

**New domain entity: `QuizSession`** (`domain/learning/entities/quiz_session.py`)

Pure domain object with: id, user_id, chapter_id, message_history (raw list for JSON serialization), question_count, created_at, completed_at.

### AI Agent

**New agent factory** in `ai_agents.py`:

`get_quiz_agent() -> Agent[None, str]` with `output_type=str` (free-form text responses).

System instructions:
- Act as a reading comprehension tutor for the chapter content
- Ask one question at a time
- Evaluate user answers, correct misunderstandings with explanations referencing the chapter
- Track progress toward the target question count
- Handle clarification requests gracefully without counting them as quiz questions
- After all questions, provide a brief summary of the user's understanding

The chapter content is passed as the initial user message when the session is created. Pydantic-ai preserves it in the message history, so it's available as context for all subsequent turns.

### AIService Methods

**`start_quiz(chapter_content: str, question_count: int, usage_context: AIUsageContext) -> tuple[str, list]`**
- Creates and runs the quiz agent with the chapter text + instruction about question count
- Returns (first AI message, serialized message history via `ModelMessagesTypeAdapter`)
- Tracks token usage via existing `_save_usage`

**`continue_quiz(user_message: str, message_history: list, usage_context: AIUsageContext) -> tuple[str, list]`**
- Deserializes message history via `ModelMessagesTypeAdapter`
- Runs the agent with the user's reply and the deserialized history
- Returns (AI response text, updated serialized message history)
- Tracks token usage per turn

### Repository

**`QuizSessionRepository`** (`infrastructure/learning/repositories/quiz_session_repository.py`)
- `create(session: QuizSession) -> QuizSession`
- `get_by_id(session_id: int, user_id: int) -> QuizSession | None`
- `update_message_history(session_id: int, message_history: list, completed_at: datetime | None) -> None`

### Use Cases

Located in `application/learning/use_cases/quiz/`.

**`StartQuizSessionUseCase`**
- Input: chapter_id, user_id
- Fetches chapter content via existing text extraction pipeline (chapter → book → file → epub extraction)
- Creates a `QuizSession` domain entity
- Calls `ai_service.start_quiz()` with chapter content
- Persists the session with initial message history
- Returns session ID + first question text

**`SendQuizMessageUseCase`**
- Input: session_id, user_message, user_id
- Loads session from repository
- Calls `ai_service.continue_quiz()` with user message and stored history
- Updates persisted message history
- Returns AI response text + completion status

### API Endpoints

New router: `infrastructure/learning/routers/quiz_sessions.py`

**`POST /api/v1/chapters/{chapter_id}/quiz-sessions`**
- Creates a new quiz session
- Response: `{ session_id: int, message: str }`
- Gated behind `require_ai_enabled`
- AI usage tracked with `task_type="quiz"`, `entity_type="chapter"`

**`POST /api/v1/quiz-sessions/{session_id}/messages`**
- Sends a user message to an existing quiz session
- Request body: `{ message: str }`
- Response: `{ message: str, is_complete: bool }`
- Gated behind `require_ai_enabled`

### DI Container

Register in `core.py`:
- `quiz_session_repository`
- `start_quiz_session_use_case`
- `send_quiz_message_use_case`

### AI Usage Tracking

Each AI call (both `start_quiz` and `continue_quiz`) records usage via the existing `AIUsageRepository` with:
- `task_type="quiz"`
- `entity_type="chapter"`
- `entity_id=chapter_id`

## Frontend

### "Quiz Me" Button

- Located inside `ChapterDetailDialog`, near the `PrereadingSummary` section
- Uses existing `AIActionButton` component
- Wrapped in `AIFeature` for feature flag gating
- On click: opens `QuizChatDialog`

### QuizChatDialog Component

New component: `pages/BookPage/Structure/ChapterDetailDialog/QuizChatDialog.tsx`

**Layout:**
- Full-screen MUI `Dialog`
- Header: chapter name + close button
- Body: scrollable message area
- Footer: text input + send button

**Message display:**
- AI messages: left-aligned bubbles, rendered with `react-markdown`
- User messages: right-aligned bubbles
- Loading indicator while waiting for AI response
- Auto-scroll to latest message on new messages

**State management:**
- Local state for displayed messages array
- Local state for session ID (set after creation)
- TanStack Query mutation for creating session (`POST /chapters/{id}/quiz-sessions`)
- TanStack Query mutation for sending messages (`POST /quiz-sessions/{id}/messages`)

**Lifecycle:**
- Modal opens → create session mutation fires → loading state → first question appears
- User types + sends → mutation fires → loading → AI response appended
- Repeats until AI signals completion
- User closes modal → component unmounts, no cleanup needed

### Generated API Client

After adding the backend endpoints, run Orval to generate the TanStack Query hooks:
- `useCreateQuizSession` mutation
- `useSendQuizMessage` mutation

## Database Migration

New Alembic migration to create the `quiz_sessions` table with the schema described above.

## Configuration

- `QUIZ_DEFAULT_QUESTION_COUNT = 5` — configurable constant in backend code, not exposed to UI
