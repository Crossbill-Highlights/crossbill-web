# Claude Code Rules for Inkwell Backend

## Code Quality Standards

### Strong Typing Required
- All Python code MUST be strongly typed
- Use type hints for all function parameters and return values
- Use `typing` module types where appropriate (e.g., `Optional`, `Union`, `List`, `Dict`)
- Configure mypy with strict mode (already configured in `pyproject.toml`)
- No use of `Any` type unless absolutely necessary and documented

### Examples of Required Typing:
```python
# Good ✓
def get_highlight(db: Session, highlight_id: int) -> Optional[Highlight]:
    return db.query(Highlight).filter(Highlight.id == highlight_id).first()

# Bad ✗
def get_highlight(db, highlight_id):
    return db.query(Highlight).filter(Highlight.id == highlight_id).first()
```

## Pre-Commit Requirements

Before committing any code, you MUST run the following checks:

### 1. Linter (Ruff)
```bash
poetry run ruff check .
```
All linting errors must be fixed before committing. Use auto-fix when possible:
```bash
poetry run ruff check --fix .
```

### 2. Type Checks (mypy)
```bash
poetry run mypy inkwell
```
All type errors must be resolved before committing.

### 3. Code Formatting (Black)
```bash
poetry run black .
```
All code must be formatted with Black before committing.

### 4. Tests
```bash
poetry run pytest
```
All tests must pass before committing.

## Recommended Pre-Commit Workflow

Run all checks in sequence:
```bash
poetry run black . && \
poetry run ruff check --fix . && \
poetry run mypy inkwell && \
poetry run pytest
```

If all checks pass, you may proceed with the commit.

## Additional Guidelines

1. **SQLAlchemy 2.0 Style**: Use the modern SQLAlchemy 2.0 syntax with `Mapped` types
2. **Async Support**: Prefer async/await for all API endpoints
3. **Documentation**: All public functions and classes must have docstrings
4. **Error Handling**: Use proper exception handling and return appropriate HTTP status codes
5. **Security**: Never commit sensitive data (API keys, passwords, etc.)
6. **Testing**: Write tests for all new features and bug fixes
