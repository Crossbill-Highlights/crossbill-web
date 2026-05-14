"""Regression test: middleware must not truncate FileResponse bodies.

When the request-id and security-headers middlewares were implemented with
Starlette's BaseHTTPMiddleware, FileResponse/StaticFiles bodies were re-streamed
through a memory pipe and could end up shorter than the declared Content-Length,
causing uvicorn to raise "Response content shorter than Content-Length".
"""

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from httpx import ASGITransport, AsyncClient

from src.main import RequestIdAndLoggingMiddleware, SecurityHeadersMiddleware


def _build_app(static_dir: Path) -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestIdAndLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.mount("/assets", StaticFiles(directory=str(static_dir)), name="assets")

    @app.get("/file")
    async def serve_file() -> FileResponse:  # pyright: ignore[reportUnusedFunction]
        return FileResponse(static_dir / "payload.bin")

    return app


@pytest.fixture
def static_dir(tmp_path: Path) -> Path:
    payload = b"x" * 65536  # 64 KiB — large enough to span multiple chunks
    (tmp_path / "payload.bin").write_bytes(payload)
    return tmp_path


@pytest.mark.asyncio
async def test_file_response_body_not_truncated(static_dir: Path) -> None:
    app = _build_app(static_dir)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/file")

    assert response.status_code == 200
    assert response.headers["content-length"] == "65536"
    assert len(response.content) == 65536
    assert response.content == b"x" * 65536


@pytest.mark.asyncio
async def test_staticfiles_body_not_truncated(static_dir: Path) -> None:
    app = _build_app(static_dir)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/assets/payload.bin")

    assert response.status_code == 200
    assert response.headers["content-length"] == "65536"
    assert len(response.content) == 65536


@pytest.mark.asyncio
async def test_request_id_and_security_headers_present(static_dir: Path) -> None:
    app = _build_app(static_dir)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/file")

    assert response.headers.get("x-request-id")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
