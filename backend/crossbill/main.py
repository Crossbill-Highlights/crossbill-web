"""Main FastAPI application."""

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from crossbill.config import get_settings
from crossbill.routers import books, highlights

settings = get_settings()

# Directory for book cover images
COVERS_DIR = Path(__file__).parent.parent / "book-covers"

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# Configure CORS
# Note: When using wildcard origins, credentials must be False
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials="*" not in settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(highlights.router, prefix=settings.API_V1_PREFIX)
app.include_router(books.router, prefix=settings.API_V1_PREFIX)

# Mount static files for book covers
# Ensure directory exists before mounting
COVERS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media/covers", StaticFiles(directory=str(COVERS_DIR)), name="covers")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Welcome to crossbill API"}


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
