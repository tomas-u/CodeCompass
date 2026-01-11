/**
 * API Client for CodeCompass Backend
 *
 * Provides a clean interface for making HTTP requests to the FastAPI backend.
 * Uses native fetch API with proper error handling and timeout support.
 *
 * Usage:
 *   import { api } from '@/lib/api'
 *   const projects = await api.getProjects()
 *
 * Error handling:
 *   try {
 *     const project = await api.getProject(id)
 *   } catch (error) {
 *     if (isApiError(error)) {
 *       console.log(error.code) // e.g., "PROJECT_NOT_FOUND"
 *       console.log(error.getUserMessage()) // User-friendly message
 *     }
 *   }
 */

import { API_CONFIG } from './api-config';
import { ApiError, NetworkError, TimeoutError, logError } from './api-error';
import type {
  // Root & Health
  RootResponse,
  HealthResponse,
  // Projects
  Project,
  ProjectCreate,
  ProjectUpdate,
  ProjectListResponse,
  // Analysis
  Analysis,
  AnalysisStartResponse,
  // Reports
  Report,
  ReportListItem,
  ReportType,
  // Diagrams
  Diagram,
  DiagramListItem,
  DiagramType,
  // Files
  FileTree,
  FileContent,
  // Search
  SearchRequest,
  SearchResponse,
  // Chat
  ChatRequest,
  ChatResponse,
  ChatSession,
  ChatSessionListItem,
  // Settings
  Settings,
  ProviderInfo,
  TestConnectionRequest,
  TestConnectionResponse,
  // Errors
  ErrorResponse,
} from '@/types/api';

/**
 * Fetch with timeout support
 */
async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeout: number = API_CONFIG.timeout
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        throw new TimeoutError();
      }
      // Network error (connection refused, DNS failure, etc.)
      throw new NetworkError(error.message);
    }

    throw error;
  }
}

/**
 * Handle API response and errors
 */
async function handleResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get('content-type');
  const isJson = contentType?.includes('application/json');

  if (!response.ok) {
    // Try to parse error response
    if (isJson) {
      try {
        const errorData: ErrorResponse = await response.json();
        throw ApiError.fromResponse(errorData, response.status);
      } catch (error) {
        // If JSON parsing fails, throw generic error
        if (error instanceof ApiError) {
          throw error;
        }
      }
    }

    // Generic HTTP error
    throw new ApiError(
      response.statusText || 'Request failed',
      'HTTP_ERROR',
      response.status
    );
  }

  // Parse successful response
  if (isJson) {
    return response.json();
  }

  // For non-JSON responses (like SVG)
  return response.text() as any;
}

/**
 * Make HTTP request with error handling
 */
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_CONFIG.baseURL}${endpoint}`;

  const requestOptions: RequestInit = {
    ...options,
    headers: {
      ...API_CONFIG.headers,
      ...options.headers,
    },
  };

  try {
    const response = await fetchWithTimeout(url, requestOptions);
    return handleResponse<T>(response);
  } catch (error) {
    logError(error, endpoint);
    throw error;
  }
}

/**
 * CodeCompass API Client
 */
class CodeCompassAPI {
  // ============================================================================
  // Root & Health
  // ============================================================================

  /**
   * Get API root information
   */
  async getRoot(): Promise<RootResponse> {
    return request<RootResponse>('/');
  }

  /**
   * Health check endpoint
   */
  async healthCheck(): Promise<HealthResponse> {
    return request<HealthResponse>('/health');
  }

  // ============================================================================
  // Projects
  // ============================================================================

  /**
   * List all projects
   */
  async getProjects(params?: {
    status?: string;
    search?: string;
    sort?: string;
    order?: 'asc' | 'desc';
    limit?: number;
    offset?: number;
  }): Promise<ProjectListResponse> {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }

    const query = queryParams.toString();
    const endpoint = `/api/projects${query ? `?${query}` : ''}`;

    return request<ProjectListResponse>(endpoint);
  }

  /**
   * Get project by ID
   */
  async getProject(id: string): Promise<Project> {
    return request<Project>(`/api/projects/${id}`);
  }

  /**
   * Create new project
   */
  async createProject(data: ProjectCreate): Promise<Project> {
    return request<Project>('/api/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * Update project
   */
  async updateProject(id: string, data: ProjectUpdate): Promise<Project> {
    return request<Project>(`/api/projects/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  /**
   * Delete project
   */
  async deleteProject(id: string, deleteFiles: boolean = true): Promise<void> {
    const params = new URLSearchParams({ delete_files: deleteFiles.toString() });
    return request<void>(`/api/projects/${id}?${params}`);
  }

  // ============================================================================
  // Analysis
  // ============================================================================

  /**
   * Start code analysis
   */
  async startAnalysis(
    projectId: string,
    options?: {
      force?: boolean;
      generate_reports?: boolean;
      generate_diagrams?: boolean;
      build_embeddings?: boolean;
    }
  ): Promise<AnalysisStartResponse> {
    return request<AnalysisStartResponse>(
      `/api/projects/${projectId}/analyze`,
      {
        method: 'POST',
        body: options ? JSON.stringify(options) : undefined,
      }
    );
  }

  /**
   * Get analysis status
   */
  async getAnalysisStatus(projectId: string): Promise<Analysis> {
    return request<Analysis>(`/api/projects/${projectId}/analysis`);
  }

  /**
   * Cancel ongoing analysis
   */
  async cancelAnalysis(projectId: string): Promise<void> {
    return request<void>(`/api/projects/${projectId}/analysis`, {
      method: 'DELETE',
    });
  }

  // ============================================================================
  // Reports
  // ============================================================================

  /**
   * List all reports for a project
   */
  async listReports(projectId: string): Promise<ReportListItem[]> {
    const response = await request<{ items: ReportListItem[] }>(
      `/api/projects/${projectId}/reports`
    );
    return response.items;
  }

  /**
   * Get specific report
   */
  async getReport(projectId: string, type: ReportType): Promise<Report> {
    return request<Report>(`/api/projects/${projectId}/reports/${type}`);
  }

  // ============================================================================
  // Diagrams
  // ============================================================================

  /**
   * List all diagrams for a project
   */
  async listDiagrams(projectId: string): Promise<DiagramListItem[]> {
    const response = await request<{ items: DiagramListItem[] }>(
      `/api/projects/${projectId}/diagrams`
    );
    return response.items;
  }

  /**
   * Get specific diagram
   */
  async getDiagram(projectId: string, type: DiagramType): Promise<Diagram> {
    return request<Diagram>(`/api/projects/${projectId}/diagrams/${type}`);
  }

  /**
   * Get diagram as SVG
   */
  async getDiagramSVG(projectId: string, type: DiagramType): Promise<string> {
    return request<string>(`/api/projects/${projectId}/diagrams/${type}/svg`);
  }

  // ============================================================================
  // Files
  // ============================================================================

  /**
   * Get file tree structure
   */
  async getFileTree(
    projectId: string,
    options?: {
      depth?: number;
      include_hidden?: boolean;
    }
  ): Promise<FileTree> {
    const queryParams = new URLSearchParams();
    if (options?.depth) {
      queryParams.append('depth', options.depth.toString());
    }
    if (options?.include_hidden) {
      queryParams.append('include_hidden', 'true');
    }

    const query = queryParams.toString();
    const endpoint = `/api/projects/${projectId}/files${query ? `?${query}` : ''}`;

    return request<FileTree>(endpoint);
  }

  /**
   * Get file content
   */
  async getFileContent(projectId: string, filePath: string): Promise<FileContent> {
    return request<FileContent>(`/api/projects/${projectId}/files/${filePath}`);
  }

  // ============================================================================
  // Search
  // ============================================================================

  /**
   * Search code semantically
   */
  async searchCode(projectId: string, searchRequest: SearchRequest): Promise<SearchResponse> {
    return request<SearchResponse>(`/api/projects/${projectId}/search`, {
      method: 'POST',
      body: JSON.stringify(searchRequest),
    });
  }

  // ============================================================================
  // Chat
  // ============================================================================

  /**
   * Send chat message
   */
  async sendChatMessage(
    projectId: string,
    chatRequest: ChatRequest
  ): Promise<ChatResponse> {
    return request<ChatResponse>(`/api/projects/${projectId}/chat`, {
      method: 'POST',
      body: JSON.stringify(chatRequest),
    });
  }

  /**
   * List chat sessions
   */
  async listChatSessions(projectId: string): Promise<ChatSessionListItem[]> {
    const response = await request<{ items: ChatSessionListItem[] }>(
      `/api/projects/${projectId}/chat/sessions`
    );
    return response.items;
  }

  /**
   * Get chat session history
   */
  async getChatSession(projectId: string, sessionId: string): Promise<ChatSession> {
    return request<ChatSession>(
      `/api/projects/${projectId}/chat/sessions/${sessionId}`
    );
  }

  /**
   * Delete chat session
   */
  async deleteChatSession(projectId: string, sessionId: string): Promise<void> {
    return request<void>(`/api/projects/${projectId}/chat/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  }

  // ============================================================================
  // Settings
  // ============================================================================

  /**
   * Get current settings
   */
  async getSettings(): Promise<Settings> {
    return request<Settings>('/api/settings');
  }

  /**
   * Update settings
   */
  async updateSettings(settings: Partial<Settings>): Promise<Settings> {
    return request<Settings>('/api/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  /**
   * List available LLM providers
   */
  async listProviders(): Promise<ProviderInfo[]> {
    const response = await request<{ providers: ProviderInfo[] }>(
      '/api/settings/providers'
    );
    return response.providers;
  }

  /**
   * Test LLM connection
   */
  async testConnection(
    config: TestConnectionRequest
  ): Promise<TestConnectionResponse> {
    return request<TestConnectionResponse>('/api/settings/test', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }
}

/**
 * Singleton API client instance
 */
export const api = new CodeCompassAPI();
