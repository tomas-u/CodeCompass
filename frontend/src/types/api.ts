/**
 * TypeScript types matching backend Pydantic schemas
 *
 * These types are manually created to match backend/app/schemas/*
 * In the future, these could be auto-generated from OpenAPI spec
 */

// ============================================================================
// Project Types
// ============================================================================

export type SourceType = 'git_url' | 'local_path';

export type ProjectStatus =
  | 'pending'
  | 'cloning'
  | 'scanning'
  | 'analyzing'
  | 'ready'
  | 'failed';

export interface ProjectSettings {
  ignore_patterns: string[];
  analyze_languages: string[];
}

export interface LanguageStats {
  files: number;
  lines: number;
}

export interface ProjectStats {
  files: number;
  directories: number;
  lines_of_code: number;
  languages: Record<string, LanguageStats>;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  source_type: SourceType;
  source: string;
  branch: string;
  local_path?: string;
  status: ProjectStatus;
  settings?: ProjectSettings;
  stats?: ProjectStats;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
  last_analyzed_at?: string; // ISO datetime
}

export interface ProjectCreate {
  name: string;
  source_type: SourceType;
  source: string;
  branch?: string;
  description?: string;
  settings?: ProjectSettings;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
  settings?: ProjectSettings;
}

export interface ProjectListItem {
  id: string;
  name: string;
  source_type: SourceType;
  source: string;
  status: ProjectStatus;
  stats?: ProjectStats;
  last_analyzed_at?: string;
  created_at: string;
}

export interface ProjectListResponse {
  items: ProjectListItem[];
  total: number;
  limit: number;
  offset: number;
}

// ============================================================================
// Analysis Types
// ============================================================================

export type AnalysisStatus =
  | 'queued'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled';

export type StepStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface AnalysisStep {
  name: string;
  status: StepStatus;
  progress_percent?: number;
  duration_ms?: number;
  details?: Record<string, any>;
}

export interface AnalysisProgress {
  current_step: string;
  steps: AnalysisStep[];
  overall_percent: number;
  estimated_remaining_seconds?: number;
}

export interface Analysis {
  id: string;
  project_id: string;
  status: AnalysisStatus;
  progress?: AnalysisProgress;
  stats?: Record<string, any>;
  error?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface AnalysisStartResponse {
  analysis_id: string;
  status: AnalysisStatus;
  message: string;
  estimated_duration_seconds?: number;
}

// ============================================================================
// Report Types
// ============================================================================

export type ReportType = 'summary' | 'architecture' | 'developer' | 'dependencies';

export interface ReportSection {
  id: string;
  title: string;
  content: string;
}

export interface ReportContent {
  format: string;
  body: string;
  sections: ReportSection[];
}

export interface Report {
  id: string;
  type: ReportType;
  title: string;
  content: ReportContent;
  metadata?: Record<string, any>;
  generated_at: string;
}

export interface ReportListItem {
  id: string;
  type: ReportType;
  title: string;
  generated_at: string;
}

// ============================================================================
// Diagram Types
// ============================================================================

export type DiagramType =
  | 'architecture'
  | 'dependency'
  | 'directory'
  | 'class'
  | 'sequence';

export interface Diagram {
  id: string;
  type: DiagramType;
  title: string;
  mermaid_code: string;
  metadata?: Record<string, any>;
  generated_at: string;
}

export interface DiagramListItem {
  id: string;
  type: DiagramType;
  title: string;
  preview_available: boolean;
}

// Dependency Summary types
export interface DependencyStats {
  total_files: number;
  total_dependencies: number;
  max_depth: number;
  leaf_files: number;
  root_files: number;
}

export interface CircularDependency {
  files: string[];
  length: number;
}

export interface CircularDependenciesInfo {
  count: number;
  has_circular: boolean;
  cycles: CircularDependency[];
}

export interface FileCount {
  file: string;
  count: number;
}

export interface DependencySummary {
  project_id: string;
  project_name: string;
  stats: DependencyStats;
  circular_dependencies: CircularDependenciesInfo;
  most_imported: FileCount[];
  most_dependencies: FileCount[];
}

// File dependency (ego graph) types
export interface FileInfo {
  file: string;
  module_name: string;
  language: string;
}

export interface FileDependencyInfo {
  file: string;
  module_name: string;
  language: string;
  imports_count: number;
  imported_by_count: number;
}

export interface FileEgoGraph {
  project_id: string;
  file: string;
  module_name: string;
  language: string;
  imports: FileInfo[];
  imports_count: number;
  imported_by: FileInfo[];
  imported_by_count: number;
  external_deps: string[];
  is_leaf: boolean;
  is_root: boolean;
  in_circular_dependency: boolean;
  circular_cycles: string[][];
}

export interface DependencyFileList {
  project_id: string;
  files: FileDependencyInfo[];
  total: number;
}

// ============================================================================
// File Types
// ============================================================================

export type NodeType = 'file' | 'directory';

export interface FileNode {
  name: string;
  type: NodeType;
  language?: string;
  size_bytes?: number;
  lines?: number;
  children?: FileNode[];
}

export interface FileTreeStats {
  total_files: number;
  total_directories: number;
}

export interface FileTree {
  root: FileNode;
  stats: FileTreeStats;
}

export interface FileContent {
  path: string;
  name: string;
  language: string;
  content: string;
  lines: number;
  size_bytes: number;
  encoding: string;
  last_modified: string;
}

// ============================================================================
// Search Types
// ============================================================================

export interface SearchFilters {
  languages?: string[];
  file_patterns?: string[];
  chunk_types?: string[];
}

export interface SearchRequest {
  query: string;
  limit?: number;
  filters?: SearchFilters;
}

export interface SearchContext {
  module: string;
  imports: string[];
}

export interface SearchResult {
  score: number;
  file_path: string;
  chunk_type: string;
  name: string;
  start_line: number;
  end_line: number;
  content: string;
  language: string;
  context?: SearchContext;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_results: number;
  search_time_ms: number;
}

// ============================================================================
// Chat Types
// ============================================================================

export type MessageRole = 'user' | 'assistant';

export interface ChatSource {
  file_path: string;
  start_line: number;
  end_line: number;
  snippet: string;
  relevance_score: number;
}

export interface ChatOptions {
  include_sources?: boolean;
  max_context_chunks?: number;
  stream?: boolean;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  options?: ChatOptions;
}

export interface TokenUsage {
  prompt: number;
  completion: number;
}

export interface ChatResponseContent {
  content: string;
  format: string;
  sources: ChatSource[];
  tokens_used?: TokenUsage;
}

export interface ChatResponse {
  session_id: string;
  message_id: string;
  response: ChatResponseContent;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  sources?: ChatSource[];
  created_at: string;
}

export interface ChatSession {
  id: string;
  title?: string;
  messages: ChatMessage[];
  created_at: string;
}

export interface ChatSessionListItem {
  id: string;
  title?: string;
  message_count: number;
  created_at: string;
  last_message_at: string;
}

// ============================================================================
// Settings Types
// ============================================================================

export interface LLMCapabilities {
  max_context_length: number;
  supports_streaming: boolean;
}

export interface LLMSettings {
  provider: string;
  model: string;
  status: string;
  capabilities?: LLMCapabilities;
  base_url?: string;
}

export interface EmbeddingSettings {
  model: string;
  dimensions: number;
  status: string;
}

export interface AnalysisSettings {
  supported_languages: string[];
  max_file_size_mb: number;
  max_repo_size_mb: number;
}

export interface Settings {
  llm: LLMSettings;
  embedding: EmbeddingSettings;
  analysis: AnalysisSettings;
}

export interface ProviderInfo {
  id: string;
  name: string;
  status: string;
  models: string[];
}

export interface ModelInfo {
  name: string;
  parameters: string;
  context_length: number;
}

export interface TestConnectionRequest {
  provider: string;
  model: string;
  base_url?: string;
}

export interface TestConnectionResponse {
  success: boolean;
  response_time_ms: number;
  model_info?: ModelInfo;
  error?: string;
}

// ============================================================================
// Health & Root Types
// ============================================================================

export interface HealthResponse {
  status: string;
  version: string;
  uptime_seconds: number;
  llm_provider: string;
  llm_status: string;
}

export interface RootResponse {
  name: string;
  version: string;
  docs_url: string;
}

// ============================================================================
// Error Types
// ============================================================================

export interface ErrorDetails {
  [key: string]: any;
}

export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: ErrorDetails;
  };
  request_id?: string;
  timestamp?: string;
}
