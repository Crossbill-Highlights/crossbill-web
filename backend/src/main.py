"""Main FastAPI application."""

import asyncio
import contextlib
import os
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.config import configure_logging, get_settings
from src.database import dispose_engine, get_session_factory, initialize_database
from src.domain.common.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleViolationError,
    ConflictError,
    DomainError,
    EntityNotFoundError,
    ValidationError,
)
from src.infrastructure.common.routers import settings as settings_router
from src.infrastructure.identity.repositories.user_repository import UserRepository
from src.infrastructure.identity.routers import auth, users
from src.infrastructure.identity.services.password_service import hash_password
from src.infrastructure.jobs.routers import job_batches
from src.infrastructure.jobs.saq_job_queue_service import SaqJobQueueService
from src.infrastructure.jobs.saq_queue import create_queue
from src.infrastructure.learning.routers import (
    ai_chapter_flashcard_suggestions,
    ai_flashcard_suggestions,
    flashcards,
    quiz_sessions,
)
from src.infrastructure.learning.routers import book_flashcards as learning_books
from src.infrastructure.library.routers import books as library_books
from src.infrastructure.library.routers import covers as library_covers
from src.infrastructure.library.routers import ereader as library_ereader
from src.infrastructure.reading.routers import (
    bookmarks,
    chapter_content,
    chapter_prereading,
    highlight_labels,
    highlights,
    reading_sessions,
)

settings = get_settings()

# Configure structured logging
configure_logging(settings.ENVIRONMENT)

logger = structlog.get_logger(__name__)

# Directory for frontend static files
STATIC_DIR = (Path(__file__).parent.parent / "static").resolve()


async def _initialize_admin_password() -> None:
    """Initialize admin user password from environment variable if not set."""
    session_factory = get_session_factory(settings)
    async with session_factory() as db:
        # Use repository to find and update admin user
        user_repository = UserRepository(db)
        admin_user = await user_repository.find_by_email(settings.ADMIN_USERNAME)

        if not admin_user:
            logger.warning(
                "admin_user_not_found",
                username=settings.ADMIN_USERNAME,
            )
            return

        if admin_user.has_password():
            logger.info(
                "admin_password_skip",
                reason="password already set",
                username=settings.ADMIN_USERNAME,
            )
            return

        # Hash password and update domain entity
        hashed = hash_password(settings.ADMIN_PASSWORD)
        admin_user.update_password(hashed)

        # Save via repository
        await user_repository.save(admin_user)
        await db.commit()

        logger.info(
            "admin_password_initialized",
            username=settings.ADMIN_USERNAME,
        )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager."""
    # Initialize database engine and connection pool once at startup
    initialize_database(settings)

    # Skip database initialization during tests
    if not os.getenv("TESTING"):
        await _initialize_admin_password()

    # Initialize SAQ queue for job enqueueing
    from src.core import container  # noqa: PLC0415

    saq_queue = create_queue(settings.DATABASE_URL)
    await saq_queue.connect()
    queue_service = SaqJobQueueService(saq_queue)
    container.job_queue_service.override(queue_service)

    # Start embedded worker if enabled (runs SAQ in the same process)
    embedded_worker = None
    worker_task: asyncio.Task[None] | None = None
    if settings.EMBEDDED_WORKER:
        from src.worker import create_embedded_worker  # noqa: PLC0415

        embedded_worker = create_embedded_worker(saq_queue, concurrency=settings.WORKER_CONCURRENCY)
        worker_task = asyncio.create_task(embedded_worker.start())
        logger.info("embedded_worker_started", concurrency=settings.WORKER_CONCURRENCY)

    yield

    # Stop embedded worker gracefully.
    # worker.stop() signals the run-loop to exit, which should resolve
    # worker_task naturally.  The cancel() is a defensive fallback in case
    # start() does not exit cleanly (e.g. stuck awaiting a job).
    if embedded_worker is not None and worker_task is not None:
        await embedded_worker.stop()
        worker_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await worker_task
        logger.info("embedded_worker_stopped")

    await saq_queue.disconnect()
    container.job_queue_service.reset_override()

    # Cleanup on shutdown
    await dispose_engine()


_docs_enabled = settings.ENVIRONMENT != "production"

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url=f"{settings.API_V1_PREFIX}/docs" if _docs_enabled else None,
    redoc_url=f"{settings.API_V1_PREFIX}/redoc" if _docs_enabled else None,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json" if _docs_enabled else None,
    lifespan=lifespan,
)

# Configure rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Handle rate limit exceeded errors."""
    logger.warning(
        "rate_limit_exceeded",
        path=request.url.path,
        client_host=request.client.host if request.client else None,
    )
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
        },
    )


# Add request ID middleware
@app.middleware("http")
async def add_request_id_and_logging(
    request: Request, call_next: RequestResponseEndpoint
) -> Response:
    """Add request ID to each request and log request/response."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Bind request_id to context for all logs in this request
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    start_time = time.time()

    # Log incoming request
    logger.info(
        "request_started",
        method=request.method,
        path=request.url.path,
        client_host=request.client.host if request.client else None,
    )

    response = await call_next(request)

    # Calculate request duration
    duration = time.time() - start_time

    # Log completed request
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(duration * 1000, 2),
    )

    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id

    return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        if settings.ENVIRONMENT != "development":
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


app.add_middleware(SecurityHeadersMiddleware)

# Configure CORS
# Note: When using wildcard origins, credentials must be False
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials="*" not in settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


DOMAIN_ERROR_STATUS_MAP: list[tuple[type[DomainError], int, str]] = [
    (EntityNotFoundError, 404, "not_found"),
    (ValidationError, 400, "bad_request"),
    (ConflictError, 409, "conflict"),
    (AuthenticationError, 401, "authentication_error"),
    (AuthorizationError, 403, "authorization_error"),
    (BusinessRuleViolationError, 400, "bad_request"),
]

SAFE_MESSAGES: dict[int, str] = {
    404: "The requested resource was not found.",
    400: "The request could not be processed.",
    401: "Authentication failed.",
    403: "You do not have permission to perform this action.",
    409: "The resource already exists or conflicts with current state.",
    500: "An unexpected error occurred.",
}


# Exception handlers
@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    """Handle all domain exceptions with safe, generic messages."""
    status_code = 500
    error_key = "internal_error"
    for exc_type, code, key in DOMAIN_ERROR_STATUS_MAP:
        if isinstance(exc, exc_type):
            status_code = code
            error_key = key
            break

    if status_code >= 500:  # noqa: PLR2004
        logger.error(
            "domain_error",
            error_type=type(exc).__name__,
            status_code=status_code,
            detail=exc.message,
            exc_info=True,
        )
    else:
        logger.warning(
            "domain_error",
            error_type=type(exc).__name__,
            status_code=status_code,
            detail=exc.message,
        )

    headers: dict[str, str] = {}
    if isinstance(exc, AuthenticationError):
        headers["WWW-Authenticate"] = "Bearer"

    return JSONResponse(
        status_code=status_code,
        content={
            "error": error_key,
            "message": SAFE_MESSAGES[status_code],
        },
        headers=headers or None,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unexpected exceptions. Returns generic 500."""
    logger.error(
        "unhandled_exception",
        exception_type=type(exc).__name__,
        message=str(exc),
        path=request.url.path,
        exc_info=exc,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": SAFE_MESSAGES[500],
        },
    )


# Register routers

# Library
app.include_router(library_books.router, prefix=settings.API_V1_PREFIX)
app.include_router(library_ereader.router, prefix=settings.API_V1_PREFIX)
app.include_router(library_covers.router, prefix=settings.API_V1_PREFIX)

# Reading
app.include_router(highlights.router, prefix=settings.API_V1_PREFIX)
app.include_router(reading_sessions.router, prefix=settings.API_V1_PREFIX)
app.include_router(bookmarks.router, prefix=settings.API_V1_PREFIX)
app.include_router(chapter_prereading.router, prefix=settings.API_V1_PREFIX)
app.include_router(chapter_prereading.book_prereading_router, prefix=settings.API_V1_PREFIX)
app.include_router(chapter_content.router, prefix=settings.API_V1_PREFIX)
app.include_router(highlight_labels.router, prefix=settings.API_V1_PREFIX)

# Learning
app.include_router(learning_books.router, prefix=settings.API_V1_PREFIX)
app.include_router(flashcards.router, prefix=settings.API_V1_PREFIX)
app.include_router(ai_flashcard_suggestions.router, prefix=settings.API_V1_PREFIX)
app.include_router(ai_chapter_flashcard_suggestions.router, prefix=settings.API_V1_PREFIX)
app.include_router(quiz_sessions.router, prefix=settings.API_V1_PREFIX)

# Identity
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(users.router, prefix=settings.API_V1_PREFIX)

# Jobs
app.include_router(job_batches.router, prefix=settings.API_V1_PREFIX)

# Common
app.include_router(settings_router.router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get(f"{settings.API_V1_PREFIX}/")
async def api_root() -> dict[str, Any]:
    """API root endpoint."""
    response: dict[str, Any] = {
        "message": "crossbill API v1",
        "version": settings.VERSION,
    }
    if _docs_enabled:
        response["docs"] = f"{settings.API_V1_PREFIX}/docs"
    return response


# Mount static files for frontend assets (JS, CSS, etc.)
# Only mount if static directory exists (for development without built frontend)
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="static_assets")

    # Catch-all route for SPA - serves index.html for all other routes
    # This must be last to not interfere with API routes
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str) -> FileResponse:
        """Serve the SPA for all non-API routes."""
        # If the path is a file that exists in static, serve it
        file_path = (STATIC_DIR / full_path).resolve()

        # Validate that the resolved path is within STATIC_DIR to prevent path traversal
        if not file_path.is_relative_to(STATIC_DIR):
            raise HTTPException(status_code=404, detail="Not found")

        if file_path.is_file():
            return FileResponse(file_path)
        # Otherwise serve index.html for client-side routing
        return FileResponse(STATIC_DIR / "index.html")
