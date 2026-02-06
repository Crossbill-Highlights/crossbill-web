from collections.abc import Callable
from typing import TypeVar

from dependency_injector.providers import Provider

from src.core import container
from src.database import DatabaseSession

T = TypeVar("T")


def inject_use_case(provider: Provider[T]) -> Callable[[DatabaseSession], T]:
    """
    Create a FastAPI dependency for a container provider.

    Automatically handles container.db override with request-scoped database session.
    """

    def dependency(db: DatabaseSession) -> T:
        try:
            container.db.override(db)
            return provider()
        finally:
            # Reset override after request completes
            container.db.reset_override()

    return dependency
