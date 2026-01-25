"""Secrets encryption service for API keys and sensitive data."""

import base64
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

# Constants
_PBKDF2_ITERATIONS = 480_000
_SALT = b"codecompass-secrets-salt-v1"  # Fixed salt for key derivation
_DEFAULT_PASSWORD = "codecompass-development-key"


class SecretsService:
    """Service for encrypting and decrypting sensitive data.

    Uses Fernet symmetric encryption (AES-128-CBC with HMAC for authentication).
    Keys can be provided directly or derived from a password using PBKDF2.

    Example:
        >>> secrets = SecretsService()
        >>> encrypted = secrets.encrypt("my-api-key")
        >>> decrypted = secrets.decrypt(encrypted)
        >>> assert decrypted == "my-api-key"
    """

    def __init__(self, secret_key: Optional[str] = None):
        """Initialize the secrets service.

        Args:
            secret_key: A Fernet-compatible key (base64-encoded 32 bytes).
                       If not provided, derives a key from a default password
                       and logs a warning.
        """
        if secret_key:
            # Use provided key directly
            try:
                self._fernet = Fernet(secret_key.encode() if isinstance(secret_key, str) else secret_key)
            except Exception as e:
                logger.error("Invalid secret key format, falling back to derived key")
                self._fernet = self._create_fernet_from_password(_DEFAULT_PASSWORD)
                logger.warning(
                    "Using derived encryption key. Set CODECOMPASS_SECRET_KEY "
                    "environment variable for production use."
                )
        else:
            # Derive key from default password
            self._fernet = self._create_fernet_from_password(_DEFAULT_PASSWORD)
            logger.warning(
                "No CODECOMPASS_SECRET_KEY configured. Using derived encryption key. "
                "This is NOT secure for production. Set CODECOMPASS_SECRET_KEY "
                "environment variable with a Fernet key."
            )

    def _create_fernet_from_password(self, password: str) -> Fernet:
        """Derive a Fernet instance from a password using PBKDF2.

        Args:
            password: The password to derive the key from.

        Returns:
            A Fernet instance with the derived key.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=_SALT,
            iterations=_PBKDF2_ITERATIONS,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string.

        Args:
            plaintext: The string to encrypt.

        Returns:
            Base64-encoded ciphertext that can be safely stored.

        Raises:
            ValueError: If plaintext is empty.
        """
        if not plaintext:
            raise ValueError("Cannot encrypt empty string")

        ciphertext = self._fernet.encrypt(plaintext.encode())
        return ciphertext.decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a ciphertext string.

        Args:
            ciphertext: Base64-encoded ciphertext from encrypt().

        Returns:
            The original plaintext string.

        Raises:
            ValueError: If ciphertext is empty.
            InvalidToken: If ciphertext is invalid or tampered with.
        """
        if not ciphertext:
            raise ValueError("Cannot decrypt empty string")

        plaintext = self._fernet.decrypt(ciphertext.encode())
        return plaintext.decode()

    @staticmethod
    def generate_key() -> str:
        """Generate a new Fernet key for configuration.

        Returns:
            A base64-encoded Fernet key suitable for CODECOMPASS_SECRET_KEY.

        Example:
            >>> key = SecretsService.generate_key()
            >>> print(f"CODECOMPASS_SECRET_KEY={key}")
        """
        return Fernet.generate_key().decode()


# Singleton instance
_secrets_service: Optional[SecretsService] = None


def get_secrets_service() -> SecretsService:
    """Get the singleton secrets service instance.

    The service is initialized lazily on first call, using the
    CODECOMPASS_SECRET_KEY from settings if available.

    Returns:
        The SecretsService singleton instance.
    """
    global _secrets_service

    if _secrets_service is None:
        from app.config import settings
        _secrets_service = SecretsService(secret_key=settings.secret_key)

    return _secrets_service


def reset_secrets_service() -> None:
    """Reset the singleton instance. Useful for testing."""
    global _secrets_service
    _secrets_service = None


# Re-export InvalidToken for consumers
__all__ = ["SecretsService", "get_secrets_service", "reset_secrets_service", "InvalidToken"]
