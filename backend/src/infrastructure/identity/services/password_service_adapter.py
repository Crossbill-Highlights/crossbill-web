from src.infrastructure.identity.services import password_service


class PasswordServiceAdapter:
    """Adapter wrapping password service functions for DI."""

    def hash_password(self, plain_password: str) -> str:
        return password_service.hash_password(plain_password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return password_service.verify_password(plain_password, hashed_password)

    def get_dummy_hash(self) -> str:
        return password_service.get_dummy_hash()
