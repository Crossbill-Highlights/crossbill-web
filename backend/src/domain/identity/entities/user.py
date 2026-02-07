"""User entity for identity management."""

from dataclasses import dataclass
from datetime import datetime

from src.domain.common.entity import Entity
from src.domain.common.exceptions import ValidationError
from src.domain.common.value_objects.ids import UserId

# Domain constraints
MAX_EMAIL_LENGTH = 100


@dataclass
class User(Entity[UserId]):
    """
    User entity representing an authenticated user in the system.

    Business Rules:
    - Email must be unique (enforced at repository level)
    - Email must be non-empty and have reasonable length (max MAX_EMAIL_LENGTH chars)
    - Users can exist without passwords (for OAuth/external auth)
    - Password hashing is an infrastructure concern (not stored as plain text)
    """

    id: UserId
    email: str
    hashed_password: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate invariants."""
        if not self.email:
            raise ValidationError("Email cannot be empty", field="email", value=self.email)
        if len(self.email) > MAX_EMAIL_LENGTH:
            raise ValidationError(
                "Email cannot exceed MAX_EMAIL_LENGTH characters", field="email", value=self.email
            )

    def has_password(self) -> bool:
        """Check if this user has a password set."""
        return self.hashed_password is not None

    def update_email(self, new_email: str) -> None:
        """
        Update the user's email address.

        Args:
            new_email: The new email address

        Raises:
            ValidationError: If email is invalid
        """
        if not new_email:
            raise ValidationError("Email cannot be empty", field="email", value=new_email)
        if len(new_email) > MAX_EMAIL_LENGTH:
            raise ValidationError(
                "Email cannot exceed MAX_EMAIL_LENGTH characters", field="email", value=new_email
            )
        self.email = new_email

    def update_password(self, new_hashed_password: str) -> None:
        """
        Update the user's password.

        Args:
            new_hashed_password: The new hashed password (hashing done by infrastructure)
        """
        self.hashed_password = new_hashed_password

    @classmethod
    def create(cls, email: str, hashed_password: str | None = None) -> "User":
        """
        Create a new user.

        Args:
            email: User's email address
            hashed_password: User's hashed password (optional, for OAuth users)

        Returns:
            New User instance

        Raises:
            ValidationError: If email is invalid
        """
        return cls(
            id=UserId.generate(),
            email=email,
            hashed_password=hashed_password,
        )

    @classmethod
    def create_with_id(
        cls,
        id: UserId,
        email: str,
        hashed_password: str | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> "User":
        """
        Reconstitute a user from persistence.

        Args:
            id: Existing user ID
            email: User's email address
            hashed_password: User's hashed password (or None)
            created_at: Timestamp when user was created
            updated_at: Timestamp when user was last updated

        Returns:
            Reconstituted User instance

        Raises:
            ValidationError: If email is invalid
        """
        return cls(
            id=id,
            email=email,
            hashed_password=hashed_password,
            created_at=created_at,
            updated_at=updated_at,
        )
