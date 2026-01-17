"""FastAPI dependencies for the application."""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from fastapi import HTTPException, status

from src.config import get_settings

F = TypeVar("F", bound=Callable[..., Any])


def require_ai_enabled(func: F) -> F:
    """
    Decorator that requires AI to be enabled for the endpoint.

    Returns HTTP 410 Gone if AI features are disabled.

    Usage:
        @router.get("/endpoint")
        @require_ai_enabled
        async def my_endpoint():
            ...
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        settings = get_settings()
        if not settings.ai_enabled:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="AI features are not enabled on this server",
            )
        return await func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]
