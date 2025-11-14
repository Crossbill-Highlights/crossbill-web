"""Main FastAPI application."""

import time
import uuid
from pathlib import Path
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import RequestResponseEndpoint

from crossbill.config import configure_logging, get_settings
from crossbill.exceptions import BookNotFoundError, CrossbillError, NotFoundError
from crossbill.routers import books, highlight, highlights

settings = get_settings()

# Configure structured logging
configure_logging(settings.ENVIRONMENT)

logger = structlog.get_logger(__name__)

# Directory for book cover images
COVERS_DIR = Path(__file__).parent.parent / "book-covers"

# Directory for frontend static files
STATIC_DIR = Path(__file__).parent.parent / "static"

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
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


# Configure CORS
# Note: When using wildcard origins, credentials must be False
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials="*" not in settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(BookNotFoundError)
async def book_not_found_handler(request: Request, exc: BookNotFoundError) -> JSONResponse:
    """Handle book not found errors."""
    logger.warning("book_not_found", book_id=exc.book_id)
    return JSONResponse(
        status_code=404,
        content={
            "error": "book_not_found",
            "message": str(exc),
            "book_id": exc.book_id,
        },
    )


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """Handle generic not found errors."""
    logger.warning("not_found_error", message=str(exc))
    return JSONResponse(
        status_code=404,
        content={
            "error": "not_found",
            "message": str(exc),
        },
    )


@app.exception_handler(CrossbillError)
async def crossbill_exception_handler(request: Request, exc: CrossbillError) -> JSONResponse:
    """Handle all custom Crossbill exceptions."""
    logger.error("crossbill_exception", message=str(exc), exception_type=type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": str(exc),
        },
    )


# Register routers
app.include_router(highlights.router, prefix=settings.API_V1_PREFIX)
app.include_router(highlight.router, prefix=settings.API_V1_PREFIX)
app.include_router(books.router, prefix=settings.API_V1_PREFIX)

# Mount static files for book covers
# Ensure directory exists before mounting
COVERS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media/covers", StaticFiles(directory=str(COVERS_DIR)), name="covers")


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get(f"{settings.API_V1_PREFIX}/")
async def api_root() -> dict[str, Any]:
    """API root endpoint."""
    return {
        "message": "crossbill API v1",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_PREFIX}/docs",
    }


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
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        # Otherwise serve index.html for client-side routing
        return FileResponse(STATIC_DIR / "index.html")
