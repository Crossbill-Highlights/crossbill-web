"""Identity domain exceptions."""

from src.domain.common.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    EntityNotFoundError,
)


class UserNotFoundError(EntityNotFoundError):
    """Raised when a user cannot be found."""

    def __init__(self, user_id: int) -> None:
        super().__init__("User", user_id)


class EmailAlreadyExistsError(ConflictError):
    """Raised when attempting to register with an email that already exists."""

    def __init__(self, email: str) -> None:
        super().__init__(f"Email {email} is already registered", {"email": email})
        self.email = email


class InvalidCredentialsError(AuthenticationError):
    """Raised when authentication fails due to invalid credentials."""

    def __init__(self) -> None:
        super().__init__("Invalid email or password")


class PasswordVerificationError(AuthenticationError):
    """Raised when current password verification fails during password change."""

    def __init__(self) -> None:
        super().__init__("Current password is incorrect")


class RegistrationDisabledError(AuthorizationError):
    """Raised when user registration is disabled via feature flag."""

    def __init__(self) -> None:
        super().__init__("User registration is currently disabled")
