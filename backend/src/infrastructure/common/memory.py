"""Helpers for nudging the C allocator to release freed memory back to the OS.

Parsing EPUBs with lxml/libxml2 makes many short-lived C-heap allocations. After
they are freed, glibc keeps the pages in its per-arena free lists instead of
returning them to the OS, so RSS ratchets upward on every parse. ``malloc_trim``
asks glibc to hand those freed pages back. This is a no-op on non-glibc
platforms (e.g. musl/Alpine) and is always safe to call.
"""

import ctypes
import functools
import logging
import platform
from collections.abc import Callable
from typing import ParamSpec, TypeVar

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


def _load_glibc() -> ctypes.CDLL | None:
    if platform.system() != "Linux":
        return None
    try:
        libc = ctypes.CDLL("libc.so.6", use_errno=True)
    except OSError:
        return None
    # malloc_trim is glibc-only; absent on musl.
    if not hasattr(libc, "malloc_trim"):
        return None
    return libc


_LIBC = _load_glibc()


def trim_memory() -> None:
    """Ask glibc to return freed heap pages to the OS.

    Fire-and-forget: failures are logged at debug level and never raised, so
    callers can use this purely as an optimisation hint.
    """
    if _LIBC is None:
        return
    try:
        _LIBC.malloc_trim(0)
    except Exception:  # pragma: no cover - defensive, malloc_trim should not raise
        logger.debug("malloc_trim failed", exc_info=True)


def trims_memory(func: Callable[P, R]) -> Callable[P, R]:
    """Decorate a (synchronous) parsing method to ``trim_memory()`` when it returns.

    Attach this to infrastructure methods that parse EPUBs with lxml/libxml2 so the
    freed C-heap pages are released back to the OS once the parse completes. Runs in a
    ``finally`` block, so it also trims when the wrapped call raises.
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return func(*args, **kwargs)
        finally:
            trim_memory()

    return wrapper
