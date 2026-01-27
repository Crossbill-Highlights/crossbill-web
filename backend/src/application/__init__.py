"""
Application layer.

The application layer orchestrates domain objects and defines the boundaries
of the system. It contains use cases that represent the operations available
to external actors.

This layer contains:
- Commands: Write operations that change state
- Queries: Read operations that return data
- Use Case Handlers: Orchestrate domain logic
- DTOs: Data transfer objects for input/output
- Ports: Interfaces for external dependencies
"""
