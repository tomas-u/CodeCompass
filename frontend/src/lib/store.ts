import { create } from 'zustand';

export type ProjectStatus = 'pending' | 'cloning' | 'scanning' | 'analyzing' | 'indexing' | 'ready' | 'failed';

export interface Project {
  id: string;
  name: string;
  sourceType: 'git_url' | 'local_path';
  source: string;
  branch: string;
  status: ProjectStatus;
  stats?: {
    files: number;
    linesOfCode: number;
    languages: string[];
  };
  createdAt: string;
  lastAnalyzedAt?: string;
}

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
  addProject: (project: Project) => void;
  deleteProject: (id: string) => void;
  setAnalysisProgress: (progress: AnalysisProgress | null) => void;
  addChatMessage: (message: ChatMessage) => void;
  clearChat: () => void;
  setIsAiTyping: (typing: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Initial state
  projects: [],
  currentProjectId: null,
  isChatPanelOpen: true,
  activeTab: 'overview',
  analysisProgress: null,
  chatMessages: [],
  isAiTyping: false,

  // Actions
  setCurrentProject: (id) => set({ currentProjectId: id }),

  toggleChatPanel: () => set((state) => ({ isChatPanelOpen: !state.isChatPanelOpen })),

  setActiveTab: (tab) => set({ activeTab: tab }),

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

  clearChat: () => set({ chatMessages: [] }),

  setIsAiTyping: (typing) => set({ isAiTyping: typing }),
}));
