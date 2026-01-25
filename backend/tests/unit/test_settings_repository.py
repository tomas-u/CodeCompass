"""Unit tests for the settings repository."""

import pytest
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.settings import LLMSettingsModel
from app.schemas.settings import ProviderType
from app.repositories.settings_repository import SettingsRepository, DEFAULT_SETTINGS_ID
from app.services.secrets_service import SecretsService, InvalidToken


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def secrets_service():
    """Create a secrets service with a test key."""
    return SecretsService()


@pytest.fixture
def repository(db_session, secrets_service):
    """Create a settings repository with test dependencies."""
    return SettingsRepository(db=db_session, secrets=secrets_service)


class TestGetLLMSettings:
    """Tests for get_llm_settings method."""

    def test_get_llm_settings_none_when_empty(self, repository):
        """Test that get_llm_settings returns None when no settings exist."""
        result = repository.get_llm_settings()
        assert result is None

    def test_get_llm_settings_returns_existing(self, repository, db_session):
        """Test that get_llm_settings returns existing settings."""
        # Create settings directly
        settings = LLMSettingsModel(
            id=DEFAULT_SETTINGS_ID,
            provider_type=ProviderType.OLLAMA_CONTAINER,
            model="test-model",
        )
        db_session.add(settings)
        db_session.commit()

        result = repository.get_llm_settings()

        assert result is not None
        assert result.model == "test-model"


class TestGetOrCreateLLMSettings:
    """Tests for get_or_create_llm_settings method."""

    def test_creates_default_when_none_exist(self, repository):
        """Test that default settings are created when none exist."""
        result = repository.get_or_create_llm_settings()

        assert result is not None
        assert result.id == DEFAULT_SETTINGS_ID
        assert result.provider_type == ProviderType.OLLAMA_CONTAINER
        assert result.model == "qwen2.5-coder:7b"
        assert result.base_url == "http://localhost:11434"

    def test_returns_existing_when_present(self, repository, db_session):
        """Test that existing settings are returned without modification."""
        # Create custom settings
        settings = LLMSettingsModel(
            id=DEFAULT_SETTINGS_ID,
            provider_type=ProviderType.OPENROUTER_BYOK,
            model="custom-model",
            base_url="https://custom.url",
        )
        db_session.add(settings)
        db_session.commit()

        result = repository.get_or_create_llm_settings()

        assert result.provider_type == ProviderType.OPENROUTER_BYOK
        assert result.model == "custom-model"
        assert result.base_url == "https://custom.url"


class TestSaveLLMSettings:
    """Tests for save_llm_settings method."""

    def test_save_settings_all_fields(self, repository):
        """Test saving settings with all fields."""
        result = repository.save_llm_settings(
            provider_type=ProviderType.OLLAMA_EXTERNAL,
            model="llama3:8b",
            base_url="http://192.168.1.100:11434",
            api_format="ollama",
        )

        assert result.provider_type == ProviderType.OLLAMA_EXTERNAL
        assert result.model == "llama3:8b"
        assert result.base_url == "http://192.168.1.100:11434"
        assert result.api_format == "ollama"

    def test_save_settings_encrypts_api_key(self, repository, secrets_service):
        """Test that API key is encrypted when saved."""
        api_key = "sk-test-api-key-12345"

        result = repository.save_llm_settings(
            provider_type=ProviderType.OPENROUTER_BYOK,
            model="anthropic/claude-3-haiku",
            api_key=api_key,
        )

        # API key should be encrypted
        assert result.api_key_encrypted is not None
        assert result.api_key_encrypted != api_key

        # Should be decryptable
        decrypted = secrets_service.decrypt(result.api_key_encrypted)
        assert decrypted == api_key

    def test_save_settings_clears_api_key_with_empty_string(self, repository, db_session):
        """Test that empty string clears the API key."""
        # First save with an API key
        repository.save_llm_settings(
            provider_type=ProviderType.OPENROUTER_BYOK,
            model="test-model",
            api_key="sk-test-key",
        )

        # Then clear it with empty string
        result = repository.save_llm_settings(
            provider_type=ProviderType.OPENROUTER_BYOK,
            model="test-model",
            api_key="",
        )

        assert result.api_key_encrypted is None

    def test_save_settings_preserves_api_key_when_none(self, repository):
        """Test that API key is preserved when not provided in update."""
        # Save with API key
        repository.save_llm_settings(
            provider_type=ProviderType.OPENROUTER_BYOK,
            model="model-1",
            api_key="sk-original-key",
        )

        # Update without providing API key
        result = repository.save_llm_settings(
            provider_type=ProviderType.OPENROUTER_BYOK,
            model="model-2",
            # api_key not provided
        )

        # API key should still be present
        assert result.api_key_encrypted is not None
        assert result.model == "model-2"

    def test_save_settings_resets_health_cache(self, repository, db_session):
        """Test that saving settings resets health check cache."""
        # Create settings with health status
        settings = repository.get_or_create_llm_settings()
        settings.last_health_check = datetime.utcnow()
        settings.last_health_status = True
        db_session.commit()

        # Update settings
        result = repository.save_llm_settings(
            provider_type=ProviderType.OLLAMA_CONTAINER,
            model="new-model",
        )

        # Health cache should be reset
        assert result.last_health_check is None
        assert result.last_health_status is None

    def test_save_settings_updates_existing(self, repository):
        """Test that save updates existing settings."""
        # Create initial settings
        repository.save_llm_settings(
            provider_type=ProviderType.OLLAMA_CONTAINER,
            model="initial-model",
        )

        # Update settings
        result = repository.save_llm_settings(
            provider_type=ProviderType.OPENROUTER_BYOK,
            model="updated-model",
            base_url="https://new.url",
        )

        # Should be updated
        assert result.provider_type == ProviderType.OPENROUTER_BYOK
        assert result.model == "updated-model"
        assert result.base_url == "https://new.url"

        # Should still be only one record
        all_settings = repository.db.query(LLMSettingsModel).all()
        assert len(all_settings) == 1


class TestGetDecryptedApiKey:
    """Tests for get_decrypted_api_key method."""

    def test_get_decrypted_api_key_returns_decrypted(self, repository, secrets_service):
        """Test that decrypted API key is returned."""
        api_key = "sk-my-secret-api-key"
        settings = repository.save_llm_settings(
            provider_type=ProviderType.OPENROUTER_BYOK,
            model="test-model",
            api_key=api_key,
        )

        result = repository.get_decrypted_api_key(settings)

        assert result == api_key

    def test_get_decrypted_api_key_returns_none_when_empty(self, repository):
        """Test that None is returned when no API key is stored."""
        settings = repository.save_llm_settings(
            provider_type=ProviderType.OLLAMA_CONTAINER,
            model="test-model",
        )

        result = repository.get_decrypted_api_key(settings)

        assert result is None

    def test_get_decrypted_api_key_raises_on_corrupted(self, repository, db_session):
        """Test that InvalidToken is raised for corrupted keys."""
        # Create settings with corrupted encrypted key
        settings = LLMSettingsModel(
            id=DEFAULT_SETTINGS_ID,
            provider_type=ProviderType.OPENROUTER_BYOK,
            model="test",
            api_key_encrypted="corrupted-not-valid-encrypted-data",
        )
        db_session.add(settings)
        db_session.commit()

        with pytest.raises(InvalidToken):
            repository.get_decrypted_api_key(settings)


class TestUpdateHealthStatus:
    """Tests for update_health_status method."""

    def test_update_health_status(self, repository):
        """Test updating health status."""
        settings = repository.get_or_create_llm_settings()

        repository.update_health_status(settings, is_healthy=True)

        assert settings.last_health_check is not None
        assert settings.last_health_status is True

    def test_update_health_status_unhealthy(self, repository):
        """Test updating health status to unhealthy."""
        settings = repository.get_or_create_llm_settings()

        repository.update_health_status(settings, is_healthy=False)

        assert settings.last_health_check is not None
        assert settings.last_health_status is False


class TestDeleteLLMSettings:
    """Tests for delete_llm_settings method."""

    def test_delete_existing_settings(self, repository):
        """Test deleting existing settings."""
        repository.save_llm_settings(
            provider_type=ProviderType.OLLAMA_CONTAINER,
            model="test-model",
        )

        result = repository.delete_llm_settings()

        assert result is True
        assert repository.get_llm_settings() is None

    def test_delete_nonexistent_settings(self, repository):
        """Test deleting when no settings exist."""
        result = repository.delete_llm_settings()

        assert result is False


class TestLLMSettingsModel:
    """Tests for LLMSettingsModel."""

    def test_to_dict_excludes_encrypted_key(self, db_session, secrets_service):
        """Test that to_dict excludes the encrypted API key."""
        settings = LLMSettingsModel(
            id="test",
            provider_type=ProviderType.OPENROUTER_BYOK,
            model="test-model",
            api_key_encrypted=secrets_service.encrypt("secret-key"),
        )

        result = settings.to_dict()

        assert "api_key_encrypted" not in result
        assert result["has_api_key"] is True

    def test_to_dict_has_api_key_false(self, db_session):
        """Test that has_api_key is False when no key is stored."""
        settings = LLMSettingsModel(
            id="test",
            provider_type=ProviderType.OLLAMA_CONTAINER,
            model="test-model",
        )

        result = settings.to_dict()

        assert result["has_api_key"] is False

    def test_repr(self, db_session):
        """Test string representation."""
        settings = LLMSettingsModel(
            id="test",
            provider_type=ProviderType.OLLAMA_CONTAINER,
            model="test-model",
        )

        result = repr(settings)

        assert "test" in result
        assert "OLLAMA_CONTAINER" in result
        assert "test-model" in result
