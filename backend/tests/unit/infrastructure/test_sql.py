from src.infrastructure.common.sql import LIKE_ESCAPE_CHAR, escape_like_pattern


def test_escape_like_pattern_leaves_plain_text_unchanged() -> None:
    assert escape_like_pattern("hello world") == "hello world"


def test_escape_like_pattern_escapes_percent() -> None:
    assert escape_like_pattern("50%") == "50\\%"


def test_escape_like_pattern_escapes_underscore() -> None:
    assert escape_like_pattern("foo_bar") == "foo\\_bar"


def test_escape_like_pattern_escapes_backslash_first() -> None:
    # Backslash must be escaped before % / _ so we don't double-escape our
    # own escape character.
    assert escape_like_pattern("a\\%b") == "a\\\\\\%b"


def test_escape_like_pattern_escape_char_is_backslash() -> None:
    assert LIKE_ESCAPE_CHAR == "\\"
