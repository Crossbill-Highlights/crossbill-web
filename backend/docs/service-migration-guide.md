# Service Migration Guide: From Legacy to DDD Architecture

This guide provides a comprehensive, step-by-step process for migrating services from the legacy layered architecture to the new DDD-inspired hexagonal architecture.

## Table of Contents

1. [Overview](#overview)
2. [When to Migrate](#when-to-migrate)
3. [Architecture Patterns](#architecture-patterns)
4. [Migration Process](#migration-process)
5. [Common Patterns](#common-patterns)
6. [Testing Strategy](#testing-strategy)
7. [Troubleshooting](#troubleshooting)

## Overview

The migration involves restructuring code into three main layers:

- **Domain Layer**: Pure business logic, entities, value objects, domain exceptions
- **Application Layer**: Use case orchestration, transaction management
- **Infrastructure Layer**: Persistence, external services, ORM mapping

## When to Migrate

Migrate a service when:

- Adding significant new features that require business logic
- Refactoring existing services with complex business rules
- The service has grown too large and needs better separation of concerns
- You need better testability and maintainability

## Architecture Patterns

### Domain Layer (src/domain/)

**Entities**: Objects with distinct identity

```python
@dataclass
class HighlightTag(Entity[HighlightTagId]):
    id: HighlightTagId
    user_id: UserId
    book_id: BookId
    name: str

    def __post_init__(self) -> None:
        # Validation
        if not self.name or not self.name.strip():
            raise DomainError("Tag name cannot be empty")

    def rename(self, new_name: str) -> None:
        # Business logic
        if not new_name or not new_name.strip():
            raise DomainError("Tag name cannot be empty")
        self.name = new_name.strip()

    @classmethod
    def create(cls, user_id: UserId, book_id: BookId, name: str) -> "HighlightTag":
        # Factory method for new entities
        return cls(
            id=HighlightTagId.generate(),
            user_id=user_id,
            book_id=book_id,
            name=name.strip(),
        )

    @classmethod
    def create_with_id(cls, id: HighlightTagId, ...) -> "HighlightTag":
        # Factory method for reconstitution from persistence
        return cls(id=id, ...)
```

**Value Objects**: Immutable objects without identity

```python
@dataclass(frozen=True)
class HighlightTagId(EntityId):
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("HighlightTagId must be non-negative")

    @classmethod
    def generate(cls) -> "HighlightTagId":
        return cls(0)  # Database assigns real ID
```

**Domain Exceptions**: Business rule violations

```python
class DuplicateTagNameError(DomainError):
    """Raised when attempting to create a tag with a duplicate name."""

    def __init__(self, tag_name: str) -> None:
        super().__init__(f"Tag '{tag_name}' already exists for this book")
```

### Application Layer (src/application/)

**Application Services**: Orchestrate use cases

```python
class HighlightTagService:
    """Application service for highlight tag CRUD operations."""

    def __init__(self, db: Session):
        self.db = db
        self.tag_repository = HighlightTagRepository(db)
        self.book_repository = BookRepository(db)

    def create_tag(self, book_id: int, name: str, user_id: int) -> HighlightTag:
        # 1. Convert primitives to value objects
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        # 2. Validate dependencies
        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise ValueError(f"Book with id {book_id} not found")

        # 3. Check business rules
        existing = self.tag_repository.find_by_book_and_name(
            book_id_vo, name.strip(), user_id_vo
        )
        if existing:
            raise CrossbillError(f"Tag '{name}' already exists", status_code=409)

        # 4. Create entity using factory
        tag = HighlightTag.create(user_id=user_id_vo, book_id=book_id_vo, name=name)

        # 5. Persist
        tag = self.tag_repository.save(tag)
        self.db.commit()

        # 6. Log
        logger.info("created_highlight_tag", tag_id=tag.id.value, book_id=book_id)
        return tag
```

### Infrastructure Layer (src/infrastructure/)

**Repositories**: Persistence abstraction

```python
class HighlightTagRepository:
    def __init__(self, db: Session):
        self.db = db
        self.mapper = HighlightTagMapper()

    def find_by_id(self, tag_id: HighlightTagId, user_id: UserId) -> HighlightTag | None:
        stmt = select(HighlightTagORM).where(
            HighlightTagORM.id == tag_id.value,
            HighlightTagORM.user_id == user_id.value,
        )
        orm_model = self.db.execute(stmt).scalar_one_or_none()
        return self.mapper.to_domain(orm_model) if orm_model else None

    def save(self, tag: HighlightTag) -> HighlightTag:
        if tag.id.value == 0:
            # Create new
            orm_model = self.mapper.to_orm(tag)
            self.db.add(orm_model)
            self.db.flush()
            self.db.refresh(orm_model)  # Get database-generated values
            return self.mapper.to_domain(orm_model)
        else:
            # Update existing
            stmt = select(HighlightTagORM).where(HighlightTagORM.id == tag.id.value)
            existing_orm = self.db.execute(stmt).scalar_one()
            self.mapper.to_orm(tag, existing_orm)
            self.db.flush()
            return self.mapper.to_domain(existing_orm)
```

**Mappers**: ORM ↔ Domain conversion

```python
class HighlightTagMapper:
    def to_domain(self, orm_model: HighlightTagORM) -> HighlightTag:
        return HighlightTag.create_with_id(
            id=HighlightTagId(orm_model.id),
            user_id=UserId(orm_model.user_id),
            book_id=BookId(orm_model.book_id),
            name=orm_model.name,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at,
        )

    def to_orm(
        self, domain_entity: HighlightTag, orm_model: HighlightTagORM | None = None
    ) -> HighlightTagORM:
        if orm_model:
            # Update existing
            orm_model.name = domain_entity.name
            return orm_model

        # Create new
        return HighlightTagORM(
            id=domain_entity.id.value if domain_entity.id.value != 0 else None,
            user_id=domain_entity.user_id.value,
            book_id=domain_entity.book_id.value,
            name=domain_entity.name,
        )
```

## Migration Process

### Phase 1: Domain Layer Foundation

#### Step 1: Create Value Objects

Add ID value objects to `src/domain/common/value_objects/ids.py`:

```python
@dataclass(frozen=True)
class YourEntityId(EntityId):
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("YourEntityId must be non-negative")

    @classmethod
    def generate(cls) -> "YourEntityId":
        return cls(0)
```

#### Step 2: Create Domain Entities

Create `src/domain/{bounded_context}/entities/your_entity.py`:

1. Define entity with value objects for IDs
2. Add validation in `__post_init__()`
3. Add command methods (methods that change state)
4. Add query methods (methods that return information)
5. Add factory methods: `create()` and `create_with_id()`

#### Step 3: Add Domain Exceptions

Add to `src/domain/{bounded_context}/exceptions.py`:

```python
class YourEntityNotFoundError(DomainError):
    """Raised when entity cannot be found."""

    def __init__(self, entity_id: int) -> None:
        super().__init__(f"Entity {entity_id} not found")
```

### Phase 2: Infrastructure Layer

#### Step 4: Create Mapper

Create `src/infrastructure/{bounded_context}/mappers/your_entity_mapper.py`:

1. Implement `to_domain()` - ORM to domain entity (use `create_with_id()`)
2. Implement `to_orm()` - domain entity to ORM (handle both create and update)

#### Step 5: Create Repository

Create `src/infrastructure/{bounded_context}/repositories/your_entity_repository.py`:

1. Accept `Session` in constructor
2. Initialize mapper
3. Implement query methods (`find_by_id`, `find_by_*`, etc.)
4. Implement `save()` method
5. Implement `delete()` method if needed
6. Always return domain entities, never ORM models
7. Use `db.refresh(orm_model)` after `db.flush()` for new entities

### Phase 3: Application Layer

#### Step 6: Create Application Services

Create service(s) in `src/application/{bounded_context}/services/`:

1. Accept `Session` in constructor
2. Initialize repositories
3. For each use case:
   - Convert primitive inputs to value objects
   - Load and validate dependencies
   - Check business rules
   - Use entity command methods
   - Persist via repository
   - Commit transaction
   - Log operation
   - Return domain entity

**Service Granularity**: Follow Single Responsibility Principle. Create separate services for:
- Core CRUD operations
- Association management
- Complex workflows

### Phase 4: Router Integration

#### Step 7: Update Routers

1. Import new application services
2. Import domain exceptions
3. Update endpoint handlers to use new services
4. **Handle value objects in responses** - manually construct Pydantic schemas:

```python
# DON'T do this (will fail with value objects):
return schemas.YourEntity.model_validate(entity)

# DO this instead:
return schemas.YourEntity(
    id=entity.id.value,  # Extract .value from value objects
    name=entity.name,    # Simple types are fine
    book_id=entity.book_id.value,
    created_at=entity.created_at,
    updated_at=entity.updated_at,
)
```

4. Add exception handling:

```python
try:
    result = service.do_something(...)
    return result
except (CrossbillError, DomainError) as e:
    # Handle domain/business errors
    if isinstance(e, CrossbillError):
        raise HTTPException(status_code=e.status_code, detail=str(e))
    raise HTTPException(status_code=400, detail=str(e))
except ValueError as e:
    # Handle validation errors
    raise HTTPException(status_code=400, detail=str(e))
```

### Phase 5: Testing & Cleanup

#### Step 8: Test

1. Run existing integration tests
2. Add unit tests for domain entities
3. Add unit tests for application services
4. Test all HTTP endpoints

#### Step 9: Clean Up

1. Remove legacy service file
2. Remove legacy repository file (if exists)
3. Update `__init__.py` imports
4. Search codebase for any remaining references

## Common Patterns

### Pattern 1: Value Objects at Boundaries

**Always** convert between primitives and value objects at service boundaries:

```python
# IN: Primitive → Value Object
def create_entity(self, entity_id: int, ...) -> Entity:
    entity_id_vo = EntityId(entity_id)
    ...

# OUT: Value Object → Primitive (in router)
return schemas.Entity(
    id=entity.id.value,
    ...
)
```

### Pattern 2: Factory Methods

Use factory methods for entity creation:

```python
# For new entities
entity = Entity.create(name="foo", ...)

# For reconstitution from database
entity = Entity.create_with_id(id=EntityId(1), name="foo", ...)
```

### Pattern 3: Command vs Query Methods

**Command methods** (change state):
```python
def rename(self, new_name: str) -> None:
    self.name = new_name
```

**Query methods** (return information):
```python
def belongs_to_user(self, user_id: UserId) -> bool:
    return self.user_id == user_id
```

### Pattern 4: Repository Patterns

```python
# Query: return None if not found
def find_by_id(self, id: EntityId) -> Entity | None:
    ...

# Query: return list (empty if none)
def find_by_user(self, user_id: UserId) -> list[Entity]:
    ...

# Command: upsert pattern
def save(self, entity: Entity) -> Entity:
    if entity.id.value == 0:
        # Create
    else:
        # Update
```

### Pattern 5: Transaction Management

Transactions are managed by application services:

```python
# Application Service
def create_something(self, ...) -> Entity:
    entity = Entity.create(...)
    entity = self.repository.save(entity)
    self.db.commit()  # ← Transaction boundary
    return entity
```

**Never** commit in:
- Domain entities
- Repositories
- Mappers

### Pattern 6: Error Handling Layers

1. **Domain Layer**: Raise `DomainError` for business rule violations
2. **Application Layer**: Raise `ValueError` for validation, `CrossbillError` for app errors
3. **Router Layer**: Convert to appropriate HTTP status codes

### Pattern 7: Application Layer Return Types

**CRITICAL**: Application services MUST NOT return Pydantic schemas.

**Return Options**:

1. **Domain Entities**: Return entities directly for simple operations
   ```python
   def create_tag(...) -> HighlightTag:
       return tag
   ```

2. **Primitives/Tuples**: For simple results
   ```python
   def upload_cover(...) -> str:  # Just the URL
       return cover_url

   def update_book(...) -> tuple[Book, int, int, list]:
       return (book, highlight_count, flashcard_count, tags)
   ```

3. **Domain Service Dataclasses**: For complex aggregations
   ```python
   @dataclass
   class BookDetailsAggregation:
       book: Book
       chapters_with_highlights: list[ChapterWithHighlights]
       # ... other aggregated data
   ```

**Router Responsibilities**:
- Construct Pydantic schemas from domain data
- Extract `.value` from value objects
- Use helper functions for complex transformations
- Keep helpers private to router file (prefix with `_`)

**Example**:
```python
# Service returns domain data
agg = service.get_book_details(book_id, user_id)

# Router constructs schema
return schemas.BookDetails(
    id=agg.book.id.value,  # Extract .value
    title=agg.book.title,
    chapters=_map_chapters_to_schemas(agg.chapters_with_highlights),
    # ...
)
```

## Testing Strategy

### Unit Tests

**Domain Entities**:
```python
def test_entity_validation():
    with pytest.raises(DomainError):
        Entity.create(name="")  # Invalid

def test_entity_command():
    entity = Entity.create(name="old")
    entity.rename("new")
    assert entity.name == "new"
```

**Application Services** (with mocked repositories):
```python
def test_create_service(mocker):
    mock_repo = mocker.Mock()
    service = YourService(mock_db)
    service.repository = mock_repo

    result = service.create(...)

    mock_repo.save.assert_called_once()
```

### Integration Tests

Keep existing API tests - they should continue to pass after migration.

## Troubleshooting

### Issue: Pydantic Validation Errors with Value Objects

**Symptom**: 400 Bad Request when returning responses, validation error about expecting `int` but got `YourValueObject`

**Solution**: Manually construct Pydantic schemas, extracting `.value`:

```python
return schemas.YourEntity(
    id=entity.id.value,  # Extract .value
    ...
)
```

### Issue: Missing `created_at`/`updated_at`

**Symptom**: Domain entity has `None` for timestamps after creation

**Solution**: Add `db.refresh(orm_model)` after `db.flush()` in repository:

```python
def save(self, entity: Entity) -> Entity:
    if entity.id.value == 0:
        orm_model = self.mapper.to_orm(entity)
        self.db.add(orm_model)
        self.db.flush()
        self.db.refresh(orm_model)  # ← Get server-generated values
        return self.mapper.to_domain(orm_model)
```

### Issue: Circular Import

**Symptom**: `ImportError: cannot import name 'X' from partially initialized module`

**Solution**: Use forward references in type hints:

```python
def add_tag(self, tag: "HighlightTag") -> None:  # ← String literal
    from src.domain.reading.entities.highlight_tag import HighlightTag
    if not isinstance(tag, HighlightTag):
        ...
```

### Issue: Service Method Not Found

**Symptom**: Tests fail with "module has no attribute 'OldService'"

**Solution**: Search for remaining imports:

```bash
grep -r "from src.services.old_service" src/
grep -r "repositories.OldRepository" src/
```

## Examples

See these completed migrations for reference:

- **Highlight Service**: `src/application/reading/services/highlight_upload_service.py`
- **HighlightTag Service**: `src/application/reading/services/highlight_tag_service.py`
- **HighlightTagGroup Service**: `src/application/reading/services/highlight_tag_group_service.py`

## Key Principles

1. **Domain logic lives in domain entities** - not in services
2. **Application services orchestrate** - they don't contain business logic
3. **Repositories return domain entities** - never ORM models
4. **Value objects for IDs** - type safety prevents ID mixups
5. **Factory methods for creation** - `create()` for new, `create_with_id()` for reconstitution
6. **Transactions in application layer** - domain and infrastructure layers don't commit
7. **Explicit conversions at boundaries** - primitives ↔ value objects, domain ↔ ORM
8. **Manual Pydantic construction** - extract `.value` from value objects for responses

## Checklist

- [ ] Domain entities created with factory methods
- [ ] Value objects created for IDs
- [ ] Domain exceptions defined
- [ ] Mappers created (to_domain, to_orm)
- [ ] Repository created returning domain entities
- [ ] Application service(s) created
- [ ] Router updated to use new services
- [ ] Response construction handles value objects (manual schema construction)
- [ ] Exception handling added
- [ ] Tests passing
- [ ] Legacy code removed
- [ ] `__init__.py` files updated

## Further Reading

- [Domain-Driven Design by Eric Evans](https://www.domainlanguage.com/ddd/)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
