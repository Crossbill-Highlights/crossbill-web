# Multi-User Database Model Implementation Plan

This document outlines the implementation plan for adding multi-user support to the Crossbill database models. This is the first phase focusing only on database schema changes, not authentication.

## Overview

### Goals
1. Create a User table with default admin user on first startup
2. Associate books, tags, highlights, and highlight tags directly to users
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
    highlights: Mapped[list["Highlight"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    highlight_tags: Mapped[list["HighlightTag"]] = relationship(
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
- Chapters, HighlightTagGroups, and Bookmarks inherit user ownership through the book relationship

### 2.2 Highlight Model Changes

Add `user_id` foreign key to enable direct user-scoped queries.

```python
class Highlight(Base):
    # Existing fields...

    # NEW: User association
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # NEW: Relationship
    user: Mapped["User"] = relationship(back_populates="highlights")
```

**Impact:**
- Highlights can be queried directly by user without joining through books
- Enables efficient user-scoped highlight searches
- The existing unique constraint `(book_id, text, datetime)` remains valid since book_id is user-scoped

### 2.3 HighlightTag Model Changes

Add `user_id` foreign key and update unique constraint to include user scope.

```python
class HighlightTag(Base):
    # Existing fields...

    # NEW: User association
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # NEW: Relationship
    user: Mapped["User"] = relationship(back_populates="highlight_tags")

    # UPDATED: Table constraint - add user_id to existing constraint
    __table_args__ = (
        UniqueConstraint("user_id", "book_id", "name", name="uq_highlight_tag_user_book_name"),
        # ... existing indexes
    )
```

**Impact:**
- HighlightTags are explicitly user-scoped at the database level
- Direct user-scoped queries without book joins
- Unique constraint ensures tag names are unique per user per book

### 2.4 Tag Model Changes

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
| **User** | (none) | (none) | New table |
| **Book** | (none) | (none) | Add user_id FK only |
| **Highlight** | `(book_id, text, datetime)` | `(book_id, text, datetime)` | Add user_id FK only |
| **HighlightTag** | `(book_id, name)` | `(user_id, book_id, name)` | **Yes - must update** |
| **Tag** | `name` (global) | `(user_id, name)` | **Yes - must update** |
| **Chapter** | `(book_id, name)` | `(book_id, name)` | No change needed |
| **HighlightTagGroup** | `(book_id, name)` | `(book_id, name)` | No change needed |
| **Bookmark** | (none) | (none) | No change needed |

### Why Some Constraints Change

- **Tag**: Currently globally unique by name. Must change to `(user_id, name)` so different users can have tags with the same name (e.g., both users can have a "Fiction" tag).

- **HighlightTag**: Currently unique per `(book_id, name)`. Updated to `(user_id, book_id, name)` to make user scope explicit at the database level.

### Why Some Constraints Don't Change

- **Highlight**: The constraint `(book_id, text, datetime)` prevents duplicate highlights within a book. Since books are user-scoped, this remains correct. Adding user_id is for direct querying, not constraint changes.

- **Chapter, HighlightTagGroup, Bookmark**: These are scoped to `book_id`. Since books are user-scoped, the existing constraints remain valid.

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

### 4.4 HighlightRepository Updates

Update methods to include user_id parameter (now direct filtering, no join needed):

```python
class HighlightRepository:
    def create(self, book_id: int, user_id: int, highlight_data: HighlightCreate) -> Highlight:
        highlight = Highlight(
            book_id=book_id,
            user_id=user_id,  # NEW
            **highlight_data.model_dump()
        )
        self.db.add(highlight)
        self.db.flush()
        return highlight

    def find_by_book(self, book_id: int, user_id: int) -> list[Highlight]:
        return self.db.query(Highlight).filter(
            Highlight.book_id == book_id,
            Highlight.user_id == user_id,
            Highlight.deleted_at.is_(None)
        ).all()

    def search(self, search_text: str, user_id: int, book_id: int | None, limit: int) -> list[Highlight]:
        # Direct user filtering without book join
        query = self.db.query(Highlight).filter(
            Highlight.user_id == user_id,
            Highlight.deleted_at.is_(None)
        )
        # ... rest of search logic
```

### 4.5 HighlightTagRepository Updates

Update methods to include user_id parameter:

```python
class HighlightTagRepository:
    def find_by_name_and_book(self, book_id: int, name: str, user_id: int) -> HighlightTag | None:
        return self.db.query(HighlightTag).filter(
            HighlightTag.book_id == book_id,
            HighlightTag.name == name,
            HighlightTag.user_id == user_id  # NEW
        ).first()

    def create(self, book_id: int, name: str, user_id: int, tag_group_id: int | None = None) -> HighlightTag:
        tag = HighlightTag(
            book_id=book_id,
            name=name,
            user_id=user_id,  # NEW
            tag_group_id=tag_group_id
        )
        self.db.add(tag)
        self.db.flush()
        return tag

    def get_by_book_id(self, book_id: int, user_id: int) -> list[HighlightTag]:
        return self.db.query(HighlightTag).filter(
            HighlightTag.book_id == book_id,
            HighlightTag.user_id == user_id
        ).all()
```

### 4.6 Other Repository Updates

The following repositories verify ownership through book relationship (no direct user_id needed):

- **ChapterRepository**: Verify through book ownership
- **BookmarkRepository**: Verify through book/highlight ownership

```python
def get_by_id_for_user(self, chapter_id: int, user_id: int) -> Chapter | None:
    return self.db.query(Chapter).join(Book).filter(
        Chapter.id == chapter_id,
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
5. Add `user_id` column to `highlights` table (nullable initially)
6. Add `user_id` column to `highlight_tags` table (nullable initially)
7. Update all existing records to belong to admin user (user_id=1)
8. Make `user_id` columns NOT NULL
9. Add foreign key constraints
10. Update unique constraints:
    - Drop old constraint on tags.name, add `(user_id, name)`
    - Drop old constraint on highlight_tags `(book_id, name)`, add `(user_id, book_id, name)`
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

    # 3. Add user_id columns (nullable first)
    op.add_column("books", sa.Column("user_id", sa.Integer(), nullable=True))
    op.add_column("tags", sa.Column("user_id", sa.Integer(), nullable=True))
    op.add_column("highlights", sa.Column("user_id", sa.Integer(), nullable=True))
    op.add_column("highlight_tags", sa.Column("user_id", sa.Integer(), nullable=True))

    # 4. Migrate existing data to admin user
    op.execute("UPDATE books SET user_id = 1 WHERE user_id IS NULL")
    op.execute("UPDATE tags SET user_id = 1 WHERE user_id IS NULL")
    op.execute("UPDATE highlights SET user_id = 1 WHERE user_id IS NULL")
    op.execute("UPDATE highlight_tags SET user_id = 1 WHERE user_id IS NULL")

    # 5. Make user_id NOT NULL
    op.alter_column("books", "user_id", nullable=False)
    op.alter_column("tags", "user_id", nullable=False)
    op.alter_column("highlights", "user_id", nullable=False)
    op.alter_column("highlight_tags", "user_id", nullable=False)

    # 6. Add foreign key constraints
    op.create_foreign_key(
        "fk_books_user_id", "books", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_tags_user_id", "tags", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_highlights_user_id", "highlights", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_highlight_tags_user_id", "highlight_tags", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )

    # 7. Update unique constraints
    # Tags: Drop old constraint (name only), add new (user_id, name)
    op.drop_constraint("uq_tags_name", "tags", type_="unique")  # May need to check actual name
    op.create_unique_constraint("uq_tag_user_name", "tags", ["user_id", "name"])

    # HighlightTags: Drop old constraint (book_id, name), add new (user_id, book_id, name)
    op.drop_constraint("uq_highlight_tag_book_name", "highlight_tags", type_="unique")
    op.create_unique_constraint(
        "uq_highlight_tag_user_book_name", "highlight_tags", ["user_id", "book_id", "name"]
    )

    # 8. Add indexes
    op.create_index(op.f("ix_books_user_id"), "books", ["user_id"])
    op.create_index(op.f("ix_tags_user_id"), "tags", ["user_id"])
    op.create_index(op.f("ix_highlights_user_id"), "highlights", ["user_id"])
    op.create_index(op.f("ix_highlight_tags_user_id"), "highlight_tags", ["user_id"])


def downgrade() -> None:
    # Remove indexes
    op.drop_index(op.f("ix_highlight_tags_user_id"), table_name="highlight_tags")
    op.drop_index(op.f("ix_highlights_user_id"), table_name="highlights")
    op.drop_index(op.f("ix_tags_user_id"), table_name="tags")
    op.drop_index(op.f("ix_books_user_id"), table_name="books")

    # Restore old constraints
    op.drop_constraint("uq_highlight_tag_user_book_name", "highlight_tags", type_="unique")
    op.create_unique_constraint("uq_highlight_tag_book_name", "highlight_tags", ["book_id", "name"])

    op.drop_constraint("uq_tag_user_name", "tags", type_="unique")
    op.create_unique_constraint("uq_tags_name", "tags", ["name"])

    # Remove foreign keys
    op.drop_constraint("fk_highlight_tags_user_id", "highlight_tags", type_="foreignkey")
    op.drop_constraint("fk_highlights_user_id", "highlights", type_="foreignkey")
    op.drop_constraint("fk_tags_user_id", "tags", type_="foreignkey")
    op.drop_constraint("fk_books_user_id", "books", type_="foreignkey")

    # Remove user_id columns
    op.drop_column("highlight_tags", "user_id")
    op.drop_column("highlights", "user_id")
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
   - Add relationships to Book, Tag, Highlight, and HighlightTag

2. **Update Book model** (`models.py`)
   - Add user_id foreign key
   - Add user relationship

3. **Update Highlight model** (`models.py`)
   - Add user_id foreign key
   - Add user relationship

4. **Update HighlightTag model** (`models.py`)
   - Add user_id foreign key
   - Add user relationship
   - Update __table_args__ with new unique constraint `(user_id, book_id, name)`

5. **Update Tag model** (`models.py`)
   - Add user_id foreign key
   - Add user relationship
   - Update __table_args__ with new unique constraint `(user_id, name)`

6. **Create migration file** (`alembic/versions/013_add_users_table.py`)
   - Follow the migration strategy above

7. **Create UserRepository** (`repositories/user_repository.py`)
   - Basic CRUD operations
   - get_or_create_default_admin method

8. **Update BookRepository** (`repositories/book_repository.py`)
   - Add user_id parameter to all methods
   - Update queries to filter by user_id

9. **Update HighlightRepository** (`repositories/highlight_repository.py`)
   - Add user_id parameter to create and query methods
   - Update queries to filter by user_id directly

10. **Update HighlightTagRepository** (`repositories/highlight_tag_repository.py`)
    - Add user_id parameter to all methods
    - Update queries to filter by user_id

11. **Update TagRepository** (`repositories/tag_repository.py`)
    - Add user_id parameter to all methods
    - Update queries to filter by user_id

12. **Update other repositories** (ChapterRepository, BookmarkRepository)
    - Add user ownership verification through book joins

13. **Update Pydantic schemas** (`schemas/`)
    - Add UserCreate, UserResponse schemas

14. **Run and test migration**
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
- Test Highlight model with user_id
- Test HighlightTag model with new unique constraint `(user_id, book_id, name)`
- Test Tag model with new unique constraint `(user_id, name)`
- Test that two users can have tags with the same name
- Test that two users can have highlight tags with the same name in the same book
- Test that two users can have books with same title/author
- Test cascade delete (deleting user deletes their books, highlights, tags, highlight_tags)

### 7.3 Repository Tests

- Test BookRepository with user_id filtering
- Test HighlightRepository with user_id filtering
- Test HighlightTagRepository with user_id filtering
- Test TagRepository with user_id filtering
- Test that users cannot access other users' data

---

## Summary

### Files to Create
- `backend/src/repositories/user_repository.py`
- `backend/alembic/versions/013_add_users_table.py`

### Files to Modify
- `backend/src/models.py` (add User model, update Book, Highlight, HighlightTag, and Tag)
- `backend/src/repositories/__init__.py` (export UserRepository)
- `backend/src/repositories/book_repository.py` (add user_id)
- `backend/src/repositories/highlight_repository.py` (add user_id)
- `backend/src/repositories/highlight_tag_repository.py` (add user_id)
- `backend/src/repositories/tag_repository.py` (add user_id)
- `backend/src/schemas/` (add user schemas if needed)

### Database Changes
- New table: `users`
- Modified table: `books` (add user_id FK)
- Modified table: `highlights` (add user_id FK)
- Modified table: `highlight_tags` (add user_id FK, change unique constraint to `(user_id, book_id, name)`)
- Modified table: `tags` (add user_id FK, change unique constraint to `(user_id, name)`)

### Data Migration
- All existing books → admin user (id=1)
- All existing highlights → admin user (id=1)
- All existing highlight_tags → admin user (id=1)
- All existing tags → admin user (id=1)
