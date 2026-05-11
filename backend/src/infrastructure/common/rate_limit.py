"""Shared rate limiter instance used app-wide.

A single Limiter instance is exposed so that per-route ``@limiter.limit(...)``
decorators (e.g. on auth endpoints) and the global ``default_limits`` share
the same internal state. Using separate Limiter instances would cause the
global default to stack on top of per-route limits instead of being
overridden by them.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from src.config import get_settings

_settings = get_settings()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[_settings.RATE_LIMIT_DEFAULT],
    enabled=_settings.RATE_LIMIT_ENABLED,
    headers_enabled=True,
)
