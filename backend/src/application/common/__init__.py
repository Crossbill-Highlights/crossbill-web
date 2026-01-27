"""
Application common module.

Contains base classes for application layer:
- Command: Base class for write operations
- Query: Base class for read operations
- CommandHandler: Handles command execution
- QueryHandler: Handles query execution
- Result: Result type for use case outcomes
"""

from .command import Command, CommandHandler
from .pagination import PaginatedResult, Pagination
from .query import Query, QueryHandler
from .result import Failure, Result, Success
from .unit_of_work import UnitOfWork

__all__ = [
    "Command",
    "CommandHandler",
    "Failure",
    "PaginatedResult",
    "Pagination",
    "Query",
    "QueryHandler",
    "Result",
    "Success",
    "UnitOfWork",
]
