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
  DependencySummary,
  DependencyFileList,
  FileEgoGraph,
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
  // Hardware & Models
  HardwareInfo,
  OllamaModelList,
  ModelPullResponse,
  // OpenRouter
  OpenRouterModelsResponse,
  LLMValidationResponse,
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
  // Admin / Debug
  // ============================================================================

  /**
   * Clear all data from database (development/testing only)
   */
  async clearDatabase(): Promise<{
    message: string;
    tables_cleared: string[];
    records_deleted: { projects: number };
    timestamp: string;
  }> {
    return request('/api/admin/database/clear', {
      method: 'DELETE',
    });
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
   * @param generate - If true, generate report if it doesn't exist (default: true)
   */
  async getReport(projectId: string, type: ReportType, generate: boolean = true): Promise<Report> {
    return request<Report>(`/api/projects/${projectId}/reports/${type}?generate=${generate}`);
  }

  /**
   * Generate or regenerate a report
   * @param force - Force regeneration even if report exists
   */
  async generateReport(
    projectId: string,
    type: ReportType,
    force: boolean = false
  ): Promise<{ message: string; report_id: string; generation_time_ms: string }> {
    return request<{ message: string; report_id: string; generation_time_ms: string }>(
      `/api/projects/${projectId}/reports/generate?report_type=${type}&force=${force}`,
      { method: 'POST' }
    );
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
   *
   * @param projectId - Project ID
   * @param type - Diagram type
   * @param options - Optional parameters for drill-down navigation
   */
  async getDiagram(
    projectId: string,
    type: DiagramType,
    options?: {
      path?: string;
      depth?: number;
      regenerate?: boolean;
      direction?: 'LR' | 'TD';
    }
  ): Promise<Diagram> {
    const queryParams = new URLSearchParams();
    if (options?.path !== undefined) {
      queryParams.append('path', options.path);
    }
    if (options?.depth !== undefined) {
      queryParams.append('depth', options.depth.toString());
    }
    if (options?.regenerate) {
      queryParams.append('regenerate', 'true');
    }
    if (options?.direction) {
      queryParams.append('direction', options.direction);
    }

    const query = queryParams.toString();
    const endpoint = `/api/projects/${projectId}/diagrams/${type}${query ? `?${query}` : ''}`;

    return request<Diagram>(endpoint);
  }

  /**
   * Get diagram as SVG
   */
  async getDiagramSVG(projectId: string, type: DiagramType): Promise<string> {
    return request<string>(`/api/projects/${projectId}/diagrams/${type}/svg`);
  }

  /**
   * Get dependency summary statistics
   */
  async getDependencySummary(projectId: string): Promise<DependencySummary> {
    return request<DependencySummary>(`/api/projects/${projectId}/dependencies/summary`);
  }

  /**
   * Get list of all files with dependency counts
   */
  async getDependencyFiles(projectId: string): Promise<DependencyFileList> {
    return request<DependencyFileList>(`/api/projects/${projectId}/dependencies/files`);
  }

  /**
   * Get ego graph for a specific file (its imports and dependents)
   */
  async getFileDependencies(projectId: string, filePath: string): Promise<FileEgoGraph> {
    return request<FileEgoGraph>(`/api/projects/${projectId}/dependencies/file/${encodeURIComponent(filePath)}`);
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
   * Send chat message with streaming response
   *
   * @param projectId - Project ID
   * @param message - User message
   * @param onToken - Callback for each token received
   * @param onSources - Callback for sources (called once before tokens)
   * @param onDone - Callback when stream is complete
   * @param onError - Callback for errors
   */
  async sendChatMessageStreaming(
    projectId: string,
    message: string,
    onToken: (token: string) => void,
    onSources: (sources: Array<{
      file_path: string;
      start_line: number;
      end_line: number;
      snippet: string;
      relevance_score: number;
    }>) => void,
    onDone: () => void,
    onError: (error: Error) => void,
  ): Promise<void> {
    const url = `${API_CONFIG.baseURL}/api/projects/${projectId}/chat`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          options: { stream: true },
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('Response body is null');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse SSE events from buffer
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        let eventType = '';
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7);
          } else if (line.startsWith('data: ') && eventType) {
            try {
              const data = JSON.parse(line.slice(6));

              switch (eventType) {
                case 'token':
                  if (data.content) {
                    onToken(data.content);
                  }
                  break;
                case 'sources':
                  if (data.sources) {
                    onSources(data.sources);
                  }
                  break;
                case 'done':
                  onDone();
                  break;
                case 'error':
                  onError(new Error(data.message || 'Unknown streaming error'));
                  break;
              }
            } catch (parseError) {
              console.warn('Failed to parse SSE data:', line);
            }
            eventType = '';
          }
        }
      }
    } catch (error) {
      onError(error instanceof Error ? error : new Error('Streaming failed'));
    }
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

  /**
   * Create a new chat session
   */
  async createChatSession(projectId: string, title?: string): Promise<ChatSession> {
    return request<ChatSession>(`/api/projects/${projectId}/chat/sessions`, {
      method: 'POST',
      body: title ? JSON.stringify({ title }) : undefined,
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

  /**
   * Get hardware information and model recommendations
   */
  async getHardwareInfo(): Promise<HardwareInfo> {
    return request<HardwareInfo>('/api/settings/hardware');
  }

  /**
   * List available models from Ollama
   */
  async listModels(): Promise<OllamaModelList> {
    return request<OllamaModelList>('/api/settings/models');
  }

  /**
   * Pull a model from Ollama library
   */
  async pullModel(model: string): Promise<ModelPullResponse> {
    return request<ModelPullResponse>('/api/settings/models/pull', {
      method: 'POST',
      body: JSON.stringify({ model }),
    });
  }

  /**
   * Delete a model from Ollama
   */
  async deleteModel(modelName: string): Promise<ModelPullResponse> {
    return request<ModelPullResponse>(
      `/api/settings/models/${encodeURIComponent(modelName)}`,
      { method: 'DELETE' }
    );
  }

  /**
   * List available OpenRouter models with pricing
   */
  async listOpenRouterModels(): Promise<OpenRouterModelsResponse> {
    return request<OpenRouterModelsResponse>('/api/settings/openrouter/models');
  }

  /**
   * Validate LLM configuration
   */
  async validateLLMConfig(config: {
    provider_type: string;
    model: string;
    base_url?: string;
    api_key?: string;
  }): Promise<LLMValidationResponse> {
    return request<LLMValidationResponse>('/api/settings/llm/validate', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }
}

/**
 * Singleton API client instance
 */
export const api = new CodeCompassAPI();
