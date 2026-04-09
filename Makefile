.PHONY: help test dev-app dev-worker migrate migrate-new lint format release-nightly empty-s3-bucket reset-db

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Backend commands (run from repo root)

test: ## Run backend tests
	cd backend && uv run pytest

dev-app: ## Run the backend dev server
	cd backend && uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

dev-worker: ## Run the SAQ background worker
	cd backend && uv run saq src.worker.worker_settings

migrate: ## Run database migrations (alembic upgrade head)
	cd backend && uv run alembic upgrade head

migrate-new: ## Create a new migration (usage: make migrate-new msg="description")
	cd backend && uv run alembic revision --autogenerate -m "$(msg)"

lint: ## Run ruff linter and pyright type checker on backend
	cd backend && uv run ruff check src tests
	cd backend && uv run pyright

format: ## Format backend code with ruff
	cd backend && uv run ruff format src tests

release-nightly: ## Build and push nightly Docker image to Docker Hub
	./scripts/build-for-docker-hub.sh

empty-s3-bucket: ## Remove all objects from the local S3 bucket
	aws --endpoint-url http://localhost:3900 s3 rm s3://crossbill-files --recursive

reset-db: ## Reset the database (removes volume and re-runs migrations)
	docker compose -f docker-compose.dev.yml down -v postgres
	docker compose -f docker-compose.dev.yml up -d postgres
	@echo "Waiting for PostgreSQL to accept connections..."
	@until docker compose -f docker-compose.dev.yml exec postgres psql -U crossbill -d crossbill -c "SELECT 1" > /dev/null 2>&1; do sleep 1; done
	$(MAKE) migrate
