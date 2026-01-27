"""
Infrastructure layer.

The infrastructure layer contains implementations of ports defined
in the application layer. It handles all external concerns:

- Persistence (database, ORM)
- Web framework (FastAPI, routers)
- External services (AI, storage, email)
- Configuration and dependency injection

This layer depends on domain and application layers,
but they do not depend on it.
"""
