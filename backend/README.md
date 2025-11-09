# Inkwell Backend

Backend API for Inkwell - a self-hosted web app to sync highlights from KOReader to a server.

## Features

- FastAPI web framework
- SQLAlchemy 2.0 ORM
- Alembic database migrations
- Poetry dependency management
- Ruff linting
- Black code formatting
- pytest testing framework
- Strong typing with mypy

## Setup

1. Install dependencies:
```bash
poetry install
```

2. Copy environment variables:
```bash
cp .env.example .env
```

3. Run migrations:
```bash
poetry run alembic upgrade head
```

4. Run the development server:
```bash
poetry run uvicorn inkwell.main:app --reload
```

## Development

### Running tests
```bash
poetry run pytest
```

### Linting
```bash
poetry run ruff check .
poetry run ruff check --fix .  # Auto-fix issues
```

### Formatting
```bash
poetry run black .
```

### Type checking
```bash
poetry run mypy inkwell
```

### Creating migrations
```bash
poetry run alembic revision --autogenerate -m "description"
poetry run alembic upgrade head
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc
