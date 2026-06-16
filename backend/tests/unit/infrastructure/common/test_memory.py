"""Tests for the glibc memory-trim helpers."""

import contextlib

import pytest

from src.infrastructure.common.memory import trim_memory, trims_memory


def test_trim_memory_never_raises() -> None:
    """trim_memory is fire-and-forget and must be safe on any platform."""
    trim_memory()  # Should not raise, whether or not glibc is present.


def test_trims_memory_returns_wrapped_value() -> None:
    calls: list[int] = []

    @trims_memory
    def parse(x: int) -> int:
        calls.append(x)
        return x * 2

    assert parse(21) == 42
    assert calls == [21]


def test_trims_memory_preserves_metadata() -> None:
    @trims_memory
    def parse(x: int) -> int:
        """Parse docstring."""
        return x

    assert parse.__name__ == "parse"
    assert parse.__doc__ == "Parse docstring."


def test_trims_memory_trims_even_when_wrapped_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trimmed: list[bool] = []
    monkeypatch.setattr(
        "src.infrastructure.common.memory.trim_memory",
        lambda: trimmed.append(True),
    )

    @trims_memory
    def boom() -> None:
        raise ValueError("kaboom")

    with contextlib.suppress(ValueError):
        boom()

    assert trimmed == [True]
