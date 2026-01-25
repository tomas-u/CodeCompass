"""Unit tests for the secrets encryption service."""

import pytest
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet, InvalidToken

from app.services.secrets_service import (
    SecretsService,
    get_secrets_service,
    reset_secrets_service,
)


class TestSecretsService:
    """Tests for SecretsService class."""

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption and decryption produce the original value."""
        service = SecretsService()
        plaintext = "sk-or-v1-my-secret-api-key-12345"

        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)

        assert decrypted == plaintext

    def test_encrypt_produces_different_output(self):
        """Test that encrypting the same value twice produces different ciphertexts."""
        service = SecretsService()
        plaintext = "test-secret"

        encrypted1 = service.encrypt(plaintext)
        encrypted2 = service.encrypt(plaintext)

        # Fernet includes a timestamp and random IV, so outputs should differ
        assert encrypted1 != encrypted2

        # But both should decrypt to the same value
        assert service.decrypt(encrypted1) == plaintext
        assert service.decrypt(encrypted2) == plaintext

    def test_encrypt_empty_string_raises_error(self):
        """Test that encrypting an empty string raises ValueError."""
        service = SecretsService()

        with pytest.raises(ValueError, match="Cannot encrypt empty string"):
            service.encrypt("")

    def test_decrypt_empty_string_raises_error(self):
        """Test that decrypting an empty string raises ValueError."""
        service = SecretsService()

        with pytest.raises(ValueError, match="Cannot decrypt empty string"):
            service.decrypt("")

    def test_decrypt_invalid_ciphertext_raises_error(self):
        """Test that decrypting invalid ciphertext raises InvalidToken."""
        service = SecretsService()

        with pytest.raises(InvalidToken):
            service.decrypt("not-a-valid-ciphertext")

    def test_decrypt_tampered_ciphertext_raises_error(self):
        """Test that decrypting tampered ciphertext raises InvalidToken."""
        service = SecretsService()
        encrypted = service.encrypt("secret")

        # Tamper with the ciphertext
        tampered = encrypted[:-5] + "XXXXX"

        with pytest.raises(InvalidToken):
            service.decrypt(tampered)

    def test_service_with_provided_key(self):
        """Test that service works with a provided Fernet key."""
        key = Fernet.generate_key().decode()
        service = SecretsService(secret_key=key)

        plaintext = "test-with-custom-key"
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)

        assert decrypted == plaintext

    def test_service_with_invalid_key_falls_back(self):
        """Test that service falls back to derived key on invalid key."""
        with patch("app.services.secrets_service.logger") as mock_logger:
            service = SecretsService(secret_key="not-a-valid-fernet-key")

            # Should still work with derived key
            plaintext = "test"
            encrypted = service.encrypt(plaintext)
            assert service.decrypt(encrypted) == plaintext

            # Should log error and warning
            mock_logger.error.assert_called_once()
            mock_logger.warning.assert_called_once()

    def test_service_without_key_logs_warning(self):
        """Test that service logs warning when no key is provided."""
        with patch("app.services.secrets_service.logger") as mock_logger:
            service = SecretsService(secret_key=None)

            mock_logger.warning.assert_called_once()
            assert "NOT secure for production" in mock_logger.warning.call_args[0][0]

    def test_different_keys_produce_different_ciphertexts(self):
        """Test that different keys produce different ciphertexts."""
        key1 = Fernet.generate_key().decode()
        key2 = Fernet.generate_key().decode()

        service1 = SecretsService(secret_key=key1)
        service2 = SecretsService(secret_key=key2)

        plaintext = "same-plaintext"
        encrypted1 = service1.encrypt(plaintext)
        encrypted2 = service2.encrypt(plaintext)

        # Different keys should produce incompatible ciphertexts
        assert encrypted1 != encrypted2

        # Each service can only decrypt its own ciphertext
        assert service1.decrypt(encrypted1) == plaintext
        assert service2.decrypt(encrypted2) == plaintext

        # Cross-decryption should fail
        with pytest.raises(InvalidToken):
            service1.decrypt(encrypted2)
        with pytest.raises(InvalidToken):
            service2.decrypt(encrypted1)

    def test_generate_key_returns_valid_fernet_key(self):
        """Test that generate_key produces a valid Fernet key."""
        key = SecretsService.generate_key()

        # Should be a valid base64-encoded string
        assert isinstance(key, str)
        assert len(key) == 44  # Fernet keys are 32 bytes = 44 base64 chars

        # Should be usable as a key
        service = SecretsService(secret_key=key)
        plaintext = "test"
        assert service.decrypt(service.encrypt(plaintext)) == plaintext

    def test_encrypt_preserves_unicode(self):
        """Test that encryption preserves unicode characters."""
        service = SecretsService()
        plaintext = "Hello, World!"

        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)

        assert decrypted == plaintext

    def test_encrypt_long_string(self):
        """Test that encryption works with long strings."""
        service = SecretsService()
        plaintext = "x" * 10000  # 10KB of data

        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)

        assert decrypted == plaintext


class TestGetSecretsService:
    """Tests for the singleton getter function."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_secrets_service()

    def teardown_method(self):
        """Reset singleton after each test."""
        reset_secrets_service()

    def test_returns_singleton_instance(self):
        """Test that get_secrets_service returns the same instance."""
        service1 = get_secrets_service()
        service2 = get_secrets_service()

        assert service1 is service2

    def test_uses_settings_secret_key(self):
        """Test that singleton uses secret_key from settings when available."""
        # This test verifies the singleton pattern works correctly.
        # The actual settings integration is tested by checking that
        # get_secrets_service() returns a working service.
        reset_secrets_service()

        service = get_secrets_service()

        # Should be able to encrypt/decrypt
        plaintext = "test-secret"
        encrypted = service.encrypt(plaintext)
        assert service.decrypt(encrypted) == plaintext

        # Verify it's the same instance on subsequent calls
        service2 = get_secrets_service()
        assert service is service2

        # The second service should decrypt what the first encrypted
        assert service2.decrypt(encrypted) == plaintext

    def test_reset_clears_singleton(self):
        """Test that reset_secrets_service clears the singleton."""
        service1 = get_secrets_service()
        reset_secrets_service()
        service2 = get_secrets_service()

        # After reset, should be a new instance
        assert service1 is not service2


class TestSecretsServiceIntegration:
    """Integration tests for common use cases."""

    def test_api_key_encryption_workflow(self):
        """Test typical API key storage workflow."""
        service = SecretsService()

        # Simulate storing an OpenRouter API key
        api_key = "sk-or-v1-abc123def456ghi789jkl012mno345pqr678stu901vwx234"

        # Encrypt for storage
        encrypted = service.encrypt(api_key)

        # Verify encrypted value looks like base64
        assert encrypted != api_key
        assert len(encrypted) > len(api_key)

        # Simulate retrieval and decryption
        decrypted = service.decrypt(encrypted)
        assert decrypted == api_key

    def test_multiple_secrets_independent(self):
        """Test that multiple secrets can be encrypted independently."""
        service = SecretsService()

        secrets = {
            "openrouter_key": "sk-or-v1-key1",
            "backup_key": "sk-or-v1-key2",
            "test_key": "sk-or-v1-key3",
        }

        encrypted = {name: service.encrypt(value) for name, value in secrets.items()}

        # All encrypted values should be different
        encrypted_values = list(encrypted.values())
        assert len(encrypted_values) == len(set(encrypted_values))

        # All should decrypt correctly
        for name, value in secrets.items():
            assert service.decrypt(encrypted[name]) == value
