"""Unit tests for the settings service."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from dataclasses import dataclass

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.services.settings_service import SettingsService
from app.services.secrets_service import SecretsService
from app.schemas.settings import ProviderType


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    from app.models import settings  # noqa: F401

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
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
def service(db_session, secrets_service):
    """Create a settings service with test dependencies."""
    return SettingsService(db=db_session, secrets=secrets_service)


class TestValidateBaseUrl:
    """Tests for validate_base_url method."""

    def test_valid_http_url(self, service):
        """Test valid HTTP URL passes validation."""
        valid, error = service.validate_base_url("http://localhost:11434")
        assert valid is True
        assert error is None

    def test_valid_https_url(self, service):
        """Test valid HTTPS URL passes validation."""
        valid, error = service.validate_base_url("https://api.openrouter.ai/v1")
        assert valid is True
        assert error is None

    def test_empty_url(self, service):
        """Test empty URL fails validation."""
        valid, error = service.validate_base_url("")
        assert valid is False
        assert "required" in error.lower()

    def test_invalid_scheme(self, service):
        """Test URL with invalid scheme fails."""
        valid, error = service.validate_base_url("ftp://localhost:11434")
        assert valid is False
        assert "http or https" in error.lower()

    def test_missing_host(self, service):
        """Test URL without host fails."""
        valid, error = service.validate_base_url("http://")
        assert valid is False
        assert "valid host" in error.lower()

    def test_blocked_ngrok_url(self, service):
        """Test ngrok URLs are blocked."""
        valid, error = service.validate_base_url("https://my-tunnel.ngrok.io")
        assert valid is False
        assert "ngrok" in error.lower()

    def test_blocked_ngrok_app_url(self, service):
        """Test ngrok.app URLs are blocked."""
        valid, error = service.validate_base_url("https://my-tunnel.ngrok.app")
        assert valid is False
        assert "ngrok" in error.lower()

    def test_blocked_localtunnel_url(self, service):
        """Test localtunnel URLs are blocked."""
        valid, error = service.validate_base_url("https://my-tunnel.localtunnel.me")
        assert valid is False
        assert "localtunnel" in error.lower()


class TestValidateModelName:
    """Tests for validate_model_name method."""

    def test_valid_simple_name(self, service):
        """Test simple model name passes."""
        valid, error = service.validate_model_name("llama3")
        assert valid is True
        assert error is None

    def test_valid_name_with_version(self, service):
        """Test model name with version passes."""
        valid, error = service.validate_model_name("qwen2.5-coder:7b")
        assert valid is True
        assert error is None

    def test_valid_name_with_slash(self, service):
        """Test model name with slash (OpenRouter) passes."""
        valid, error = service.validate_model_name("anthropic/claude-3-haiku")
        assert valid is True
        assert error is None

    def test_empty_name(self, service):
        """Test empty name fails."""
        valid, error = service.validate_model_name("")
        assert valid is False
        assert "required" in error.lower()

    def test_name_too_long(self, service):
        """Test name exceeding max length fails."""
        valid, error = service.validate_model_name("x" * 201)
        assert valid is False
        assert "too long" in error.lower()

    def test_name_with_invalid_chars(self, service):
        """Test name with invalid characters fails."""
        valid, error = service.validate_model_name("model<script>")
        assert valid is False
        assert "invalid characters" in error.lower()


class TestValidateOpenRouterKey:
    """Tests for validate_openrouter_key method."""

    def test_valid_key(self, service):
        """Test valid OpenRouter key passes."""
        valid, error = service.validate_openrouter_key("sk-or-v1-abcdefghijklmnop")
        assert valid is True
        assert error is None

    def test_empty_key(self, service):
        """Test empty key fails."""
        valid, error = service.validate_openrouter_key("")
        assert valid is False
        assert "required" in error.lower()

    def test_wrong_prefix(self, service):
        """Test key with wrong prefix fails."""
        valid, error = service.validate_openrouter_key("sk-test-abcdefghijklmnop")
        assert valid is False
        assert "sk-or-" in error

    def test_key_too_short(self, service):
        """Test key that's too short fails."""
        valid, error = service.validate_openrouter_key("sk-or-short")
        assert valid is False
        assert "too short" in error.lower()


# Helper dataclass for mocking ModelInfo
@dataclass
class MockModelInfo:
    """Mock model info for testing."""
    name: str
    size: int = 0
    modified_at: str = ""
    digest: str = ""
    details: dict = None


@dataclass
class MockOpenRouterModelInfo:
    """Mock OpenRouter model info for testing."""
    id: str
    name: str
    context_length: int
    pricing: dict
    description: str = None


class TestTestConnection:
    """Tests for test_connection method."""

    @pytest.mark.asyncio
    @patch("app.services.settings_service.OllamaProvider")
    async def test_ollama_connection_success(self, mock_provider_class, service):
        """Test successful Ollama connection."""
        mock_provider = MagicMock()
        mock_provider.health_check = AsyncMock(return_value=True)
        mock_provider.list_models = AsyncMock(
            return_value=[MockModelInfo(name="qwen2.5-coder:7b")]
        )
        mock_provider.generate = AsyncMock(return_value=MagicMock(content="test"))
        mock_provider_class.return_value = mock_provider

        result = await service.test_connection(
            provider_type=ProviderType.OLLAMA_CONTAINER,
            model="qwen2.5-coder:7b",
            base_url="http://localhost:11434",
        )

        assert result.valid is True
        assert result.provider_status == "ready"
        assert result.model_available is True

    @pytest.mark.asyncio
    @patch("app.services.settings_service.OllamaProvider")
    async def test_ollama_connection_unavailable(self, mock_provider_class, service):
        """Test Ollama connection when service unavailable."""
        mock_provider = MagicMock()
        mock_provider.health_check = AsyncMock(return_value=False)
        mock_provider_class.return_value = mock_provider

        result = await service.test_connection(
            provider_type=ProviderType.OLLAMA_CONTAINER,
            model="qwen2.5-coder:7b",
            base_url="http://localhost:11434",
        )

        assert result.valid is False
        assert result.provider_status == "unavailable"

    @pytest.mark.asyncio
    async def test_ollama_connection_invalid_url(self, service):
        """Test Ollama connection with invalid URL."""
        result = await service.test_connection(
            provider_type=ProviderType.OLLAMA_EXTERNAL,
            model="llama3:8b",
            base_url="not-a-valid-url",
        )

        assert result.valid is False
        assert "URL" in result.error

    @pytest.mark.asyncio
    async def test_openrouter_missing_key(self, service):
        """Test OpenRouter connection without API key."""
        result = await service.test_connection(
            provider_type=ProviderType.OPENROUTER_BYOK,
            model="anthropic/claude-3-haiku",
        )

        assert result.valid is False
        assert "API key" in result.error

    @pytest.mark.asyncio
    async def test_openrouter_invalid_key_format(self, service):
        """Test OpenRouter connection with invalid key format."""
        result = await service.test_connection(
            provider_type=ProviderType.OPENROUTER_BYOK,
            model="anthropic/claude-3-haiku",
            api_key="invalid-key",
        )

        assert result.valid is False
        assert "sk-or-" in result.error

    @pytest.mark.asyncio
    @patch("app.services.settings_service.OpenRouterProvider")
    async def test_openrouter_connection_success(self, mock_provider_class, service):
        """Test successful OpenRouter connection."""
        mock_provider = MagicMock()
        mock_provider.health_check = AsyncMock(return_value=True)
        mock_provider.list_models_detailed = AsyncMock(
            return_value=[
                MockOpenRouterModelInfo(
                    id="anthropic/claude-3-haiku",
                    name="Claude 3 Haiku",
                    context_length=200000,
                    pricing={"prompt": 0.00025, "completion": 0.00125},
                )
            ]
        )
        mock_provider.close = AsyncMock()
        mock_provider_class.return_value = mock_provider

        result = await service.test_connection(
            provider_type=ProviderType.OPENROUTER_BYOK,
            model="anthropic/claude-3-haiku",
            api_key="sk-or-v1-valid-test-key",
        )

        assert result.valid is True
        assert result.provider_status == "ready"
        assert result.model_available is True


class TestListOpenRouterModels:
    """Tests for list_openrouter_models method."""

    @pytest.mark.asyncio
    async def test_invalid_key_format(self, service):
        """Test listing models with invalid key format raises."""
        with pytest.raises(ValueError, match="sk-or-"):
            await service.list_openrouter_models("invalid-key")

    @pytest.mark.asyncio
    @patch("app.services.settings_service.OpenRouterProvider")
    async def test_list_models_success(self, mock_provider_class, service):
        """Test successful model listing."""
        mock_provider = MagicMock()
        mock_provider.list_models_detailed = AsyncMock(
            return_value=[
                MockOpenRouterModelInfo(
                    id="anthropic/claude-3-haiku",
                    name="Claude 3 Haiku",
                    context_length=200000,
                    pricing={"prompt": 0.00025, "completion": 0.00125},
                    description="Fast and affordable",
                ),
                MockOpenRouterModelInfo(
                    id="openai/gpt-4",
                    name="GPT-4",
                    context_length=8192,
                    pricing={"prompt": 0.03, "completion": 0.06},
                ),
            ]
        )
        mock_provider.close = AsyncMock()
        mock_provider_class.return_value = mock_provider

        models = await service.list_openrouter_models("sk-or-v1-valid-key-long-enough")

        assert len(models) == 2
        assert models[0].id == "anthropic/claude-3-haiku"
        assert models[0].provider == "anthropic"
        assert models[1].provider == "openai"
