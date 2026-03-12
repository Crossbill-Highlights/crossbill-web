# Batch AI Processing Framework — Design Spec

## Problem

Crossbill's AI features (prereading, flashcards, summaries) currently execute inline during HTTP requests. For bulk operations — such as generating prereading for all chapters in a book or producing embedding vectors for semantic search — this is too slow and blocks the user. A background processing framework is needed.

## Goals

- Queue many AI tasks and process them in the background
- Track progress so the frontend can show status on page load
- Support cancellation of in-progress batch jobs
- Keep provider/model configuration as an infrastructure concern, invisible to the application layer
- Design for future extension: new task types (embeddings), provider batch APIs (Anthropic/OpenAI), different models per task

## Non-Goals (for now)

- Active polling or push notifications (WebSocket/SSE)
- Anthropic or OpenAI batch API integration (design accommodates it, but not built yet)
- Embedding generation (first use case is batch prereading only)

## Stack Decision

**SAQ with PostgreSQL backend.** Chosen because:

- PostgreSQL is already in the stack — no new infrastructure
- SAQ is async-native, fits the async FastAPI + SQLAlchemy stack
- Provides durable jobs, retry support, and cancellation out of the box
- Worker runs as a second container using the same Docker image

Alternatives considered and rejected:
- **In-process asyncio tasks**: jobs don't survive app restarts
- **DB-polling custom worker**: reinvents what SAQ provides
- **Redis-backed queues (ARQ, TaskIQ)**: unnecessary infrastructure addition

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     API Layer                            │
│  POST /api/books/{id}/batch/prereading                  │
│  GET  /api/batch-jobs/{id}                              │
│  POST /api/batch-jobs/{id}/cancel                       │
└────────────────┬────────────────────────────────────────┘
                 │ delegates to use cases
                 ▼
┌─────────────────────────────────────────────────────────┐
│              Application Layer                           │
│  CreateBatchPrereadingUseCase                            │
│  GetBatchJobStatusUseCase                                │
│  CancelBatchJobUseCase                                   │
│  (works with domain entities + protocols only)           │
└────────────────┬────────────────────────────────────────┘
                 │
    ┌────────────┴────────────┐
    ▼                         ▼
┌──────────┐        ┌──────────────────┐
│ BatchJob  │        │   SAQ Queue      │
│ BatchItem │        │ (PostgreSQL)     │
│ (DB)      │        │                  │
└──────────┘        └────────┬─────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│              Worker Process                              │
│  SAQ task: process_batch_job(batch_job_id)               │
│    → loads job + items from DB                           │
│    → selects processor by job_type                       │
│    → runs items concurrently (semaphore-throttled)       │
│    → retries failures (3 attempts, exponential backoff)  │
│    → checks for cancellation between items               │
│    → updates progress in DB                              │
└─────────────────────────────────────────────────────────┘
```

## Domain Layer

### BatchJob Entity

Located in `domain/batch/entities/batch_job.py`.

```python
@dataclass
class BatchJob:
    id: int
    user_id: UserId
    book_id: int
    job_type: str              # "prereading", "embedding" (future)
    status: BatchJobStatus     # pending, processing, completed, failed, cancelled
    total_items: int
    completed_items: int
    failed_items: int
    created_at: datetime
    completed_at: datetime | None
```

```python
class BatchJobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

### BatchItem Entity

Located in `domain/batch/entities/batch_item.py`.

```python
@dataclass
class BatchItem:
    id: int
    batch_job_id: int
    entity_type: str           # "chapter", "highlight"
    entity_id: int
    status: BatchItemStatus    # pending, processing, succeeded, failed
    attempts: int
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None
```

```python
class BatchItemStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
```

## Application Layer

### Protocol

Located in `application/batch/protocols/batch_job_service.py`.

```python
class BatchJobServiceProtocol(Protocol):
    async def enqueue_batch_prereading(
        self, user_id: UserId, book_id: int
    ) -> BatchJob: ...

    async def get_batch_job_status(
        self, user_id: UserId, job_id: int
    ) -> BatchJob: ...

    async def cancel_batch_job(
        self, user_id: UserId, job_id: int
    ) -> BatchJob: ...
```

### Use Cases

Located in `application/batch/use_cases/`.

- **`CreateBatchPrereadingUseCase`** — validates user owns the book, determines which chapters still need prereading (skips those that already have it), calls `enqueue_batch_prereading`. Returns the created `BatchJob`.
- **`GetBatchJobStatusUseCase`** — returns current `BatchJob` state. Used by frontend on page load.
- **`CancelBatchJobUseCase`** — marks job as cancelled, stops remaining work.

Use cases work with domain entities and protocols only. No awareness of SAQ, providers, or concurrency.

## Infrastructure Layer

### ORM Models

Located in `infrastructure/batch/models.py`.

**`batch_jobs` table:**
| Column | Type | Notes |
|---|---|---|
| id | Integer, PK | auto-increment |
| user_id | Integer, FK → users | cascade delete |
| book_id | Integer, FK → books | cascade delete |
| job_type | VARCHAR | e.g., "prereading" |
| status | VARCHAR | indexed |
| total_items | Integer | default 0 |
| completed_items | Integer | default 0 |
| failed_items | Integer | default 0 |
| created_at | TIMESTAMP | |
| completed_at | TIMESTAMP | nullable |

Index: `(user_id, job_type, status)` — for checking if a running job already exists.

**`batch_items` table:**
| Column | Type | Notes |
|---|---|---|
| id | Integer, PK | auto-increment |
| batch_job_id | Integer, FK → batch_jobs | cascade delete, indexed |
| entity_type | VARCHAR | e.g., "chapter" |
| entity_id | Integer | |
| status | VARCHAR | |
| attempts | Integer | default 0 |
| error_message | TEXT | nullable |
| created_at | TIMESTAMP | |
| completed_at | TIMESTAMP | nullable |

### BatchJobService (Infrastructure Implementation)

Located in `infrastructure/batch/batch_job_service.py`. Implements `BatchJobServiceProtocol`.

- `enqueue_batch_prereading`: creates `BatchJob` + `BatchItem` rows in DB, enqueues a SAQ task with the job ID
- `get_batch_job_status`: loads and returns the `BatchJob`
- `cancel_batch_job`: updates job status to `cancelled`

### Batch Processors

Located in `infrastructure/batch/processors/`.

Each processor handles one task type. A processor is a class with:

```python
class PrereadingBatchProcessor:
    async def process_item(self, item: BatchItem) -> None:
        # Extract chapter text, call AI, save prereading result
        ...
```

The `PrereadingBatchProcessor` reuses existing infrastructure services (text extraction, AI service) but constructs them with batch-specific model/provider configuration from environment variables.

### SAQ Worker

Located in `infrastructure/batch/worker.py`.

Single SAQ task function `process_batch_job(ctx, batch_job_id)`:

1. Load `BatchJob` and pending `BatchItem`s from DB
2. Look up processor by `job.job_type`
3. Mark job as `processing`
4. Run items concurrently using `asyncio.Semaphore(max_concurrency)` + `asyncio.TaskGroup`
5. Per item:
   - Check if job is cancelled → stop early if so
   - Call `processor.process_item(item)`
   - On success: mark item `succeeded`, increment `completed_items`
   - On failure: retry up to 3 times with exponential backoff, then mark `failed`, increment `failed_items`
   - Update job progress in DB after each item
6. When done: mark job `completed` (or `failed` if all items failed)

### Configuration

Environment variables for batch AI (infrastructure concern only):

| Variable | Default | Purpose |
|---|---|---|
| `BATCH_AI_PROVIDER` | falls back to `AI_PROVIDER` | AI provider for batch tasks |
| `BATCH_AI_MODEL_NAME` | falls back to `AI_MODEL_NAME` | Model for batch tasks |
| `BATCH_MAX_CONCURRENCY` | `5` | Max parallel AI requests per job |

Future task types add their own variables (e.g., `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL_NAME`).

## API Endpoints

All guarded by `@require_ai_enabled`.

### `POST /api/books/{book_id}/batch/prereading`

Creates a batch job to generate prereading for all chapters that don't already have it.

**Response** (201 Created):
```json
{ "job_id": 1, "status": "pending", "total_items": 25 }
```

**Error cases:**
- 404: book not found or not owned by user
- 409: a prereading batch job is already running for this book

### `GET /api/batch-jobs/{job_id}`

Returns current job state. Called by frontend on page load.

**Response** (200):
```json
{
  "job_id": 1,
  "job_type": "prereading",
  "status": "processing",
  "total_items": 25,
  "completed_items": 12,
  "failed_items": 1,
  "created_at": "2026-03-12T10:00:00Z",
  "completed_at": null
}
```

**Error cases:**
- 404: job not found or not owned by user

### `POST /api/batch-jobs/{job_id}/cancel`

Cancels a running batch job.

**Response** (200): updated job status.

**Error cases:**
- 404: job not found or not owned by user
- 409: job is already completed/cancelled

## Worker Deployment

Second container in `docker-compose.yml` using the same image:

```yaml
worker:
  image: tumetsu/crossbill:latest
  command: uv run saq src.infrastructure.batch.worker.settings
  depends_on:
    postgres:
      condition: service_healthy
  environment:
    - DATABASE_URL=postgresql://...
    - BATCH_AI_PROVIDER=anthropic
    - BATCH_AI_MODEL_NAME=claude-sonnet-4-20250514
    - BATCH_MAX_CONCURRENCY=5
```

For local development: `cd backend && uv run saq src.infrastructure.batch.worker.settings`

## File Structure

```
backend/src/
├── domain/batch/
│   ├── entities/
│   │   ├── batch_job.py
│   │   └── batch_item.py
│   └── protocols/
│       └── batch_job_repository.py
│
├── application/batch/
│   ├── protocols/
│   │   └── batch_job_service.py
│   └── use_cases/
│       ├── create_batch_prereading_use_case.py
│       ├── get_batch_job_status_use_case.py
│       └── cancel_batch_job_use_case.py
│
├── infrastructure/batch/
│   ├── models.py
│   ├── mappers.py
│   ├── repositories/
│   │   └── batch_job_repository.py
│   ├── batch_job_service.py
│   ├── processors/
│   │   └── prereading_batch_processor.py
│   ├── worker.py
│   └── routers/
│       └── batch_jobs.py
```

## Future Extensions

This section documents how to extend the batch processing framework for future needs. The key abstraction principle: **the application layer sees task-specific methods (e.g., `enqueue_batch_prereading`), while all provider, model, concurrency, and execution strategy concerns are contained in the infrastructure layer.**

### Adding a New Batch Task Type (e.g., Embeddings)

1. **Create a new processor** in `infrastructure/batch/processors/` (e.g., `embedding_batch_processor.py`) with a `process_item` method
2. **Register the processor** in the worker's processor lookup by `job_type`
3. **Add a new use case** in `application/batch/use_cases/` (e.g., `create_batch_embeddings_use_case.py`)
4. **Add a method** to `BatchJobServiceProtocol` (e.g., `enqueue_batch_embeddings`)
5. **Add environment variables** for the new task type's model/provider config (e.g., `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL_NAME`)
6. **Add an API endpoint** if needed

The SAQ worker, job/item tracking, retry logic, cancellation, and progress reporting are all shared — no changes needed to the framework.

### Adding Provider Batch API Support (Anthropic/OpenAI)

Currently, the worker runs items concurrently using individual AI calls. To add provider batch API support (50% cost savings):

1. **Introduce an execution strategy abstraction** at the infrastructure level — e.g., a `BatchExecutionStrategy` protocol with an `execute(items, processor)` method
2. **Implement provider-specific strategies**: `AnthropicBatchStrategy` (submits to Message Batches API, polls for completion), `OpenAIBatchStrategy` (uploads JSONL, creates batch, polls)
3. **Add a strategy selector** that checks the provider config and picks the right strategy
4. **Modify the SAQ task** to use the selected strategy instead of the current semaphore-based concurrency

The domain and application layers don't change. The strategy abstraction lives entirely within infrastructure.

### Processor-Level Concerns

Each processor is responsible for:
- Knowing how to process a single item for its task type
- Constructing its AI service with the correct model/provider from environment variables
- Reusing existing infrastructure services where possible (e.g., text extraction)

Processors do NOT manage concurrency, retries, or progress tracking — the worker handles all of that.

### Configuration Hierarchy

For any batch task, the model/provider resolution follows this chain:
1. Task-type-specific env var (e.g., `EMBEDDING_PROVIDER`) — highest priority
2. Batch-level env var (`BATCH_AI_PROVIDER`) — fallback
3. Main app env var (`AI_PROVIDER`) — final fallback
