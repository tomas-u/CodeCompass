# CodeCompass LLM Configuration - Product Requirements Document

## Document Info
| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Status** | Draft |
| **Author** | Product Manager |
| **Last Updated** | 2026-01-25 |
| **Related Documents** | 001-PRD_BACKEND_API.md, CLAUDE.md |

---

## 1. Executive Summary

This PRD specifies the comprehensive LLM configuration system for CodeCompass, enabling users to configure and switch between multiple LLM providers seamlessly. The system supports local models (Ollama), external local LLM servers, and cloud providers through OpenRouter.

### Strategic Vision

| Current State | Future State (This PRD) |
|---------------|-------------------------|
| Single Ollama provider hardcoded | 4 provider modes supported |
| Configuration via environment variables | Interactive Settings UI |
| No provider switching at runtime | Hot-reload model switching |
| No API key management | Encrypted secrets storage |
| No hardware awareness | GPU/VRAM detection with recommendations |
| No connection validation | Pre-save connection testing |
| No visual status feedback | Always-visible LLM status indicator |

### Business Value
- **Accessibility:** Users can choose providers based on their hardware and preferences
- **Flexibility:** Support local-first privacy or cloud-powered capability
- **Cost Control:** Users manage their own API keys and usage
- **Developer Experience:** Zero-config defaults with full customization available
- **Reliability:** Connection testing prevents configuration errors

### Provider Modes Overview

| Mode | Provider Type | Use Case | MVP |
|------|--------------|----------|-----|
| 1 | Container Ollama | Default setup, runs with CodeCompass stack | Yes |
| 2 | External Local LLM | User's own LM Studio, llama.cpp, Ollama | Yes |
| 3 | OpenRouter (BYOK) | Cloud with user's API key | Yes |
| 4 | OpenRouter (Managed) | CodeCompass-provided key (future monetization) | Yes |

---

## 2. Provider Types & Configuration

### 2.1 Container Ollama (Default)

**Description:** Ollama running as part of the CodeCompass Docker/Podman compose stack. This is the zero-configuration default for users running the full stack.

**Configuration Schema:**
```python
class OllamaContainerConfig(BaseModel):
    """Configuration for container-based Ollama."""
    provider_type: Literal["ollama_container"] = "ollama_container"
    model: str = "qwen2.5-coder:7b"
    base_url: str = "http://ollama:11434"  # Docker network address
```

**Features:**
- Model pulling/deletion through UI
- Hardware detection (GPU/VRAM in container)
- Model size recommendations based on available resources
- Automatic connection to compose network

**Detection:** Check if `http://ollama:11434` (Docker) or `http://localhost:11434` (host) responds.

---

### 2.2 External Local LLM

**Description:** User's own LLM server running separately - LM Studio, llama.cpp server, vLLM, or external Ollama installation.

**Configuration Schema:**
```python
class ExternalLLMConfig(BaseModel):
    """Configuration for external local LLM server."""
    provider_type: Literal["ollama_external"] = "ollama_external"
    model: str
    base_url: str  # e.g., http://localhost:1234
    api_format: Literal["ollama", "openai"] = "ollama"  # API compatibility mode
```

**Supported Servers:**
| Server | API Format | Default Port | Notes |
|--------|------------|--------------|-------|
| Ollama | ollama | 11434 | Native Ollama API |
| LM Studio | openai | 1234 | OpenAI-compatible |
| llama.cpp server | openai | 8080 | OpenAI-compatible |
| vLLM | openai | 8000 | OpenAI-compatible |
| text-generation-webui | openai | 5000 | OpenAI-compatible |

**Features:**
- Custom base URL configuration
- API format auto-detection with manual override
- Model discovery from server (when supported)
- Connection testing before save

---

### 2.3 OpenRouter (BYOK - Bring Your Own Key)

**Description:** Cloud LLM access through OpenRouter using the user's own API key. Provides access to GPT-4, Claude, Llama, Mistral, and many other models.

**Configuration Schema:**
```python
class OpenRouterBYOKConfig(BaseModel):
    """Configuration for OpenRouter with user's API key."""
    provider_type: Literal["openrouter_byok"] = "openrouter_byok"
    model: str = "anthropic/claude-3.5-sonnet"
    api_key: str  # Encrypted at rest
    base_url: str = "https://openrouter.ai/api/v1"

    # Optional preferences
    allow_fallbacks: bool = True
    require_providers: Optional[List[str]] = None  # e.g., ["anthropic", "openai"]
```

**Features:**
- Model browser with pricing information
- API key validation on entry
- Usage tracking and cost estimation
- Provider preference settings
- Encrypted key storage

**OpenRouter Headers:**
```python
headers = {
    "Authorization": f"Bearer {api_key}",
    "HTTP-Referer": "https://codecompass.dev",
    "X-Title": "CodeCompass",
}
```

---

### 2.4 OpenRouter (Managed Key)

**Description:** Cloud LLM access using a CodeCompass-managed API key. Enables future monetization through usage-based billing.

**Configuration Schema:**
```python
class OpenRouterManagedConfig(BaseModel):
    """Configuration for OpenRouter with managed key."""
    provider_type: Literal["openrouter_managed"] = "openrouter_managed"
    model: str = "anthropic/claude-3-haiku"  # Default to cost-effective model
    # No API key needed - server-side managed
```

**Features:**
- No API key required from user
- Usage tracking per user/project
- Model restrictions based on plan (future)
- Rate limiting (future)

**Note:** MVP implementation will use a shared development key with rate limiting. Production will require user accounts.

---

## 3. User Stories & Acceptance Criteria

### US-1: First-Time Setup

**As a** new user running CodeCompass for the first time,
**I want** the LLM to work automatically with sensible defaults,
**So that** I can start using the chat feature immediately.

**Acceptance Criteria:**
- [ ] Container Ollama auto-detected when running via docker-compose
- [ ] Default model `qwen2.5-coder:7b` pre-selected if available
- [ ] If no model available, prompt to pull recommended model
- [ ] Status indicator shows "Ready" when LLM is configured
- [ ] Chat works without any manual configuration

---

### US-2: Container Ollama Configuration

**As a** user running the full CodeCompass stack,
**I want** to manage Ollama models through the UI,
**So that** I can choose models suited to my hardware.

**Acceptance Criteria:**
- [ ] List all locally available Ollama models
- [ ] Pull new models from Ollama library
- [ ] Delete unused models to free space
- [ ] See model size and resource requirements
- [ ] Hardware detection shows GPU/VRAM available
- [ ] Model recommendations based on hardware
- [ ] Test selected model before saving

---

### US-3: External LLM Server Configuration

**As a** user with my own LLM server (LM Studio, llama.cpp),
**I want** to connect CodeCompass to my existing setup,
**So that** I can leverage my preferred models and hardware.

**Acceptance Criteria:**
- [ ] Enter custom base URL
- [ ] Auto-detect API format (Ollama vs OpenAI-compatible)
- [ ] Manual API format override option
- [ ] Discover available models from server
- [ ] Test connection before saving
- [ ] Clear error messages for connection failures
- [ ] Supports common ports (1234, 8080, 11434)

---

### US-4: OpenRouter Cloud Configuration

**As a** user who wants cloud LLM capabilities,
**I want** to use OpenRouter with my own API key,
**So that** I can access powerful models like GPT-4 and Claude.

**Acceptance Criteria:**
- [ ] Enter and validate OpenRouter API key
- [ ] Browse available models with pricing
- [ ] Filter models by capability (chat, code, long-context)
- [ ] See per-token pricing before selection
- [ ] API key encrypted at rest
- [ ] Key never logged or exposed in errors
- [ ] Test connection validates key and model access

---

### US-5: Hot-Reload Model Switching

**As a** user who has configured an LLM,
**I want** to switch models without restarting the application,
**So that** I can try different models quickly.

**Acceptance Criteria:**
- [ ] Change model selection in settings
- [ ] Click "Apply" to activate new model
- [ ] Next chat message uses new model
- [ ] No application restart required
- [ ] Previous chat history preserved
- [ ] Status indicator updates to show active model

---

### US-6: LLM Status Visibility

**As a** user,
**I want** to see the current LLM status at a glance,
**So that** I know if the AI features are available.

**Acceptance Criteria:**
- [ ] Status indicator always visible in header
- [ ] Shows: Ready (green), Connecting (yellow), Error (red)
- [ ] Hover shows current model name and provider
- [ ] Click opens Settings dialog to LLM tab
- [ ] Error state shows brief error description
- [ ] Automatic reconnection attempts on transient failures

---

### US-7: Hardware Detection & Recommendations

**As a** user setting up container Ollama,
**I want** to see my hardware capabilities and model recommendations,
**So that** I choose a model that runs well on my system.

**Acceptance Criteria:**
- [ ] Detect GPU presence (NVIDIA, AMD, Apple Silicon)
- [ ] Show available VRAM
- [ ] Recommend models based on VRAM
- [ ] Warning when selected model may not fit in VRAM
- [ ] Fallback to CPU-only recommendations if no GPU
- [ ] Show estimated inference speed for recommendations

---

## 4. Settings UI Design

### 4.1 Dialog Structure

The Settings dialog is a modal accessible from the Header settings button. It uses a tabbed interface.

```
+------------------------------------------------------------------+
|  Settings                                              [X] Close  |
+------------------------------------------------------------------+
|  [ LLM ]  [ Embedding ]  [ Analysis ]                             |
+------------------------------------------------------------------+
|                                                                   |
|  (Tab content area - see sections below)                          |
|                                                                   |
|                                                                   |
|                                                                   |
+------------------------------------------------------------------+
|                              [Cancel]  [Test Connection]  [Save]  |
+------------------------------------------------------------------+
```

### 4.2 LLM Settings Tab

```
+------------------------------------------------------------------+
|  LLM Provider                                                     |
+------------------------------------------------------------------+
|                                                                   |
|  Provider Type:                                                   |
|  +------------------------------------------------------------+  |
|  | ( ) Container Ollama (Default)                              |  |
|  |     Ollama running in Docker/Podman compose stack           |  |
|  +------------------------------------------------------------+  |
|  | ( ) External Local LLM                                      |  |
|  |     Connect to LM Studio, llama.cpp, or external Ollama     |  |
|  +------------------------------------------------------------+  |
|  | ( ) OpenRouter (Your API Key)                               |  |
|  |     Cloud models using your OpenRouter API key              |  |
|  +------------------------------------------------------------+  |
|  | ( ) OpenRouter (Managed)                                    |  |
|  |     Cloud models with CodeCompass-provided access           |  |
|  +------------------------------------------------------------+  |
|                                                                   |
|  (Provider-specific configuration panel appears below)            |
|                                                                   |
+------------------------------------------------------------------+
```

### 4.3 Container Ollama Panel

```
+------------------------------------------------------------------+
|  Container Ollama Configuration                                   |
+------------------------------------------------------------------+
|                                                                   |
|  Hardware Detected:                                               |
|  +------------------------------------------------------------+  |
|  |  GPU: NVIDIA RTX 3080                                       |  |
|  |  VRAM: 10 GB available                                      |  |
|  |  Recommended models: 7B-13B parameters                      |  |
|  +------------------------------------------------------------+  |
|                                                                   |
|  Available Models:                                                |
|  +------------------------------------------------------------+  |
|  | [*] qwen2.5-coder:7b          4.7 GB    Recommended        |  |
|  | [ ] llama3.2:3b               2.0 GB    Fast               |  |
|  | [ ] codellama:13b             7.4 GB                        |  |
|  | [ ] deepseek-coder:6.7b       3.8 GB                        |  |
|  +------------------------------------------------------------+  |
|                                                                   |
|  [Pull New Model...]                                              |
|                                                                   |
|  Pull Model:  [________________________] [Pull]                   |
|  (e.g., mistral:7b, phi3:latest)                                 |
|                                                                   |
+------------------------------------------------------------------+
```

### 4.4 External LLM Panel

```
+------------------------------------------------------------------+
|  External LLM Configuration                                       |
+------------------------------------------------------------------+
|                                                                   |
|  Server URL:                                                      |
|  [http://localhost:1234___________________________] [Detect]      |
|                                                                   |
|  API Format:                                                      |
|  ( ) Auto-detect  (*) Ollama API  ( ) OpenAI-compatible           |
|                                                                   |
|  Available Models:        (Fetched from server)                   |
|  +------------------------------------------------------------+  |
|  | [*] TheBloke/Mistral-7B-GGUF                               |  |
|  | [ ] microsoft/phi-3-mini-4k                                |  |
|  +------------------------------------------------------------+  |
|                                                                   |
|  Or enter model name manually:                                    |
|  [________________________________]                               |
|                                                                   |
|  Common Configurations:                                           |
|  [LM Studio (localhost:1234)] [Ollama (localhost:11434)]          |
|  [llama.cpp (localhost:8080)] [vLLM (localhost:8000)]             |
|                                                                   |
+------------------------------------------------------------------+
```

### 4.5 OpenRouter Panel

```
+------------------------------------------------------------------+
|  OpenRouter Configuration                                         |
+------------------------------------------------------------------+
|                                                                   |
|  API Key:                                                         |
|  [sk-or-v1-*****************************] [Validate]              |
|  Status: Valid - 1000 credits remaining                         |
|                                                                   |
|  Get your API key at: https://openrouter.ai/keys                  |
|                                                                   |
|  Select Model:                                                    |
|  +------------------------------------------------------------+  |
|  | Filter: [All______] [_Search models..._________________]    |  |
|  +------------------------------------------------------------+  |
|  | Model                          Input      Output    Context |  |
|  +------------------------------------------------------------+  |
|  | [ ] anthropic/claude-3.5-so... $3.00/M    $15.00/M  200K   |  |
|  | [*] anthropic/claude-3-haiku   $0.25/M    $1.25/M   200K   |  |
|  | [ ] openai/gpt-4-turbo         $10.00/M   $30.00/M  128K   |  |
|  | [ ] openai/gpt-3.5-turbo       $0.50/M    $1.50/M   16K    |  |
|  | [ ] meta-llama/llama-3.1-70b   $0.59/M    $0.79/M   128K   |  |
|  | [ ] google/gemini-pro-1.5      $1.25/M    $5.00/M   1M     |  |
|  +------------------------------------------------------------+  |
|                                                                   |
|  Selected: anthropic/claude-3-haiku                               |
|  Estimated cost: ~$0.002 per chat message                         |
|                                                                   |
+------------------------------------------------------------------+
```

### 4.6 LLM Status Indicator (Header)

Always visible in the Header, next to the Settings button:

```
Ready state:     [*] qwen2.5-coder:7b     (green dot)
Loading state:   [~] Connecting...        (yellow dot, pulsing)
Error state:     [!] LLM Unavailable      (red dot)
```

**Hover tooltip shows:**
```
Provider: Container Ollama
Model: qwen2.5-coder:7b
Status: Ready
Last used: 2 minutes ago
```

**Click action:** Opens Settings dialog to LLM tab

---

## 5. Backend Implementation

### 5.1 New Endpoints

#### `GET /api/settings/hardware`
Get detected hardware capabilities.

**Response:**
```json
{
  "gpu": {
    "detected": true,
    "name": "NVIDIA GeForce RTX 3080",
    "vendor": "nvidia",
    "vram_total_gb": 10.0,
    "vram_available_gb": 8.5,
    "compute_capability": "8.6"
  },
  "cpu": {
    "name": "AMD Ryzen 9 5900X",
    "cores": 12,
    "threads": 24,
    "ram_total_gb": 32.0,
    "ram_available_gb": 24.5
  },
  "recommendations": {
    "max_model_params": "13B",
    "recommended_models": [
      {
        "name": "qwen2.5-coder:7b",
        "reason": "Optimal for 10GB VRAM",
        "estimated_speed": "~30 tokens/sec"
      },
      {
        "name": "llama3.2:3b",
        "reason": "Fast inference on your hardware",
        "estimated_speed": "~50 tokens/sec"
      }
    ]
  }
}
```

#### `POST /api/settings/llm/validate`
Validate LLM configuration before saving.

**Request:**
```json
{
  "provider_type": "openrouter_byok",
  "model": "anthropic/claude-3-haiku",
  "api_key": "sk-or-v1-...",
  "base_url": "https://openrouter.ai/api/v1"
}
```

**Response:**
```json
{
  "valid": true,
  "provider_status": "ready",
  "model_available": true,
  "test_response_ms": 450,
  "details": {
    "model_name": "anthropic/claude-3-haiku",
    "context_length": 200000,
    "pricing": {
      "input_per_million": 0.25,
      "output_per_million": 1.25
    }
  }
}
```

#### `PUT /api/settings/llm`
Update LLM configuration (with hot-reload).

**Request:**
```json
{
  "provider_type": "ollama_container",
  "model": "qwen2.5-coder:7b",
  "base_url": "http://ollama:11434"
}
```

**Response:**
```json
{
  "success": true,
  "provider_type": "ollama_container",
  "model": "qwen2.5-coder:7b",
  "status": "ready",
  "reloaded": true
}
```

#### `GET /api/settings/openrouter/models`
List available OpenRouter models (requires valid API key in session).

**Response:**
```json
{
  "models": [
    {
      "id": "anthropic/claude-3.5-sonnet",
      "name": "Claude 3.5 Sonnet",
      "provider": "anthropic",
      "context_length": 200000,
      "pricing": {
        "input_per_million": 3.0,
        "output_per_million": 15.0
      },
      "capabilities": ["chat", "code", "function_calling"],
      "description": "Most capable Claude model for complex tasks"
    }
  ]
}
```

### 5.2 OpenRouterProvider Implementation

**Location:** `backend/app/services/llm/openrouter_provider.py`

```python
"""OpenRouter LLM provider implementation."""

import logging
from typing import List, Optional, AsyncIterator, Dict, Any

import httpx

from .base import LLMProvider, GenerationResult, ChatMessage, ModelInfo

logger = logging.getLogger(__name__)


class OpenRouterProvider(LLMProvider):
    """LLM provider using OpenRouter API."""

    def __init__(
        self,
        api_key: str,
        model: str = "anthropic/claude-3-haiku",
        base_url: str = "https://openrouter.ai/api/v1",
        timeout: float = 120.0,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers including auth and app identification."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://codecompass.dev",
            "X-Title": "CodeCompass",
            "Content-Type": "application/json",
        }

    async def chat(self, messages: List[ChatMessage], **kwargs) -> GenerationResult:
        """Chat with the model using OpenRouter's OpenAI-compatible API."""
        client = await self._get_client()

        message_dicts = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        payload = {
            "model": kwargs.get("model", self.model),
            "messages": message_dicts,
        }

        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]

        response = await client.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=self._get_headers(),
        )
        response.raise_for_status()
        data = response.json()

        choice = data.get("choices", [{}])[0]
        usage = data.get("usage", {})

        return GenerationResult(
            content=choice.get("message", {}).get("content", ""),
            model=data.get("model", self.model),
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
        )

    async def list_models(self) -> List[ModelInfo]:
        """List available models from OpenRouter."""
        client = await self._get_client()

        response = await client.get(
            f"{self.base_url}/models",
            headers=self._get_headers(),
        )
        response.raise_for_status()
        data = response.json()

        models = []
        for model_data in data.get("data", []):
            models.append(ModelInfo(
                name=model_data.get("id", ""),
                details={
                    "context_length": model_data.get("context_length"),
                    "pricing": model_data.get("pricing"),
                    "description": model_data.get("description"),
                },
            ))
        return models
```

### 5.3 Settings Persistence

**Location:** `backend/app/models/settings.py`

```python
"""Settings database model."""

from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.sql import func

from app.database import Base


class LLMSettings(Base):
    """Persistent LLM settings."""

    __tablename__ = "llm_settings"

    id = Column(String, primary_key=True, default="default")
    provider_type = Column(String(50), nullable=False, default="ollama_container")
    model = Column(String(200), nullable=False, default="qwen2.5-coder:7b")
    base_url = Column(String(500), nullable=True)
    api_format = Column(String(20), nullable=True)  # ollama, openai

    # Encrypted API key (for OpenRouter)
    api_key_encrypted = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Status cache (updated on health checks)
    last_health_check = Column(DateTime, nullable=True)
    last_health_status = Column(Boolean, nullable=True)
```

### 5.4 Secrets Encryption Service

**Location:** `backend/app/services/secrets_service.py`

```python
"""Secrets encryption service for API keys."""

import os
import base64
import logging
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class SecretsService:
    """Service for encrypting/decrypting sensitive data."""

    def __init__(self, secret_key: Optional[str] = None):
        key = secret_key or os.environ.get("CODECOMPASS_SECRET_KEY")

        if not key:
            logger.warning("No CODECOMPASS_SECRET_KEY set, using derived key")
            key = self._derive_key("codecompass-dev-key")

        self.fernet = Fernet(key.encode() if isinstance(key, str) else key)

    def _derive_key(self, password: str) -> str:
        """Derive a Fernet key from a password."""
        salt = b"codecompass-salt"  # In production, use a secure random salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode()

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string and return base64-encoded ciphertext."""
        return self.fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt base64-encoded ciphertext and return plaintext."""
        return self.fernet.decrypt(ciphertext.encode()).decode()


# Singleton instance
_secrets_service: Optional[SecretsService] = None


def get_secrets_service() -> SecretsService:
    """Get the secrets service singleton."""
    global _secrets_service
    if _secrets_service is None:
        _secrets_service = SecretsService()
    return _secrets_service
```

### 5.5 Factory Updates

**Modified:** `backend/app/services/llm/factory.py`

Add support for provider hot-reload and new provider types:

```python
def reload_provider(config: Dict[str, Any]) -> LLMProvider:
    """Reload the LLM provider with new configuration."""
    global _llm_provider

    provider_type = config.get("provider_type", "ollama_container")

    if provider_type in ("ollama_container", "ollama_external"):
        _llm_provider = OllamaProvider(
            base_url=config.get("base_url", "http://localhost:11434"),
            model=config.get("model", "qwen2.5-coder:7b"),
        )
    elif provider_type in ("openrouter_byok", "openrouter_managed"):
        from .openrouter_provider import OpenRouterProvider
        _llm_provider = OpenRouterProvider(
            api_key=config.get("api_key", ""),
            model=config.get("model", "anthropic/claude-3-haiku"),
        )
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")

    logger.info(f"Reloaded LLM provider: {provider_type} with model {config.get('model')}")
    return _llm_provider
```

---

## 6. Frontend Implementation

### 6.1 New Components

| Component | Location | Description |
|-----------|----------|-------------|
| `SettingsDialog` | `components/settings/SettingsDialog.tsx` | Main settings modal with tabs |
| `LLMSettingsPanel` | `components/settings/LLMSettingsPanel.tsx` | LLM configuration tab |
| `OllamaContainerPanel` | `components/settings/OllamaContainerPanel.tsx` | Container Ollama config |
| `ExternalLLMPanel` | `components/settings/ExternalLLMPanel.tsx` | External server config |
| `OpenRouterPanel` | `components/settings/OpenRouterPanel.tsx` | OpenRouter config |
| `LLMStatusIndicator` | `components/layout/LLMStatusIndicator.tsx` | Header status indicator |
| `ModelSelector` | `components/settings/ModelSelector.tsx` | Reusable model picker |
| `HardwareInfo` | `components/settings/HardwareInfo.tsx` | Hardware detection display |

### 6.2 State Management

**Modified:** `frontend/src/lib/store.ts`

```typescript
interface SettingsState {
  // LLM Settings
  llmConfig: LLMConfig | null;
  llmStatus: 'ready' | 'connecting' | 'error' | 'unknown';
  llmError: string | null;

  // Available models (cached)
  availableModels: ModelInfo[];
  isLoadingModels: boolean;

  // Hardware info
  hardwareInfo: HardwareInfo | null;

  // Actions
  fetchSettings: () => Promise<void>;
  updateLLMConfig: (config: LLMConfig) => Promise<boolean>;
  validateLLMConfig: (config: LLMConfig) => Promise<ValidationResult>;
  fetchHardwareInfo: () => Promise<void>;
  fetchAvailableModels: () => Promise<void>;
  pullModel: (modelName: string) => Promise<void>;
  deleteModel: (modelName: string) => Promise<void>;
}
```

### 6.3 API Types

**Modified:** `frontend/src/types/api.ts`

```typescript
// Provider types
export type ProviderType =
  | 'ollama_container'
  | 'ollama_external'
  | 'openrouter_byok'
  | 'openrouter_managed';

// LLM configuration
export interface LLMConfig {
  provider_type: ProviderType;
  model: string;
  base_url?: string;
  api_format?: 'ollama' | 'openai';
  api_key?: string;  // Only for OpenRouter BYOK
}

// Hardware detection
export interface HardwareInfo {
  gpu: {
    detected: boolean;
    name?: string;
    vendor?: 'nvidia' | 'amd' | 'apple' | 'intel';
    vram_total_gb?: number;
    vram_available_gb?: number;
  };
  cpu: {
    name: string;
    cores: number;
    threads: number;
    ram_total_gb: number;
    ram_available_gb: number;
  };
  recommendations: {
    max_model_params: string;
    recommended_models: RecommendedModel[];
  };
}

export interface RecommendedModel {
  name: string;
  reason: string;
  estimated_speed?: string;
}

// OpenRouter model info
export interface OpenRouterModel {
  id: string;
  name: string;
  provider: string;
  context_length: number;
  pricing: {
    input_per_million: number;
    output_per_million: number;
  };
  capabilities: string[];
  description?: string;
}

// Validation result
export interface ValidationResult {
  valid: boolean;
  provider_status: string;
  model_available: boolean;
  test_response_ms?: number;
  error?: string;
}
```

### 6.4 Header Integration

**Modified:** `frontend/src/components/layout/Header.tsx`

Add LLMStatusIndicator and wire Settings button:

```tsx
import { LLMStatusIndicator } from './LLMStatusIndicator';
import { SettingsDialog } from '@/components/settings/SettingsDialog';

// In Header component:
const [settingsOpen, setSettingsOpen] = useState(false);

// In JSX:
<div className="flex items-center gap-2">
  <LLMStatusIndicator onClick={() => setSettingsOpen(true)} />
  <Button variant="ghost" size="icon" onClick={() => setSettingsOpen(true)}>
    <Settings className="h-5 w-5" />
  </Button>
  {/* ... */}
</div>

<SettingsDialog open={settingsOpen} onOpenChange={setSettingsOpen} />
```

---

## 7. Hardware Detection

### 7.1 Detection Methods

**Container Environment:**
```python
async def detect_hardware() -> HardwareInfo:
    """Detect hardware in container environment."""

    # GPU detection via nvidia-smi (if available)
    gpu_info = await detect_nvidia_gpu()

    # Fallback: check Ollama's GPU info
    if not gpu_info:
        gpu_info = await get_ollama_gpu_info()

    # CPU and RAM from /proc (Linux)
    cpu_info = get_cpu_info()
    ram_info = get_ram_info()

    # Generate recommendations
    recommendations = generate_recommendations(gpu_info, ram_info)

    return HardwareInfo(...)
```

### 7.2 Model Recommendation Table

| VRAM Available | Recommended Models | Notes |
|----------------|-------------------|-------|
| < 4 GB | `llama3.2:1b`, `phi3:mini` | CPU inference recommended |
| 4-6 GB | `llama3.2:3b`, `qwen2.5:3b` | Smaller models only |
| 6-8 GB | `qwen2.5-coder:7b`, `mistral:7b` | 7B models fit well |
| 8-12 GB | `llama3.1:8b`, `codellama:13b` | Room for larger context |
| 12-16 GB | `qwen2.5:14b`, `deepseek-coder:14b` | 13-14B models |
| 16-24 GB | `llama3.1:70b-q4`, `mixtral:8x7b` | Quantized large models |
| 24+ GB | `llama3.1:70b`, `qwen2.5:72b` | Full precision large |

### 7.3 Implementation

**Location:** `backend/app/services/hardware_service.py`

```python
"""Hardware detection service."""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GPUInfo:
    detected: bool
    name: Optional[str] = None
    vendor: Optional[str] = None
    vram_total_gb: Optional[float] = None
    vram_available_gb: Optional[float] = None
    compute_capability: Optional[str] = None


@dataclass
class CPUInfo:
    name: str
    cores: int
    threads: int
    ram_total_gb: float
    ram_available_gb: float


@dataclass
class HardwareInfo:
    gpu: GPUInfo
    cpu: CPUInfo
    recommendations: Dict[str, Any]


async def detect_nvidia_gpu() -> Optional[GPUInfo]:
    """Detect NVIDIA GPU using nvidia-smi."""
    try:
        result = await asyncio.create_subprocess_exec(
            "nvidia-smi",
            "--query-gpu=name,memory.total,memory.free",
            "--format=csv,noheader,nounits",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await result.communicate()

        if result.returncode == 0 and stdout:
            parts = stdout.decode().strip().split(", ")
            if len(parts) >= 3:
                return GPUInfo(
                    detected=True,
                    name=parts[0],
                    vendor="nvidia",
                    vram_total_gb=float(parts[1]) / 1024,
                    vram_available_gb=float(parts[2]) / 1024,
                )
    except Exception as e:
        logger.debug(f"nvidia-smi not available: {e}")

    return None


def generate_recommendations(
    gpu: Optional[GPUInfo],
    ram_gb: float
) -> Dict[str, Any]:
    """Generate model recommendations based on hardware."""

    # Determine effective memory
    if gpu and gpu.vram_available_gb:
        effective_memory = gpu.vram_available_gb
        is_gpu = True
    else:
        effective_memory = ram_gb * 0.7  # Use 70% of RAM for CPU inference
        is_gpu = False

    # Recommendation thresholds
    if effective_memory < 4:
        max_params = "3B"
        models = [
            {"name": "llama3.2:1b", "reason": "Tiny model for limited memory"},
            {"name": "phi3:mini", "reason": "Efficient small model"},
        ]
    elif effective_memory < 8:
        max_params = "7B"
        models = [
            {"name": "qwen2.5-coder:7b", "reason": "Optimized for coding tasks"},
            {"name": "llama3.2:3b", "reason": "Good balance of speed and quality"},
        ]
    elif effective_memory < 16:
        max_params = "13B"
        models = [
            {"name": "qwen2.5-coder:7b", "reason": "Recommended for 8-16GB VRAM"},
            {"name": "codellama:13b", "reason": "Larger coding model"},
        ]
    else:
        max_params = "70B (quantized)"
        models = [
            {"name": "qwen2.5:14b", "reason": "High quality for ample VRAM"},
            {"name": "llama3.1:70b-q4", "reason": "Large model with quantization"},
        ]

    return {
        "max_model_params": max_params,
        "recommended_models": models,
        "inference_mode": "GPU" if is_gpu else "CPU",
    }
```

---

## 8. Security Considerations

### 8.1 API Key Protection

| Concern | Mitigation |
|---------|------------|
| Storage | Keys encrypted with Fernet (AES-128-CBC) |
| Transmission | HTTPS required for OpenRouter |
| Logging | Keys redacted in all log output |
| Display | Keys masked in UI (show last 4 chars only) |
| Memory | Keys cleared after use where possible |

### 8.2 Input Validation

```python
# Base URL validation
def validate_base_url(url: str) -> bool:
    """Validate LLM server base URL."""
    parsed = urlparse(url)

    # Must be http or https
    if parsed.scheme not in ("http", "https"):
        return False

    # Must have a host
    if not parsed.netloc:
        return False

    # Block dangerous URLs
    blocked_hosts = ["localhost.run", "ngrok.io", "localtunnel.me"]
    if any(blocked in parsed.netloc for blocked in blocked_hosts):
        return False

    return True

# Model name validation
def validate_model_name(name: str) -> bool:
    """Validate model name format."""
    # Allow alphanumeric, hyphens, underscores, slashes, colons, dots
    return bool(re.match(r"^[\w\-\./:\d]+$", name))

# API key format validation
def validate_openrouter_key(key: str) -> bool:
    """Validate OpenRouter API key format."""
    return key.startswith("sk-or-") and len(key) > 20
```

### 8.3 Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| `POST /api/settings/llm/validate` | 10 | 1 minute |
| `PUT /api/settings/llm` | 5 | 1 minute |
| `POST /api/settings/models/pull` | 3 | 10 minutes |

---

## 9. Testing Strategy

### 9.1 Unit Tests

**Backend:**
```
tests/unit/
  test_openrouter_provider.py     # OpenRouter API client
  test_secrets_service.py          # Encryption/decryption
  test_hardware_service.py         # Hardware detection
  test_llm_factory.py              # Provider factory & reload
  test_settings_validation.py      # Config validation
```

**Coverage targets:**
- OpenRouter provider: 90%+ coverage
- Secrets service: 100% coverage
- Settings validation: 100% coverage

### 9.2 Integration Tests

```
tests/integration/
  test_settings_routes.py          # Settings API endpoints
  test_provider_switching.py       # Hot-reload functionality
  test_openrouter_integration.py   # Real OpenRouter calls (needs key)
  test_hardware_detection.py       # Hardware detection in CI
```

**Test scenarios:**
- [ ] Container Ollama detection and model listing
- [ ] External LLM connection with different API formats
- [ ] OpenRouter API key validation
- [ ] Provider hot-reload during active session
- [ ] Encrypted settings persistence and retrieval

### 9.3 Frontend Tests

```
frontend/src/components/settings/__tests__/
  SettingsDialog.test.tsx
  LLMSettingsPanel.test.tsx
  OllamaContainerPanel.test.tsx
  ExternalLLMPanel.test.tsx
  OpenRouterPanel.test.tsx
  LLMStatusIndicator.test.tsx
```

**Test scenarios:**
- [ ] Dialog opens and closes correctly
- [ ] Tab navigation works
- [ ] Provider selection updates panel
- [ ] Form validation on all inputs
- [ ] Connection test shows results
- [ ] Save updates store and closes dialog
- [ ] Status indicator reflects current state

### 9.4 E2E Tests

Using MCP Playwright (accessibility snapshots, not screenshots):

1. **First-time user flow:**
   - Open app with no settings
   - Verify default LLM status
   - Open settings, verify container Ollama selected
   - Save without changes, verify status

2. **Model switching flow:**
   - Open settings
   - Change model selection
   - Test connection
   - Save and verify status updates

3. **External LLM flow:**
   - Select External LLM option
   - Enter custom URL
   - Verify connection test
   - Save and use in chat

4. **OpenRouter flow:**
   - Select OpenRouter BYOK
   - Enter API key
   - Validate key
   - Browse and select model
   - Save and verify chat works

### 9.5 Security Tests

- [ ] API keys not logged in any log level
- [ ] Encrypted keys not decryptable without secret
- [ ] Invalid URLs rejected before connection attempt
- [ ] Rate limiting enforced on sensitive endpoints
- [ ] XSS prevention in model names and descriptions

---

## 10. Success Metrics

### 10.1 Performance Targets

| Operation | Target | Acceptable |
|-----------|--------|------------|
| Settings dialog load | < 200ms | < 500ms |
| Provider validation | < 2s | < 5s |
| Model list fetch | < 1s | < 3s |
| Hot-reload switch | < 500ms | < 1s |
| Hardware detection | < 3s | < 5s |

### 10.2 UX Metrics

| Metric | Target |
|--------|--------|
| First-time setup success rate | > 95% |
| Settings dialog task completion | > 90% |
| Error message helpfulness | > 4/5 user rating |
| Time to configure external LLM | < 2 minutes |

### 10.3 Reliability Metrics

| Metric | Target |
|--------|--------|
| LLM status accuracy | > 99% |
| Connection test accuracy | > 95% |
| Settings persistence | 100% |
| Secret encryption integrity | 100% |

---

## 11. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| OpenRouter API changes | Provider breaks | Low | Version-locked API, fallback modes |
| Hardware detection fails | Poor recommendations | Medium | Graceful degradation to conservative defaults |
| API key leak via logs | Security breach | Low | Strict key redaction, security audit |
| Provider hot-reload race conditions | Chat errors | Medium | Mutex lock during reload, retry logic |
| External LLM compatibility issues | Connection failures | High | Extensive format detection, manual override |
| Model pull timeout | User frustration | Medium | Background task with progress, cancellation support |

---

## 12. Appendix

### A. OpenRouter API Reference

**Base URL:** `https://openrouter.ai/api/v1`

**Authentication:**
```
Authorization: Bearer sk-or-v1-...
```

**List Models:**
```
GET /models

Response:
{
  "data": [
    {
      "id": "anthropic/claude-3-haiku",
      "name": "Claude 3 Haiku",
      "context_length": 200000,
      "pricing": {
        "prompt": "0.00000025",
        "completion": "0.00000125"
      }
    }
  ]
}
```

**Chat Completion:**
```
POST /chat/completions

{
  "model": "anthropic/claude-3-haiku",
  "messages": [
    {"role": "user", "content": "Hello"}
  ]
}

Response:
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help?"
      }
    }
  ],
  "usage": {
    "prompt_tokens": 5,
    "completion_tokens": 10,
    "total_tokens": 15
  }
}
```

### B. Ollama API Reference

**Base URL:** `http://localhost:11434`

**List Models:**
```
GET /api/tags

Response:
{
  "models": [
    {
      "name": "qwen2.5-coder:7b",
      "size": 4700000000,
      "modified_at": "2026-01-20T10:00:00Z"
    }
  ]
}
```

**Generate:**
```
POST /api/generate

{
  "model": "qwen2.5-coder:7b",
  "prompt": "Hello",
  "stream": false
}
```

**Chat:**
```
POST /api/chat

{
  "model": "qwen2.5-coder:7b",
  "messages": [
    {"role": "user", "content": "Hello"}
  ],
  "stream": false
}
```

**Pull Model:**
```
POST /api/pull

{
  "name": "llama3.2:3b",
  "stream": false
}
```

**Delete Model:**
```
DELETE /api/delete

{
  "name": "llama3.2:3b"
}
```

### C. Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CODECOMPASS_SECRET_KEY` | Fernet key for encrypting secrets | (derived) |
| `LLM_PROVIDER` | Default provider type | `ollama_container` |
| `LLM_MODEL` | Default model | `qwen2.5-coder:7b` |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://ollama:11434` |
| `OPENROUTER_API_KEY` | Managed OpenRouter key | (none) |

---

*Document End*
