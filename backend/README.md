# crossbill Backend

Backend API for crossbill - a self-hosted web app to sync highlights from KOReader to a server.

## Features

- FastAPI web framework
- SQLAlchemy 2.0 ORM
- PostgreSQL database with Docker support
- Alembic database migrations
- Poetry dependency management
- Hexagonal architecture
- Ruff linting
- pytest testing framework
- Strong typing with pyright

## Prerequisites

- Python 3.11+
- Poetry
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
poetry install
```

### 3. Copy environment variables

```bash
cp .env.example .env
```

```

### 4. Run migrations

```bash
poetry run alembic upgrade head
```

### 5. Run the development server

```bash
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 
```

The API will be available at http://localhost:8000

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
poetry run pytest
```

### Linting
```bash
poetry run ruff check .
poetry run ruff check --fix .  # Auto-fix issues
```

### Formatting
```bash
poetry run ruff format
```

### Type checking
```bash
poetry run pyright
```

### Creating migrations
```bash
poetry run alembic revision --autogenerate -m "description"
poetry run alembic upgrade head
```

## Create password hash to be saved to the database from password:
```
 poetry run python -c "from argon2 import PasswordHasher; ph = PasswordHasher(); print(ph.hash('your_password_here'))"
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc
