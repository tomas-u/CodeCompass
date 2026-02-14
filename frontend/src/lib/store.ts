import { create } from 'zustand';
import type { ProjectListItem, ProjectStatus as ApiProjectStatus, ChatSessionListItem } from '@/types/api';
import type { LLMConfig, LLMConfigUpdate, LLMValidationResponse, HardwareInfo, OllamaModel, OpenRouterModel } from '@/types/settings';
import type { LLMStatus } from '@/types/settings';

// Type alias for internal use and re-export for convenience
export type Project = ProjectListItem;
export type ProjectStatus = ApiProjectStatus;
export type { ChatSessionListItem };

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: {
    filePath: string;
    startLine: number;
    endLine: number;
    snippet: string;
  }[];
  createdAt: string;
}

export interface AnalysisProgress {
  // Note: These must match the backend ProjectStatus enum values
  currentStep: 'cloning' | 'scanning' | 'analyzing' | 'embedding';
  overallPercent: number;
  currentFile?: string;
  filesProcessed?: number;
  filesTotal?: number;
  estimatedRemainingSeconds?: number;
}

interface AppState {
  // Projects
  projects: Project[];
  currentProjectId: string | null;
  isLoadingProjects: boolean;
  projectsError: string | null;

  // UI State
  isChatPanelOpen: boolean;
  activeTab: 'overview' | 'diagrams' | 'files' | 'reports';

  // Analysis
  analysisProgress: AnalysisProgress | null;

  // Chat
  chatMessages: ChatMessage[];
  isAiTyping: boolean;
  currentSessionId: string | null;
  chatSessions: ChatSessionListItem[];
  isLoadingSessions: boolean;

  // Settings - LLM Configuration
  llmConfig: LLMConfig | null;
  llmStatus: LLMStatus;
  llmError: string | null;

  // Settings - Hardware
  hardwareInfo: HardwareInfo | null;
  isLoadingHardware: boolean;

  // Settings - Models
  availableModels: OllamaModel[];
  isLoadingModels: boolean;

  // Settings - OpenRouter Models
  openRouterModels: OpenRouterModel[];
  isLoadingOpenRouterModels: boolean;

  // Project Actions
  setCurrentProject: (id: string | null) => void;
  toggleChatPanel: () => void;
  setActiveTab: (tab: 'overview' | 'diagrams' | 'files' | 'reports') => void;
  fetchProjects: () => Promise<void>;
  setProjects: (projects: Project[]) => void;
  addProject: (project: Project) => void;
  deleteProject: (id: string) => void;
  setAnalysisProgress: (progress: AnalysisProgress | null) => void;

  // Chat Actions
  addChatMessage: (message: ChatMessage) => void;
  updateChatMessage: (id: string, updater: (msg: ChatMessage) => ChatMessage) => void;
  clearChat: () => void;
  setIsAiTyping: (typing: boolean) => void;
  setCurrentSessionId: (sessionId: string | null) => void;
  setChatSessions: (sessions: ChatSessionListItem[]) => void;
  setIsLoadingSessions: (loading: boolean) => void;
  setChatMessages: (messages: ChatMessage[]) => void;

  // Settings Actions
  fetchLLMSettings: () => Promise<void>;
  updateLLMConfig: (config: LLMConfigUpdate) => Promise<boolean>;
  validateLLMConfig: (config: LLMConfigUpdate) => Promise<LLMValidationResponse>;
  fetchHardwareInfo: () => Promise<void>;
  fetchAvailableModels: () => Promise<void>;
  fetchOpenRouterModels: (apiKey?: string) => Promise<void>;
  pullModel: (modelName: string) => Promise<boolean>;
  deleteModel: (modelName: string) => Promise<boolean>;
  startStatusPolling: () => void;
  stopStatusPolling: () => void;
}

// Status polling interval (outside store to avoid serialization)
let pollingInterval: ReturnType<typeof setInterval> | null = null;

export const useAppStore = create<AppState>((set, get) => ({
  // Initial state
  projects: [],
  currentProjectId: null,
  isLoadingProjects: false,
  projectsError: null,
  isChatPanelOpen: true,
  activeTab: 'overview',
  analysisProgress: null,
  chatMessages: [],
  isAiTyping: false,
  currentSessionId: null,
  chatSessions: [],
  isLoadingSessions: false,

  // Settings initial state
  llmConfig: null,
  llmStatus: 'unknown',
  llmError: null,
  hardwareInfo: null,
  isLoadingHardware: false,
  availableModels: [],
  isLoadingModels: false,
  openRouterModels: [],
  isLoadingOpenRouterModels: false,

  // ============================================================================
  // Project Actions
  // ============================================================================

  setCurrentProject: (id) => set({
    currentProjectId: id,
    // Clear chat state when changing projects
    chatMessages: [],
    currentSessionId: null,
    chatSessions: [],
    isLoadingSessions: false,
  }),

  toggleChatPanel: () => set((state) => ({ isChatPanelOpen: !state.isChatPanelOpen })),

  setActiveTab: (tab) => set({ activeTab: tab }),

  fetchProjects: async () => {
    set({ isLoadingProjects: true, projectsError: null });
    try {
      const { api } = await import('./api');
      const result = await api.getProjects();

      // Sort projects by created_at descending (newest first)
      const sortedProjects = [...result.items].sort((a, b) => {
        const dateA = new Date(a.created_at).getTime();
        const dateB = new Date(b.created_at).getTime();
        return dateB - dateA;
      });

      set({
        projects: sortedProjects,
        isLoadingProjects: false
      });
    } catch (error) {
      const { getErrorMessage } = await import('./api-error');
      set({
        projectsError: getErrorMessage(error),
        isLoadingProjects: false
      });
    }
  },

  setProjects: (projects) => set({ projects }),

  addProject: (project) => set((state) => ({
    projects: [...state.projects, project],
    currentProjectId: project.id
  })),

  deleteProject: (id) => set((state) => ({
    projects: state.projects.filter(p => p.id !== id),
    currentProjectId: state.currentProjectId === id ? null : state.currentProjectId
  })),

  setAnalysisProgress: (progress) => set({ analysisProgress: progress }),

  // ============================================================================
  // Chat Actions
  // ============================================================================

  addChatMessage: (message) => set((state) => ({
    chatMessages: [...state.chatMessages, message]
  })),

  updateChatMessage: (id, updater) => set((state) => ({
    chatMessages: state.chatMessages.map((msg) =>
      msg.id === id ? updater(msg) : msg
    ),
  })),

  clearChat: () => set({ chatMessages: [], currentSessionId: null }),

  setIsAiTyping: (typing) => set({ isAiTyping: typing }),

  setCurrentSessionId: (sessionId) => set({ currentSessionId: sessionId }),

  setChatSessions: (sessions) => set({ chatSessions: sessions }),

  setIsLoadingSessions: (loading) => set({ isLoadingSessions: loading }),

  setChatMessages: (messages) => set({ chatMessages: messages }),

  // ============================================================================
  // Settings Actions
  // ============================================================================

  fetchLLMSettings: async () => {
    try {
      const { api } = await import('./api');
      const config = await api.getLLMSettings();
      set({
        llmConfig: config,
        llmStatus: config.status === 'ready' ? 'ready'
          : config.status === 'unavailable' ? 'error'
          : config.status === 'unknown' ? 'unknown'
          : 'error',
        llmError: null,
      });
    } catch (error) {
      const { getErrorMessage } = await import('./api-error');
      set({
        llmStatus: 'error',
        llmError: getErrorMessage(error),
      });
    }
  },

  updateLLMConfig: async (config) => {
    try {
      set({ llmStatus: 'connecting', llmError: null });
      const { api } = await import('./api');
      await api.updateLLMConfig(config);
      await get().fetchLLMSettings();
      return true;
    } catch (error) {
      const { getErrorMessage } = await import('./api-error');
      set({
        llmStatus: 'error',
        llmError: getErrorMessage(error),
      });
      return false;
    }
  },

  validateLLMConfig: async (config) => {
    try {
      const { api } = await import('./api');
      return await api.validateLLMConfig({
        provider_type: config.provider_type,
        model: config.model,
        base_url: config.base_url,
        api_key: config.api_key,
        api_format: config.api_format,
      });
    } catch (error) {
      const { getErrorMessage } = await import('./api-error');
      return {
        valid: false,
        provider_status: 'error',
        model_available: false,
        error: getErrorMessage(error),
      };
    }
  },

  fetchHardwareInfo: async () => {
    set({ isLoadingHardware: true });
    try {
      const { api } = await import('./api');
      const info = await api.getHardwareInfo();
      set({ hardwareInfo: info, isLoadingHardware: false });
    } catch {
      set({ isLoadingHardware: false });
    }
  },

  fetchAvailableModels: async () => {
    set({ isLoadingModels: true });
    try {
      const { api } = await import('./api');
      const result = await api.listModels();
      set({ availableModels: result.models, isLoadingModels: false });
    } catch {
      set({ isLoadingModels: false });
    }
  },

  fetchOpenRouterModels: async (apiKey) => {
    set({ isLoadingOpenRouterModels: true });
    try {
      const { api } = await import('./api');
      const result = await api.listOpenRouterModels(apiKey);
      set({ openRouterModels: result.models, isLoadingOpenRouterModels: false });
    } catch {
      set({ isLoadingOpenRouterModels: false });
    }
  },

  pullModel: async (modelName) => {
    try {
      const { api } = await import('./api');
      const result = await api.pullModel(modelName);
      if (result.success) {
        await get().fetchAvailableModels();
      }
      return result.success;
    } catch {
      return false;
    }
  },

  deleteModel: async (modelName) => {
    try {
      const { api } = await import('./api');
      const result = await api.deleteModel(modelName);
      if (result.success) {
        await get().fetchAvailableModels();
      }
      return result.success;
    } catch {
      return false;
    }
  },

  startStatusPolling: () => {
    if (pollingInterval) return;
    pollingInterval = setInterval(() => {
      get().fetchLLMSettings();
    }, 30_000);
  },

  stopStatusPolling: () => {
    if (pollingInterval) {
      clearInterval(pollingInterval);
      pollingInterval = null;
    }
  },
}));
