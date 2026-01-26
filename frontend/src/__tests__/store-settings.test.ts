import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useAppStore } from '@/lib/store';

// Mock the API module
vi.mock('@/lib/api', () => ({
  api: {
    getLLMSettings: vi.fn(),
    updateLLMConfig: vi.fn(),
    validateLLMConfig: vi.fn(),
    getHardwareInfo: vi.fn(),
    listModels: vi.fn(),
    listOpenRouterModels: vi.fn(),
    pullModel: vi.fn(),
    deleteModel: vi.fn(),
  },
}));

// Mock the error module
vi.mock('@/lib/api-error', () => ({
  getErrorMessage: vi.fn((error: unknown) =>
    error instanceof Error ? error.message : 'Unknown error'
  ),
}));

async function getApi() {
  const { api } = await import('@/lib/api');
  return api as unknown as Record<string, ReturnType<typeof vi.fn>>;
}

describe('Settings Store Slice', () => {
  beforeEach(() => {
    // Reset store to initial state
    useAppStore.setState({
      llmConfig: null,
      llmStatus: 'unknown',
      llmError: null,
      hardwareInfo: null,
      isLoadingHardware: false,
      availableModels: [],
      isLoadingModels: false,
      openRouterModels: [],
      isLoadingOpenRouterModels: false,
    });
    vi.clearAllMocks();
  });

  afterEach(() => {
    useAppStore.getState().stopStatusPolling();
  });

  // ============================================================================
  // fetchLLMSettings
  // ============================================================================

  describe('fetchLLMSettings', () => {
    it('populates state on successful fetch', async () => {
      const mockConfig = {
        provider_type: 'ollama_container',
        model: 'llama3.1:8b',
        status: 'ready',
        base_url: 'http://ollama:11434',
      };

      const api = await getApi();
      api.getLLMSettings.mockResolvedValue(mockConfig);

      await useAppStore.getState().fetchLLMSettings();

      const state = useAppStore.getState();
      expect(state.llmConfig).toEqual(mockConfig);
      expect(state.llmStatus).toBe('ready');
      expect(state.llmError).toBeNull();
    });

    it('sets status to error for non-ready config', async () => {
      const mockConfig = {
        provider_type: 'ollama_container',
        model: 'llama3.1:8b',
        status: 'disconnected',
      };

      const api = await getApi();
      api.getLLMSettings.mockResolvedValue(mockConfig);

      await useAppStore.getState().fetchLLMSettings();

      const state = useAppStore.getState();
      expect(state.llmConfig).toEqual(mockConfig);
      expect(state.llmStatus).toBe('error');
    });

    it('handles fetch error', async () => {
      const api = await getApi();
      api.getLLMSettings.mockRejectedValue(new Error('Network error'));

      await useAppStore.getState().fetchLLMSettings();

      const state = useAppStore.getState();
      expect(state.llmStatus).toBe('error');
      expect(state.llmError).toBe('Network error');
    });
  });

  // ============================================================================
  // validateLLMConfig
  // ============================================================================

  describe('validateLLMConfig', () => {
    it('returns validation result on success', async () => {
      const mockResult = {
        valid: true,
        provider_status: 'ready',
        model_available: true,
        test_response_ms: 150,
      };

      const api = await getApi();
      api.validateLLMConfig.mockResolvedValue(mockResult);

      const result = await useAppStore.getState().validateLLMConfig({
        provider_type: 'ollama_container',
        model: 'llama3.1:8b',
      });

      expect(result).toEqual(mockResult);
    });

    it('returns error result on failure', async () => {
      const api = await getApi();
      api.validateLLMConfig.mockRejectedValue(new Error('Connection refused'));

      const result = await useAppStore.getState().validateLLMConfig({
        provider_type: 'ollama_external',
        model: 'test',
        base_url: 'http://localhost:9999',
      });

      expect(result.valid).toBe(false);
      expect(result.provider_status).toBe('error');
      expect(result.error).toBe('Connection refused');
    });
  });

  // ============================================================================
  // updateLLMConfig
  // ============================================================================

  describe('updateLLMConfig', () => {
    it('saves config and refreshes settings', async () => {
      const api = await getApi();
      api.updateLLMConfig.mockResolvedValue({});
      api.getLLMSettings.mockResolvedValue({
        provider_type: 'openrouter_byok',
        model: 'anthropic/claude-3-haiku',
        status: 'ready',
      });

      const success = await useAppStore.getState().updateLLMConfig({
        provider_type: 'openrouter_byok',
        model: 'anthropic/claude-3-haiku',
        api_key: 'sk-test',
      });

      expect(success).toBe(true);
      expect(api.updateLLMConfig).toHaveBeenCalledWith({
        provider_type: 'openrouter_byok',
        model: 'anthropic/claude-3-haiku',
        api_key: 'sk-test',
      });
      expect(api.getLLMSettings).toHaveBeenCalled();

      const state = useAppStore.getState();
      expect(state.llmStatus).toBe('ready');
    });

    it('sets connecting status while saving', async () => {
      const api = await getApi();
      let capturedStatus: string | null = null;

      api.updateLLMConfig.mockImplementation(async () => {
        capturedStatus = useAppStore.getState().llmStatus;
        return {};
      });
      api.getLLMSettings.mockResolvedValue({
        provider_type: 'ollama_container',
        model: 'llama3.1:8b',
        status: 'ready',
      });

      await useAppStore.getState().updateLLMConfig({
        provider_type: 'ollama_container',
        model: 'llama3.1:8b',
      });

      expect(capturedStatus).toBe('connecting');
    });

    it('handles save error', async () => {
      const api = await getApi();
      api.updateLLMConfig.mockRejectedValue(new Error('Save failed'));

      const success = await useAppStore.getState().updateLLMConfig({
        provider_type: 'ollama_container',
        model: 'test',
      });

      expect(success).toBe(false);
      const state = useAppStore.getState();
      expect(state.llmStatus).toBe('error');
      expect(state.llmError).toBe('Save failed');
    });
  });

  // ============================================================================
  // fetchHardwareInfo
  // ============================================================================

  describe('fetchHardwareInfo', () => {
    it('populates hardware state', async () => {
      const mockHardware = {
        gpu: { detected: true, name: 'NVIDIA RTX 4090', vram_total_gb: 24 },
        cpu: { name: 'AMD Ryzen 9', cores: 16, threads: 32, ram_total_gb: 64, ram_available_gb: 48 },
        recommendations: {
          max_model_params: '70B',
          recommended_models: [{ name: 'llama3.1:70b', reason: 'Fits in VRAM' }],
          inference_mode: 'gpu',
        },
      };

      const api = await getApi();
      api.getHardwareInfo.mockResolvedValue(mockHardware);

      await useAppStore.getState().fetchHardwareInfo();

      const state = useAppStore.getState();
      expect(state.hardwareInfo).toEqual(mockHardware);
      expect(state.isLoadingHardware).toBe(false);
    });

    it('resets loading state on error', async () => {
      const api = await getApi();
      api.getHardwareInfo.mockRejectedValue(new Error('Failed'));

      await useAppStore.getState().fetchHardwareInfo();

      expect(useAppStore.getState().isLoadingHardware).toBe(false);
    });
  });

  // ============================================================================
  // fetchAvailableModels
  // ============================================================================

  describe('fetchAvailableModels', () => {
    it('populates models list', async () => {
      const mockModels = {
        models: [
          { name: 'llama3.1:8b', size: '4.7GB', modified_at: '2024-01-01', details: {} },
          { name: 'codellama:7b', size: '3.8GB', modified_at: '2024-01-01', details: {} },
        ],
      };

      const api = await getApi();
      api.listModels.mockResolvedValue(mockModels);

      await useAppStore.getState().fetchAvailableModels();

      const state = useAppStore.getState();
      expect(state.availableModels).toEqual(mockModels.models);
      expect(state.isLoadingModels).toBe(false);
    });

    it('resets loading state on error', async () => {
      const api = await getApi();
      api.listModels.mockRejectedValue(new Error('Failed'));

      await useAppStore.getState().fetchAvailableModels();

      expect(useAppStore.getState().isLoadingModels).toBe(false);
    });
  });

  // ============================================================================
  // fetchOpenRouterModels
  // ============================================================================

  describe('fetchOpenRouterModels', () => {
    it('populates OpenRouter models list', async () => {
      const mockModels = {
        models: [
          {
            id: 'anthropic/claude-3-haiku',
            name: 'Claude 3 Haiku',
            provider: 'anthropic',
            context_length: 200000,
            pricing: { input_per_million: 0.25, output_per_million: 1.25 },
            capabilities: ['chat'],
          },
        ],
      };

      const api = await getApi();
      api.listOpenRouterModels.mockResolvedValue(mockModels);

      await useAppStore.getState().fetchOpenRouterModels();

      const state = useAppStore.getState();
      expect(state.openRouterModels).toEqual(mockModels.models);
      expect(state.isLoadingOpenRouterModels).toBe(false);
    });

    it('resets loading state on error', async () => {
      const api = await getApi();
      api.listOpenRouterModels.mockRejectedValue(new Error('Failed'));

      await useAppStore.getState().fetchOpenRouterModels();

      expect(useAppStore.getState().isLoadingOpenRouterModels).toBe(false);
    });
  });

  // ============================================================================
  // pullModel / deleteModel
  // ============================================================================

  describe('pullModel', () => {
    it('pulls model and refreshes list on success', async () => {
      const api = await getApi();
      api.pullModel.mockResolvedValue({ success: true, model: 'llama3.1:8b', message: 'OK' });
      api.listModels.mockResolvedValue({ models: [] });

      const result = await useAppStore.getState().pullModel('llama3.1:8b');

      expect(result).toBe(true);
      expect(api.pullModel).toHaveBeenCalledWith('llama3.1:8b');
      expect(api.listModels).toHaveBeenCalled();
    });

    it('does not refresh list on failure', async () => {
      const api = await getApi();
      api.pullModel.mockResolvedValue({ success: false, model: 'bad', message: 'not found' });

      const result = await useAppStore.getState().pullModel('bad');

      expect(result).toBe(false);
      expect(api.listModels).not.toHaveBeenCalled();
    });

    it('returns false on error', async () => {
      const api = await getApi();
      api.pullModel.mockRejectedValue(new Error('Network error'));

      const result = await useAppStore.getState().pullModel('test');

      expect(result).toBe(false);
    });
  });

  describe('deleteModel', () => {
    it('deletes model and refreshes list on success', async () => {
      const api = await getApi();
      api.deleteModel.mockResolvedValue({ success: true, model: 'old-model', message: 'deleted' });
      api.listModels.mockResolvedValue({ models: [] });

      const result = await useAppStore.getState().deleteModel('old-model');

      expect(result).toBe(true);
      expect(api.deleteModel).toHaveBeenCalledWith('old-model');
      expect(api.listModels).toHaveBeenCalled();
    });

    it('returns false on error', async () => {
      const api = await getApi();
      api.deleteModel.mockRejectedValue(new Error('Failed'));

      const result = await useAppStore.getState().deleteModel('test');

      expect(result).toBe(false);
    });
  });

  // ============================================================================
  // Status Polling
  // ============================================================================

  describe('status polling', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('starts polling and fetches settings periodically', async () => {
      const api = await getApi();
      api.getLLMSettings.mockResolvedValue({
        provider_type: 'ollama_container',
        model: 'test',
        status: 'ready',
      });

      useAppStore.getState().startStatusPolling();

      // Should not fetch immediately
      expect(api.getLLMSettings).not.toHaveBeenCalled();

      // Advance 30 seconds (use async to handle dynamic imports in callback)
      await vi.advanceTimersByTimeAsync(30_000);
      expect(api.getLLMSettings).toHaveBeenCalledTimes(1);

      // Advance another 30 seconds
      await vi.advanceTimersByTimeAsync(30_000);
      expect(api.getLLMSettings).toHaveBeenCalledTimes(2);

      useAppStore.getState().stopStatusPolling();
    });

    it('stops polling', async () => {
      const api = await getApi();
      api.getLLMSettings.mockResolvedValue({
        provider_type: 'ollama_container',
        model: 'test',
        status: 'ready',
      });

      useAppStore.getState().startStatusPolling();
      useAppStore.getState().stopStatusPolling();

      await vi.advanceTimersByTimeAsync(60_000);
      expect(api.getLLMSettings).not.toHaveBeenCalled();
    });

    it('does not start duplicate polling', async () => {
      const api = await getApi();
      api.getLLMSettings.mockResolvedValue({
        provider_type: 'ollama_container',
        model: 'test',
        status: 'ready',
      });

      useAppStore.getState().startStatusPolling();
      useAppStore.getState().startStatusPolling(); // duplicate call

      await vi.advanceTimersByTimeAsync(30_000);
      // Should only have one interval running
      expect(api.getLLMSettings).toHaveBeenCalledTimes(1);

      useAppStore.getState().stopStatusPolling();
    });
  });
});
