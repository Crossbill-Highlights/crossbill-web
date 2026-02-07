# Claude Code Project Guidelines

## Type Checking

This project uses **pyright** (not mypy) for type checking. Always run `pyright` to verify type correctness after changes to Python files. Never suggest or run mypy.

```bash
# Backend type checking
cd backend && .venv/bin/pyright <file>

# Frontend type checking
cd frontend && npm run type-check
```

## Linting

- **Backend**: Uses `ruff` for linting and formatting
- **Frontend**: Uses `eslint` for linting, `prettier` for formatting

```bash
# Backend linting
cd backend && .venv/bin/ruff check <file>

# Frontend linting
cd frontend && npm run lint
```

## Architecture: Domain-Driven Design with Hexagonal/Dependency Injection Patterns

This backend follows DDD (Domain-Driven Design) with hexagonal architecture and dependency injection. **These boundaries are critical and must be strictly enforced:**

### Layer Responsibilities

1. **Domain Layer** (`backend/src/domain/`)
   - Contains domain entities, value objects, and domain services
   - **MUST NOT** depend on ORM models, Pydantic schemas, or any infrastructure
   - Pure business logic only
   - Example: `Book`, `Chapter`, `XPoint` (value objects)

2. **Application Layer** (`backend/src/application/`)
   - Contains use cases (application services)
   - Works with **domain entities**, NOT ORM models
   - Uses repository protocols (interfaces) via dependency injection
   - **MUST NOT** import from infrastructure layer
   - **MUST NOT** return Pydantic schemas - return domain entities

3. **Infrastructure Layer** (`backend/src/infrastructure/`)
   - Contains repository implementations
   - ORM models live **ONLY** here
   - Responsible for all ORM-to-domain and domain-to-ORM conversion
   - Implements repository protocols defined in domain layer

4. **Routers/API Layer** (`backend/src/routers/`)
   - HTTP endpoints
   - Uses use cases via dependency injection
   - Converts between domain entities and Pydantic schemas
   - **MUST NOT** use ORM models directly
   - **MUST NOT** contain business logic

### Critical Architectural Rules

1. **ORM Models**
   - ORM models belong **ONLY** in the infrastructure/repository layer
   - **NEVER** import or use ORM models in:
     - Routers
     - Application services (use cases)
     - Domain layer
   - Repositories are responsible for converting between ORM and domain entities

2. **Domain Entities vs ORM Models**
   - Domain entities are in `backend/src/domain/`
   - ORM models are in `backend/src/infrastructure/`
   - Domain entities must NOT depend on SQLAlchemy or ORM models
   - Application services work with domain entities, not ORM models

3. **Value Objects and Pydantic Schemas**
   - Domain value objects (e.g., `XPoint`, `ISBN`) must be converted to primitives before passing to Pydantic models
   - Do NOT pass raw value objects to Pydantic schema fields
   - Example:
     ```python
     # ✗ WRONG
     schema = BookSchema(xpoint=book.xpoint)  # XPoint is a value object

     # ✓ CORRECT
     schema = BookSchema(xpoint=book.xpoint.value)  # Convert to primitive
     ```

4. **SQLAlchemy Query Safety**
   - When using `joinedload()` with collections, always call `.unique()` on the result
   - Example:
     ```python
     # ✓ CORRECT
     result = session.execute(
         select(Book).options(joinedload(Book.chapters))
     ).unique().scalars().all()
     ```

5. **Domain Services**
   - Domain services live in the domain layer, NOT the application layer
   - They encapsulate domain logic that doesn't belong to a single entity

## Refactoring and Migration Rules

### Before ANY file deletion or module move:

1. **ALWAYS** grep for all imports of the old module path
2. Update all import references before running tests
3. Do NOT consider a migration complete until stale imports are resolved

```bash
# Example: Check for stale imports after moving a service
rg "from.*old_module_path import" backend/
```

### Migration Checklist

When migrating a service to DDD architecture:

1. ✓ Read the migration plan document if one exists
2. ✓ Create domain entities/value objects in domain layer (no ORM dependencies)
3. ✓ Create/update repository in infrastructure layer (all ORM code here only)
4. ✓ Convert application service to work with domain entities, not ORM models
5. ✓ After ANY file deletion/move, grep for old import paths and update them
6. ✓ Ensure value objects are converted to primitives before Pydantic schemas
7. ✓ For SQLAlchemy joinedload collections, use `.unique()`
8. ✓ Run pyright and fix all type errors
9. ✓ Run pytest and fix all test failures
10. ✓ Do NOT declare complete until all checks pass

## Testing

Always run the full test suite after completing any migration or refactoring:

```bash
cd backend && .venv/bin/pytest
```

Do not declare work complete until all tests pass. If tests fail, fix them before stopping.

## Working Style

- When a migration plan document exists, follow it precisely
- Do not redesign the architecture or create broader plans unless explicitly asked
- If something in the plan seems wrong, ask before deviating
- After editing files, the post-edit hooks will automatically run linting and type checking

## Common Pitfalls to Avoid

Based on past migrations, watch out for:

1. **ORM Leakage**: Accidentally using ORM models in routers or application services
2. **Stale Imports**: Leaving old import statements after moving/deleting files
3. **Value Object Type Errors**: Passing value objects directly to Pydantic instead of converting to primitives
4. **Missing .unique()**: Forgetting `.unique()` on SQLAlchemy queries with joinedload
5. **Domain Services in Wrong Layer**: Placing domain services in application layer instead of domain layer
6. **Incorrect Return Types**: Application services returning Pydantic schemas instead of domain entities

## Pre-Commit Validation

The project has automatic hooks that run:
- Ruff (linting)
- Pyright (type checking)

These run automatically after Edit/Write operations. Pay attention to the warnings and errors they surface.
