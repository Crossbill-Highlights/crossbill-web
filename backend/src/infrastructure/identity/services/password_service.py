"""Password hashing and verification service."""

from pwdlib import PasswordHash

from src.config import get_settings

settings = get_settings()
PASSWORD_PEPPER = settings.PASSWORD_PEPPER
DUMMY_HASH = "fasdflkdfjdlkfjlfdjsdlkasfsf"

password_hash = PasswordHash.recommended()


def hash_password(plain_password: str) -> str:
    """Hash a plain password for storage with pepper."""
    peppered_password = plain_password + PASSWORD_PEPPER
    return password_hash.hash(peppered_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Tries with pepper first (current standard), then falls back to non-peppered
    for backward compatibility with existing passwords.

    DEPRECATED: Non-peppered password verification will be removed in a future release.
    Users should change their passwords to migrate to peppered hashes.
    """
    # Try with pepper first (current standard)
    peppered_password = plain_password + PASSWORD_PEPPER
    if password_hash.verify(peppered_password, hashed_password):
        return True

    # Fallback to non-peppered for backward compatibility (DEPRECATED)
    # This allows existing users to login and change their password
    return password_hash.verify(plain_password, hashed_password)


def get_dummy_hash() -> str:
    """Get a dummy hash for timing attack prevention."""
    return DUMMY_HASH
