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
- SAQ's PostgreSQL backend uses psycopg 3, the same async driver this project already uses

SAQ's PostgreSQL backend is newer than its Redis backend (introduced mid-2024, with stability improvements through 2025-2026). It is production-ready but less battle-tested. If stability issues arise, switching to the Redis backend is a straightforward change (add Redis to docker-compose, change the queue URL).

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
│    → checks for cancellation before launching each item  │
│    → updates progress in DB                              │
└─────────────────────────────────────────────────────────┘
```

## Domain Layer

### BatchJob Entity

Located in `domain/batch/entities/batch_job.py`.

Uses typed IDs consistent with the existing codebase pattern (`EntityId` subclasses in `domain/common/value_objects/ids.py`).

```python
@dataclass
class BatchJob:
    id: BatchJobId
    user_id: UserId
    book_id: BookId
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

A job with `status == COMPLETED` means all items were attempted. The frontend uses `failed_items > 0` to distinguish clean completion from partial failure — no separate `COMPLETED_WITH_ERRORS` status is needed. The `FAILED` status is reserved for job-level infrastructure errors (e.g., worker crash, database unavailable) — not for "all items failed," which is still `COMPLETED` with `failed_items == total_items`.

### BatchItem Entity

Located in `domain/batch/entities/batch_item.py`.

```python
@dataclass
class BatchItem:
    id: BatchItemId
    batch_job_id: BatchJobId
    entity_type: str           # "chapter", "highlight"
    entity_id: int             # polymorphic reference, kept as raw int intentionally
    status: BatchItemStatus    # pending, processing, succeeded, failed
    attempts: int
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None
```

`entity_id` is a raw `int` because it references different entity types (chapters, highlights, etc.) depending on `entity_type`. A typed ID would be misleading here.

```python
class BatchItemStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
```

New typed IDs `BatchJobId` and `BatchItemId` are added to `domain/common/value_objects/ids.py` following the existing `EntityId` subclass pattern.

## Application Layer

### Protocols

Located in `application/batch/protocols/`.

**`BatchJobRepositoryProtocol`** (`application/batch/protocols/batch_job_repository.py`) — data access, consistent with how all other repository protocols are placed in the application layer:

```python
class BatchJobRepositoryProtocol(Protocol):
    async def save_job(self, job: BatchJob) -> BatchJob: ...
    async def save_item(self, item: BatchItem) -> BatchItem: ...
    async def get_job(self, job_id: BatchJobId) -> BatchJob | None: ...
    async def get_job_items(self, job_id: BatchJobId) -> list[BatchItem]: ...
    async def find_active_job(
        self, user_id: UserId, book_id: BookId, job_type: str
    ) -> BatchJob | None: ...
```

**`BatchQueueServiceProtocol`** (`application/batch/protocols/batch_queue_service.py`) — queue operations, separated from data access:

```python
class BatchQueueServiceProtocol(Protocol):
    async def enqueue_job(self, job_id: BatchJobId) -> None: ...
    async def cancel_job(self, job_id: BatchJobId) -> None: ...
```

This separation keeps data access (repository) and side effects (queue enqueueing) in distinct protocols, consistent with the codebase's existing patterns and making testing easier.

### Use Cases

Located in `application/batch/use_cases/`.

- **`CreateBatchPrereadingUseCase`** — validates user owns the book, **checks for an existing pending/processing batch job for the same book** (raises domain error if one exists, resulting in 409 at the API layer), determines which chapters still need prereading (skips those that already have it), creates `BatchJob` + `BatchItem` entities via the repository, calls `enqueue_job` on the queue service. Returns the created `BatchJob`.
- **`GetBatchJobStatusUseCase`** — loads and returns current `BatchJob` state via the repository. Used by frontend on page load.
- **`CancelBatchJobUseCase`** — loads job, validates it's still active, marks as cancelled via the repository, calls `cancel_job` on the queue service.

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

Index: `(user_id, book_id, job_type, status)` — for the `find_active_job` duplicate prevention query.

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

### Repository Implementation

Located in `infrastructure/batch/repositories/batch_job_repository.py`. Implements `BatchJobRepositoryProtocol`.

Handles all ORM ↔ domain entity conversion via `BatchJobMapper` and `BatchItemMapper` in `infrastructure/batch/mappers.py`.

### BatchQueueService (Infrastructure Implementation)

Located in `infrastructure/batch/batch_queue_service.py`. Implements `BatchQueueServiceProtocol`.

- `enqueue_job`: enqueues a SAQ task with the job ID
- `cancel_job`: calls SAQ's abort/cancel mechanism for the task

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

#### Worker Bootstrapping

The worker runs as a separate process and needs its own infrastructure setup:

- Initializes its own async SQLAlchemy engine and session factory using `DATABASE_URL` (reusing the existing `database.py` module)
- Constructs dependencies (repositories, processors, AI services) directly — does **not** reuse the FastAPI DI container, since it runs outside the FastAPI request lifecycle
- SAQ lifecycle hooks manage setup and teardown:
  - `startup`: initialize database engine, create session factory, construct processors
  - `shutdown`: dispose database engine
  - `before_process`: create a new async session for each job
  - `after_process`: close the session

#### Task Execution

Single SAQ task function `process_batch_job(ctx, batch_job_id)`:

1. Load `BatchJob` and pending `BatchItem`s from DB
2. Look up processor by `job.job_type`
3. Mark job as `processing`
4. Process items concurrently using `asyncio.Semaphore(max_concurrency)` + `asyncio.TaskGroup`:
   - Items are launched from a loop that checks cancellation **before acquiring the semaphore** for each new item
   - If the job is cancelled, the loop stops launching new items; in-flight items are allowed to complete naturally
   - This means cancellation is cooperative: no in-flight AI calls are interrupted, but no new ones start
5. Per item:
   - Call `processor.process_item(item)`
   - On success: mark item `succeeded`, increment `completed_items`
   - On failure: release semaphore, wait with exponential backoff, re-acquire semaphore, retry (up to 3 attempts). After all retries exhausted, mark `failed`, increment `failed_items`
   - Update item status and job progress counters atomically (same transaction) to keep progress display consistent
6. When done: mark job `completed` (all items attempted, regardless of individual outcomes). Mark `failed` only for job-level infrastructure errors (not item-level failures)

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
- 409: a prereading batch job is already pending/processing for this book

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
│   └── entities/
│       ├── batch_job.py          # BatchJob, BatchJobStatus
│       └── batch_item.py         # BatchItem, BatchItemStatus
│
├── domain/common/value_objects/
│   └── ids.py                    # + BatchJobId, BatchItemId (added to existing file)
│
├── application/batch/
│   ├── protocols/
│   │   ├── batch_job_repository.py   # BatchJobRepositoryProtocol
│   │   └── batch_queue_service.py    # BatchQueueServiceProtocol
│   └── use_cases/
│       ├── create_batch_prereading_use_case.py
│       ├── get_batch_job_status_use_case.py
│       └── cancel_batch_job_use_case.py
│
├── infrastructure/batch/
│   ├── models.py                 # ORM models for batch_jobs, batch_items
│   ├── mappers.py                # ORM ↔ domain entity mapping
│   ├── repositories/
│   │   └── batch_job_repository.py   # SQLAlchemy implementation
│   ├── batch_queue_service.py    # SAQ queue implementation
│   ├── processors/
│   │   └── prereading_batch_processor.py
│   ├── worker.py                 # SAQ worker config, lifecycle hooks, task function
│   └── routers/
│       └── batch_jobs.py         # API endpoints
```

## Future Extensions

This section documents how to extend the batch processing framework for future needs. The key abstraction principle: **the application layer sees task-specific methods (e.g., `enqueue_batch_prereading`), while all provider, model, concurrency, and execution strategy concerns are contained in the infrastructure layer.**

### Adding a New Batch Task Type (e.g., Embeddings)

1. **Create a new processor** in `infrastructure/batch/processors/` (e.g., `embedding_batch_processor.py`) with a `process_item` method
2. **Register the processor** in the worker's processor lookup by `job_type`
3. **Add a new use case** in `application/batch/use_cases/` (e.g., `create_batch_embeddings_use_case.py`)
4. **Add a method** to `BatchQueueServiceProtocol` or reuse the generic `enqueue_job`
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
