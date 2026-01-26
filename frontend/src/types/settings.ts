/**
 * Settings types for the Zustand store
 *
 * Re-exports API types and defines store-specific types for LLM settings management.
 */

export type {
  LLMConfig,
  LLMConfigUpdate,
  LLMValidationRequest,
  LLMValidationResponse,
  HardwareInfo,
  OllamaModel,
  OllamaModelList,
  ModelPullResponse,
  OpenRouterModel,
  OpenRouterModelsResponse,
} from './api';

export type ProviderType =
  | 'ollama_container'
  | 'ollama_external'
  | 'openrouter_byok'
  | 'openrouter_managed';

export type LLMStatus = 'ready' | 'connecting' | 'error' | 'unknown';
