## Type Checking section near the top of CLAUDE.md\n\

This project uses **pyright** for type checking. Always run `pyright` to verify type correctness after changes. Never suggest or run mypy.
Add as a dedicated ## Architecture section in CLAUDE.md\n\n## Architecture: DDD with Hexagonal/DI Patterns

- Domain entities and value objects must NOT depend on ORM models or Pydantic schemas
- ORM models belong ONLY in the infrastructure/repository layer — never in routers, application services, or domain layer
- Application services work with domain entities, NOT ORM models
- Repositories are responsible for all ORM-to-domain and domain-to-ORM conversion
- Domain services live in the domain layer, not the application layer
- When using SQLAlchemy joinedload with collections, always call `.unique()` on the result

## Refactoring / Migration Rules section

After any file deletion or module move, immediately grep for all imports of the old module path and update them before running tests. Do NOT consider a migration complete until stale imports are resolved.

## Architecture section

When converting between domain entities and Pydantic schemas, ensure domain value objects (e.g., XPoint) are converted to their primitive representations (str, int, etc.) before passing to Pydantic models. Do not pass raw value objects to schema fields.

## Testing section

Always run the full test suite (`pytest`) after completing any migration or refactoring. Do not declare work complete until all tests pass. If tests fail, fix them before stopping.

## Working Style section

When the user provides a migration plan document, follow it precisely. Do not redesign the architecture or create a broader plan unless explicitly asked. If something in the plan seems wrong, ask before deviating.
