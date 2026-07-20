"""Association tables for many-to-many relationships within the reading subdomain."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Table, func

from src.database import Base

# Association table for many-to-many relationship between highlights and tags
highlight_tags = Table(
    "highlight_tags",
    Base.metadata,
    Column(
        "highlight_id",
        Integer,
        ForeignKey("highlights.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
    Column(
        "tag_id",
        Integer,
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
    Column(
        "created_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
)


# Association table for many-to-many relationship between reading_sessions and highlights
reading_session_highlights = Table(
    "reading_session_highlights",
    Base.metadata,
    Column(
        "reading_session_id",
        Integer,
        ForeignKey("reading_sessions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "highlight_id",
        Integer,
        ForeignKey("highlights.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
    Column(
        "created_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
)
