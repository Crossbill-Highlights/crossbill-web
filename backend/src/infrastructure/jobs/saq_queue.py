"""SAQ queue instance factory."""

from saq import Queue


def create_queue(database_url: str) -> Queue:
    """Create a SAQ queue backed by PostgreSQL."""
    return Queue.from_url(database_url)
