"""Integration tests for settings API endpoints.

Uses fixtures from conftest.py:
- client: FastAPI test client with test database
- test_db: Test database session
"""

from unittest.mock import patch, AsyncMock, MagicMock
from dataclasses import dataclass


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


class TestGetLLMConfig:
    """Tests for GET /api/settings/llm endpoint."""

    def test_get_llm_config_returns_defaults(self, client):
        """Test that default settings are returned when none exist."""
        response = client.get("/api/settings/llm")

        assert response.status_code == 200
        data = response.json()
        assert data["provider_type"] == "ollama_container"
        assert data["model"] == "qwen2.5-coder:7b"
        assert data["has_api_key"] is False
        assert data["status"] == "unknown"

    def test_get_llm_config_returns_saved_settings(self, client):
        """Test that saved settings are returned."""
        # First save some settings
        update_data = {
            "provider_type": "ollama_external",
            "model": "llama3:8b",
            "base_url": "http://localhost:11434",
        }
        client.put("/api/settings/llm", json=update_data)

        # Then get them
        response = client.get("/api/settings/llm")

        assert response.status_code == 200
        data = response.json()
        assert data["provider_type"] == "ollama_external"
        assert data["model"] == "llama3:8b"
        assert data["base_url"] == "http://localhost:11434"


class TestUpdateLLMConfig:
    """Tests for PUT /api/settings/llm endpoint."""

    def test_update_llm_config_success(self, client):
        """Test successful update of LLM configuration."""
        update_data = {
            "provider_type": "ollama_container",
            "model": "qwen2.5-coder:7b",
            "base_url": "http://localhost:11434",
        }

        response = client.put("/api/settings/llm", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["provider_type"] == "ollama_container"
        assert data["model"] == "qwen2.5-coder:7b"
        assert data["reloaded"] is True

    def test_update_llm_config_with_api_key(self, client):
        """Test update with API key (gets encrypted)."""
        update_data = {
            "provider_type": "openrouter_byok",
            "model": "anthropic/claude-3-haiku",
            "api_key": "sk-or-v1-test-key-12345",
        }

        response = client.put("/api/settings/llm", json=update_data)

        assert response.status_code == 200

        # Verify API key is stored (but not returned)
        get_response = client.get("/api/settings/llm")
        assert get_response.json()["has_api_key"] is True

    def test_update_llm_config_invalid_provider(self, client):
        """Test update with invalid provider type."""
        update_data = {
            "provider_type": "invalid_provider",
            "model": "test-model",
        }

        response = client.put("/api/settings/llm", json=update_data)

        assert response.status_code == 422  # Validation error

    def test_update_llm_config_empty_model(self, client):
        """Test update with empty model name."""
        update_data = {
            "provider_type": "ollama_container",
            "model": "",
        }

        response = client.put("/api/settings/llm", json=update_data)

        assert response.status_code == 422  # Validation error


class TestValidateLLMConfig:
    """Tests for POST /api/settings/llm/validate endpoint."""

    @patch("app.services.settings_service.OllamaProvider")
    def test_validate_ollama_success(self, mock_provider_class, client):
        """Test successful validation of Ollama config."""
        # Setup mock
        mock_provider = MagicMock()
        mock_provider.health_check = AsyncMock(return_value=True)
        mock_provider.list_models = AsyncMock(
            return_value=[MockModelInfo(name="qwen2.5-coder:7b")]
        )
        mock_provider.generate = AsyncMock(return_value=MagicMock(content="test"))
        mock_provider_class.return_value = mock_provider

        validate_data = {
            "provider_type": "ollama_container",
            "model": "qwen2.5-coder:7b",
            "base_url": "http://localhost:11434",
        }

        response = client.post("/api/settings/llm/validate", json=validate_data)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["provider_status"] == "ready"
        assert data["model_available"] is True

    @patch("app.services.settings_service.OllamaProvider")
    def test_validate_ollama_unavailable(self, mock_provider_class, client):
        """Test validation when Ollama is unavailable."""
        mock_provider = MagicMock()
        mock_provider.health_check = AsyncMock(return_value=False)
        mock_provider_class.return_value = mock_provider

        validate_data = {
            "provider_type": "ollama_container",
            "model": "qwen2.5-coder:7b",
            "base_url": "http://localhost:11434",
        }

        response = client.post("/api/settings/llm/validate", json=validate_data)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["provider_status"] == "unavailable"

    def test_validate_invalid_url(self, client):
        """Test validation with invalid URL."""
        validate_data = {
            "provider_type": "ollama_external",
            "model": "llama3:8b",
            "base_url": "not-a-valid-url",
        }

        response = client.post("/api/settings/llm/validate", json=validate_data)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "URL" in data["error"]

    def test_validate_blocked_url(self, client):
        """Test validation with blocked tunneling URL."""
        validate_data = {
            "provider_type": "ollama_external",
            "model": "llama3:8b",
            "base_url": "https://my-tunnel.ngrok.io",
        }

        response = client.post("/api/settings/llm/validate", json=validate_data)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "ngrok" in data["error"].lower()

    def test_validate_openrouter_missing_key(self, client):
        """Test validation of OpenRouter without API key."""
        validate_data = {
            "provider_type": "openrouter_byok",
            "model": "anthropic/claude-3-haiku",
        }

        response = client.post("/api/settings/llm/validate", json=validate_data)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "API key" in data["error"]

    def test_validate_openrouter_invalid_key_format(self, client):
        """Test validation of OpenRouter with invalid key format."""
        validate_data = {
            "provider_type": "openrouter_byok",
            "model": "anthropic/claude-3-haiku",
            "api_key": "invalid-key-format",
        }

        response = client.post("/api/settings/llm/validate", json=validate_data)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "sk-or-" in data["error"]

    @patch("app.services.settings_service.OpenRouterProvider")
    def test_validate_openrouter_success(self, mock_provider_class, client):
        """Test successful validation of OpenRouter config."""
        mock_provider = MagicMock()
        mock_provider.health_check = AsyncMock(return_value=True)
        mock_provider.list_models_detailed = AsyncMock(
            return_value=[
                MockOpenRouterModelInfo(
                    id="anthropic/claude-3-haiku",
                    name="Claude 3 Haiku",
                    context_length=200000,
                    pricing={"prompt": 0.00025, "completion": 0.00125},
                    description="Fast and affordable",
                )
            ]
        )
        mock_provider.close = AsyncMock()
        mock_provider_class.return_value = mock_provider

        validate_data = {
            "provider_type": "openrouter_byok",
            "model": "anthropic/claude-3-haiku",
            "api_key": "sk-or-v1-valid-test-key-12345",
        }

        response = client.post("/api/settings/llm/validate", json=validate_data)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["model_available"] is True
        assert data["details"]["model_name"] == "Claude 3 Haiku"


class TestListOpenRouterModels:
    """Tests for GET /api/settings/openrouter/models endpoint."""

    def test_list_models_no_key(self, client):
        """Test listing models without API key."""
        response = client.get("/api/settings/openrouter/models")

        assert response.status_code == 400
        assert "API key required" in response.json()["detail"]

    @patch("app.services.settings_service.OpenRouterProvider")
    def test_list_models_with_header_key(self, mock_provider_class, client):
        """Test listing models with API key in header."""
        mock_provider = MagicMock()
        mock_provider.list_models_detailed = AsyncMock(
            return_value=[
                MockOpenRouterModelInfo(
                    id="anthropic/claude-3-haiku",
                    name="Claude 3 Haiku",
                    context_length=200000,
                    pricing={"prompt": 0.00025, "completion": 0.00125},
                    description="Fast and affordable",
                )
            ]
        )
        mock_provider.close = AsyncMock()
        mock_provider_class.return_value = mock_provider

        response = client.get(
            "/api/settings/openrouter/models",
            headers={"X-OpenRouter-Key": "sk-or-v1-valid-key-12345"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["models"]) == 1
        assert data["models"][0]["id"] == "anthropic/claude-3-haiku"

    def test_list_models_invalid_key_format(self, client):
        """Test listing models with invalid key format."""
        response = client.get(
            "/api/settings/openrouter/models",
            headers={"X-OpenRouter-Key": "invalid-key"},
        )

        assert response.status_code == 400
        assert "sk-or-" in response.json()["detail"]

    @patch("app.services.settings_service.OpenRouterProvider")
    def test_list_models_auth_failure(self, mock_provider_class, client):
        """Test listing models with invalid API key."""
        from app.services.llm.openrouter_provider import OpenRouterAuthError

        mock_provider = MagicMock()
        mock_provider.list_models_detailed = AsyncMock(
            side_effect=OpenRouterAuthError("Invalid API key")
        )
        mock_provider.close = AsyncMock()
        mock_provider_class.return_value = mock_provider

        response = client.get(
            "/api/settings/openrouter/models",
            headers={"X-OpenRouter-Key": "sk-or-v1-invalid-key-12345"},
        )

        assert response.status_code == 401
        assert "Authentication failed" in response.json()["detail"]

    def test_list_models_with_stored_key_decryption_failure(self, client, test_db):
        """Test listing models when stored API key cannot be decrypted."""
        from app.models.settings import LLMSettingsModel
        from app.schemas.settings import ProviderType

        # Create settings with corrupted encrypted key
        settings = LLMSettingsModel(
            id="default",
            provider_type=ProviderType.OPENROUTER_BYOK,
            model="test-model",
            api_key_encrypted="corrupted-invalid-encrypted-data",
        )
        test_db.add(settings)
        test_db.commit()

        # Try to list models without header key (should try to use stored key)
        response = client.get("/api/settings/openrouter/models")

        # Should return 500 with helpful error message
        assert response.status_code == 500
        assert "corrupted" in response.json()["detail"].lower()


class TestInputValidation:
    """Tests for input validation across endpoints."""

    def test_model_name_too_long(self, client):
        """Test that overly long model names are rejected."""
        update_data = {
            "provider_type": "ollama_container",
            "model": "x" * 201,  # Exceeds max_length=200
        }

        response = client.put("/api/settings/llm", json=update_data)

        assert response.status_code == 422

    def test_base_url_too_long(self, client):
        """Test that overly long URLs are rejected."""
        update_data = {
            "provider_type": "ollama_external",
            "model": "test-model",
            "base_url": "http://example.com/" + "x" * 500,  # Exceeds max_length=500
        }

        response = client.put("/api/settings/llm", json=update_data)

        assert response.status_code == 422

    def test_api_key_too_long(self, client):
        """Test that overly long API keys are rejected."""
        update_data = {
            "provider_type": "openrouter_byok",
            "model": "test-model",
            "api_key": "sk-or-v1-" + "x" * 1000,  # Exceeds max_length=1000
        }

        response = client.put("/api/settings/llm", json=update_data)

        assert response.status_code == 422

    def test_invalid_api_format(self, client):
        """Test that invalid API format is rejected."""
        update_data = {
            "provider_type": "ollama_external",
            "model": "test-model",
            "api_format": "invalid",  # Must be "ollama" or "openai"
        }

        response = client.put("/api/settings/llm", json=update_data)

        assert response.status_code == 422
