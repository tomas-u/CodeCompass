import { create } from 'zustand';
import type { ProjectListItem, ProjectStatus as ApiProjectStatus } from '@/types/api';

// Type alias for internal use and re-export for convenience
export type Project = ProjectListItem;
export type ProjectStatus = ApiProjectStatus;

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
  currentStep: 'cloning' | 'scanning' | 'analyzing' | 'generating' | 'indexing';
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

  // Actions
  setCurrentProject: (id: string | null) => void;
  toggleChatPanel: () => void;
  setActiveTab: (tab: 'overview' | 'diagrams' | 'files' | 'reports') => void;
  fetchProjects: () => Promise<void>;
  setProjects: (projects: Project[]) => void;
  addProject: (project: Project) => void;
  deleteProject: (id: string) => void;
  setAnalysisProgress: (progress: AnalysisProgress | null) => void;
  addChatMessage: (message: ChatMessage) => void;
  updateChatMessage: (id: string, updater: (msg: ChatMessage) => ChatMessage) => void;
  clearChat: () => void;
  setIsAiTyping: (typing: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
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

  // Actions
  setCurrentProject: (id) => set({ currentProjectId: id }),

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

  addChatMessage: (message) => set((state) => ({
    chatMessages: [...state.chatMessages, message]
  })),

  updateChatMessage: (id, updater) => set((state) => ({
    chatMessages: state.chatMessages.map((msg) =>
      msg.id === id ? updater(msg) : msg
    ),
  })),

  clearChat: () => set({ chatMessages: [] }),

  setIsAiTyping: (typing) => set({ isAiTyping: typing }),
}));
