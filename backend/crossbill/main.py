"""Main FastAPI application."""

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from crossbill.config import get_settings
from crossbill.routers import books, highlights

settings = get_settings()

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
    app.mount(
        "/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="static_assets"
    )

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
