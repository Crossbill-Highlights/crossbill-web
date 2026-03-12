# crossbill Backend

Backend API for crossbill - a self-hosted web app to sync highlights from KOReader to a server.

## Features

- FastAPI web framework
- SQLAlchemy 2.0 ORM
- PostgreSQL database with Docker support
- Alembic database migrations
- uv dependency management
- Hexagonal architecture
- Ruff linting
- pytest testing framework
- Strong typing with pyright

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Docker and Docker Compose (for PostgreSQL)

## Setup

### 1. Start PostgreSQL Database

```bash
docker-compose up -d
```

This starts a PostgreSQL 16 container with the following configuration:
- Host: localhost
- Port: 5432
- Database: crossbill
- User: crossbill
- Password: crossbill_dev_password

### 2. Install dependencies

```bash
uv sync
```

### 3. Copy environment variables

```bash
cp .env.example .env
```

```

### 4. Run migrations

```bash
uv run alembic upgrade head
```

### 5. Run the development server

```bash
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000

### 6. Run the batch worker (optional)

The batch worker processes background AI tasks (e.g. batch chapter prereading generation). It requires AI to be enabled and uses the same PostgreSQL database as the main app for its job queue.

```bash
uv run saq src.infrastructure.batch.worker.settings
```

You can optionally configure the worker with these environment variables:

- `BATCH_AI_PROVIDER` — AI provider for batch tasks (defaults to main `AI_PROVIDER`)
- `BATCH_AI_MODEL_NAME` — model name for batch tasks (defaults to main `AI_MODEL_NAME`)
- `BATCH_MAX_CONCURRENCY` — max concurrent AI calls per job (default: `5`)

## Docker Commands

### Stop the database
```bash
docker-compose stop
```

### Start the database
```bash
docker-compose start
```

### Stop and remove containers (data is preserved in volumes)
```bash
docker-compose down
```

### Remove containers and volumes (⚠️ deletes all data)
```bash
docker-compose down -v
```

### View database logs
```bash
docker-compose logs -f postgres
```

### Access PostgreSQL CLI
```bash
docker-compose exec postgres psql -U crossbill -d crossbill
```

## Development

### Running tests
```bash
uv run pytest
```

### Linting
```bash
uv run ruff check .
uv run ruff check --fix .  # Auto-fix issues
```

### Formatting
```bash
uv run ruff format
```

### Type checking
```bash
uv run pyright
```

### Creating migrations
```bash
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

## Create password hash to be saved to the database from password:
```
 uv run python -c "from argon2 import PasswordHasher; ph = PasswordHasher(); print(ph.hash('your_password_here'))"
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc
