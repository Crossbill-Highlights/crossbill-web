# Multi-User Database Model Implementation Plan

This document outlines the implementation plan for adding multi-user support to the Crossbill database models. This is the first phase focusing only on database schema changes, not authentication.

## Overview

### Goals
1. Create a User table with default admin user on first startup
2. Associate books and tags directly to users (other entities inherit ownership through book)
3. Update unique constraints to be user-scoped
4. Migrate existing data to the default admin user

### Current State
- 7 models: Book, Chapter, Highlight, Tag, HighlightTag, HighlightTagGroup, Bookmark
- No user model exists
- All data is globally shared
- Unique constraints are global (e.g., Tag.name is globally unique)

---

## Phase 1: User Model

### 1.1 Create User Model

**File:** `backend/src/models.py`

```python
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    books: Mapped[list["Book"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    tags: Mapped[list["Tag"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
```

### 1.2 Default Admin User

The default admin user will be created during the migration with:
- `id`: 1
- `name`: "admin"

This user will own all existing data after migration.

---

## Phase 2: Model Modifications

### 2.1 Book Model Changes

Add `user_id` foreign key to associate books with users.

```python
class Book(Base):
    # Existing fields...

    # NEW: User association
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # NEW: Relationship
    user: Mapped["User"] = relationship(back_populates="books")
```

**Impact:**
- Books are directly owned by users
- Chapters, Highlights, HighlightTags, HighlightTagGroups, and Bookmarks inherit user ownership through the book relationship
- No changes needed to these child models - they remain scoped to book_id

### 2.2 Tag Model Changes

Add `user_id` foreign key and update unique constraint.

```python
class Tag(Base):
    # Existing fields...

    # NEW: User association
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # NEW: Relationship
    user: Mapped["User"] = relationship(back_populates="tags")

    # UPDATED: Table constraint
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_tag_user_name"),
    )
```

**Impact:**
- Tags become user-scoped
- Different users can have tags with the same name
- Existing global uniqueness on `name` is replaced with `(user_id, name)` uniqueness

---

## Phase 3: Unique Constraint Analysis

### Current Constraints vs New Constraints

| Model | Current Constraint | New Constraint | Change Required |
|-------|-------------------|----------------|-----------------|
| **User** | (none) | name unique? | New table |
| **Book** | (none) | (none) | Add user_id FK only |
| **Tag** | `name` (global) | `(user_id, name)` | **Yes - must update** |
| **Chapter** | `(book_id, name)` | `(book_id, name)` | No change needed |
| **Highlight** | `(book_id, text, datetime)` | `(book_id, text, datetime)` | No change needed |
| **HighlightTag** | `(book_id, name)` | `(book_id, name)` | No change needed |
| **HighlightTagGroup** | `(book_id, name)` | `(book_id, name)` | No change needed |
| **Bookmark** | (none) | (none) | No change needed |

### Why Most Constraints Don't Need Changes

- **Chapter, Highlight, HighlightTag, HighlightTagGroup, Bookmark**: These are all scoped to `book_id`. Since books will now be user-scoped, the child entities are transitively user-scoped. The existing constraints prevent duplicates within a book, which is the correct behavior.

- **Tag**: Currently globally unique by name. Must change to `(user_id, name)` so different users can have tags with the same name (e.g., both users can have a "Fiction" tag).

---

## Phase 4: Repository Layer Updates

### 4.1 New UserRepository

**File:** `backend/src/repositories/user_repository.py`

```python
class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_name(self, name: str) -> User | None:
        return self.db.query(User).filter(User.name == name).first()

    def create(self, name: str) -> User:
        user = User(name=name)
        self.db.add(user)
        self.db.flush()
        return user

    def get_or_create_default_admin(self) -> User:
        admin = self.get_by_name("admin")
        if admin is None:
            admin = self.create("admin")
        return admin
```

### 4.2 BookRepository Updates

Update methods to include user_id parameter:

```python
class BookRepository:
    def find_by_title_and_author(
        self, title: str, author: str | None, user_id: int
    ) -> Book | None:
        query = self.db.query(Book).filter(
            Book.title == title,
            Book.user_id == user_id  # NEW
        )
        if author:
            query = query.filter(Book.author == author)
        return query.first()

    def create(self, book_data: BookCreate, user_id: int) -> Book:
        book = Book(**book_data.model_dump(), user_id=user_id)  # NEW
        self.db.add(book)
        self.db.flush()
        return book

    def get_or_create(self, book_data: BookCreate, user_id: int) -> tuple[Book, bool]:
        # Updated to use user_id
        ...

    def get_books_with_highlight_count(
        self, user_id: int, offset: int, limit: int, search_text: str | None
    ) -> list[BookWithHighlightCount]:
        # Filter by user_id
        ...

    def get_by_id(self, book_id: int, user_id: int) -> Book | None:
        return self.db.query(Book).filter(
            Book.id == book_id,
            Book.user_id == user_id
        ).first()
```

### 4.3 TagRepository Updates

Update methods to include user_id parameter:

```python
class TagRepository:
    def get_by_name(self, name: str, user_id: int) -> Tag | None:
        return self.db.query(Tag).filter(
            Tag.name == name,
            Tag.user_id == user_id
        ).first()

    def create(self, name: str, user_id: int) -> Tag:
        tag = Tag(name=name, user_id=user_id)
        self.db.add(tag)
        self.db.flush()
        return tag

    def get_or_create(self, name: str, user_id: int) -> tuple[Tag, bool]:
        # Updated to use user_id
        ...

    def get_all(self, user_id: int) -> list[Tag]:
        return self.db.query(Tag).filter(
            Tag.user_id == user_id
        ).order_by(Tag.name).all()
```

### 4.4 Other Repository Updates

The following repositories need user_id filtering for security (ensuring users only access their own data):

- **ChapterRepository**: Add user_id verification through book ownership
- **HighlightRepository**: Add user_id verification through book ownership
- **HighlightTagRepository**: Add user_id verification through book ownership
- **BookmarkRepository**: Add user_id verification through book ownership

These can verify ownership by joining to the books table:

```python
def get_by_id_for_user(self, highlight_id: int, user_id: int) -> Highlight | None:
    return self.db.query(Highlight).join(Book).filter(
        Highlight.id == highlight_id,
        Book.user_id == user_id
    ).first()
```

---

## Phase 5: Migration Strategy

### 5.1 Migration File: `013_add_users_table.py`

This migration will:

1. Create the `users` table
2. Insert the default admin user with id=1
3. Add `user_id` column to `books` table (nullable initially)
4. Add `user_id` column to `tags` table (nullable initially)
5. Update all existing books to belong to admin user (user_id=1)
6. Update all existing tags to belong to admin user (user_id=1)
7. Make `user_id` columns NOT NULL
8. Add foreign key constraints
9. Drop old unique constraint on tags.name
10. Add new unique constraint on (user_id, name) for tags
11. Add indexes

```python
"""Add users table and associate existing data with admin user

Revision ID: 013
Revises: 012
Create Date: 2024-XX-XX
"""

from alembic import op
import sqlalchemy as sa

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"])
    op.create_index(op.f("ix_users_name"), "users", ["name"])

    # 2. Insert default admin user
    op.execute("INSERT INTO users (id, name) VALUES (1, 'admin')")

    # 3. Add user_id to books (nullable first)
    op.add_column("books", sa.Column("user_id", sa.Integer(), nullable=True))

    # 4. Add user_id to tags (nullable first)
    op.add_column("tags", sa.Column("user_id", sa.Integer(), nullable=True))

    # 5. Migrate existing data to admin user
    op.execute("UPDATE books SET user_id = 1 WHERE user_id IS NULL")
    op.execute("UPDATE tags SET user_id = 1 WHERE user_id IS NULL")

    # 6. Make user_id NOT NULL
    op.alter_column("books", "user_id", nullable=False)
    op.alter_column("tags", "user_id", nullable=False)

    # 7. Add foreign key constraints
    op.create_foreign_key(
        "fk_books_user_id", "books", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_tags_user_id", "tags", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )

    # 8. Update tags unique constraint
    # Drop old constraint (name only)
    op.drop_constraint("uq_tags_name", "tags", type_="unique")  # May need to check actual name
    # Add new constraint (user_id, name)
    op.create_unique_constraint("uq_tag_user_name", "tags", ["user_id", "name"])

    # 9. Add indexes
    op.create_index(op.f("ix_books_user_id"), "books", ["user_id"])
    op.create_index(op.f("ix_tags_user_id"), "tags", ["user_id"])


def downgrade() -> None:
    # Remove indexes
    op.drop_index(op.f("ix_tags_user_id"), table_name="tags")
    op.drop_index(op.f("ix_books_user_id"), table_name="books")

    # Restore old tags constraint
    op.drop_constraint("uq_tag_user_name", "tags", type_="unique")
    op.create_unique_constraint("uq_tags_name", "tags", ["name"])

    # Remove foreign keys
    op.drop_constraint("fk_tags_user_id", "tags", type_="foreignkey")
    op.drop_constraint("fk_books_user_id", "books", type_="foreignkey")

    # Remove user_id columns
    op.drop_column("tags", "user_id")
    op.drop_column("books", "user_id")

    # Drop users table
    op.drop_index(op.f("ix_users_name"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")
```

---

## Phase 6: Implementation Order

### Step-by-Step Implementation

1. **Create User model** (`models.py`)
   - Add User class with id, name, timestamps
   - Add relationships to Book and Tag

2. **Update Book model** (`models.py`)
   - Add user_id foreign key
   - Add user relationship
   - Update back_populates

3. **Update Tag model** (`models.py`)
   - Add user_id foreign key
   - Add user relationship
   - Update __table_args__ with new unique constraint

4. **Create migration file** (`alembic/versions/013_add_users_table.py`)
   - Follow the migration strategy above

5. **Create UserRepository** (`repositories/user_repository.py`)
   - Basic CRUD operations
   - get_or_create_default_admin method

6. **Update BookRepository** (`repositories/book_repository.py`)
   - Add user_id parameter to all methods
   - Update queries to filter by user_id

7. **Update TagRepository** (`repositories/tag_repository.py`)
   - Add user_id parameter to all methods
   - Update queries to filter by user_id

8. **Update other repositories** (if needed for security)
   - Add user ownership verification through book joins

9. **Update Pydantic schemas** (`schemas/`)
   - Add UserCreate, UserResponse schemas
   - Update BookCreate if needed

10. **Run and test migration**
    - `alembic upgrade head`
    - Verify existing data is associated with admin user
    - Verify unique constraints work correctly

---

## Phase 7: Testing Strategy

### 7.1 Migration Tests

- Test that migration runs successfully on empty database
- Test that migration runs successfully on database with existing data
- Test that all existing books are associated with admin user
- Test that all existing tags are associated with admin user
- Test downgrade works correctly

### 7.2 Model Tests

- Test User model creation
- Test Book model with user_id
- Test Tag model with new unique constraint
- Test that two users can have tags with the same name
- Test that two users can have books with same title/author
- Test cascade delete (deleting user deletes their books and tags)

### 7.3 Repository Tests

- Test BookRepository with user_id filtering
- Test TagRepository with user_id filtering
- Test that users cannot access other users' data

---

## Summary

### Files to Create
- `backend/src/repositories/user_repository.py`
- `backend/alembic/versions/013_add_users_table.py`

### Files to Modify
- `backend/src/models.py` (add User model, update Book and Tag)
- `backend/src/repositories/__init__.py` (export UserRepository)
- `backend/src/repositories/book_repository.py` (add user_id)
- `backend/src/repositories/tag_repository.py` (add user_id)
- `backend/src/schemas/` (add user schemas if needed)

### Database Changes
- New table: `users`
- Modified table: `books` (add user_id FK)
- Modified table: `tags` (add user_id FK, change unique constraint)

### Data Migration
- All existing books → admin user (id=1)
- All existing tags → admin user (id=1)
