LIKE_ESCAPE_CHAR = "\\"


def escape_like_pattern(text: str) -> str:
    """Escape LIKE/ILIKE wildcard characters in user-supplied search text.

    Pair with ``.ilike(pattern, escape=LIKE_ESCAPE_CHAR)`` so ``%`` and ``_`` in
    user input match literally instead of acting as wildcards.
    """
    return (
        text.replace(LIKE_ESCAPE_CHAR, LIKE_ESCAPE_CHAR * 2)
        .replace("%", LIKE_ESCAPE_CHAR + "%")
        .replace("_", LIKE_ESCAPE_CHAR + "_")
    )
