# CodeCompass Epic & Story Structure

## Epic #1: Frontend-Backend Integration
**Goal:** Complete the frontend-backend integration by replacing all mock data with real API calls.

**Stories:**
- #9: Connect project list to backend API (Phase 2)
- #10: Implement project creation with backend (Phase 2)
- #11: Add project status polling (Phase 2)
- #12: Implement analysis trigger and status tracking (Phase 3)
- #13: Build analysis progress UI with polling (Phase 3)
- #14: Connect reports to backend API (Phase 4)
- #15: Connect diagrams to backend and implement Mermaid rendering (Phase 4)
- #16: Build file browser and code viewer from backend API (Phase 5)
- #17: Implement semantic search UI (Phase 5)
- #18: Build AI chat interface with RAG (Phase 6)
- #19: Implement chat session management (Phase 6)

## Epic #2: Code Analysis Engine
**Goal:** Build robust code analysis capabilities with hybrid approach: generic analyzer for all languages + specialized enhancements for Python/JS/TS.

**Architecture:**
- Generic analyzer (works with ANY Tree-sitter grammar)
- Language-specific analyzers extend generic with deep insights

**Stories:**
- #33: Build generic Tree-sitter analyzer for all languages (foundation)
- #21: Implement Python-specific analysis enhancements (depends on #33)
- #22: Implement JavaScript/TypeScript-specific analysis enhancements (depends on #33)
- #23: Build dependency graph from analysis data (depends on #33, #21, #22)
- #31: Implement background task orchestration for analysis

## Epic #3: Report Generation System
**Goal:** Generate comprehensive, AI-powered reports analyzing codebase architecture.

**Stories:**
- #24: Implement architecture report generation with LLM (depends on #23)

## Epic #4: Diagram Generation System
**Goal:** Generate interactive Mermaid diagrams visualizing codebase architecture.

**Stories:**
- #25: Generate Mermaid dependency diagrams (depends on #23)

## Epic #5: Vector Search & Embeddings
**Goal:** Build semantic code search using vector embeddings and Qdrant.

**Stories:**
- #26: Set up Qdrant vector database
- #27: Implement code chunking strategy (depends on #33, #21, #22)
- #28: Implement embedding generation service (depends on #27)
- #29: Build semantic search API endpoint (depends on #26, #28)

## Epic #6: AI-Powered Chat (RAG)
**Goal:** Build AI-powered Q&A chat enabling natural language queries about the codebase.

**Stories:**
- #30: Implement RAG pipeline for chat (depends on #29)

## Epic #7: LLM Provider Expansion
**Goal:** Expand LLM provider support beyond local HuggingFace models.

**Stories:**
- #32: Implement multiple LLM provider support

## Epic #8: Polish & Developer Experience
**Goal:** Polish the application with incremental updates, performance optimizations, and export features.

**Stories:**
- (Future stories to be added based on user feedback and testing)

---

## Implementation Phases

### Phase 1: Core Integration (Weeks 1-2)
**Focus:** Get projects and analysis working end-to-end

**Backend:**
- #33: Generic Tree-sitter analyzer (foundation for all languages)
- #21: Python-specific enhancements
- #22: JavaScript/TypeScript-specific enhancements
- #23: Dependency graph building
- #31: Background task orchestration

**Frontend:**
- #9: Project list from API
- #10: Project creation
- #11: Status polling

**Deliverable:** Users can add projects and trigger analysis on Python/JS/TS codebases (with basic support for other languages)

---

### Phase 2: Analysis Flow (Weeks 3-4)
**Focus:** Complete analysis workflow with reports and diagrams

**Backend:**
- #24: Architecture report generation
- #25: Mermaid diagram generation

**Frontend:**
- #12: Analysis trigger UI
- #13: Progress tracking UI
- #14: Report viewer
- #15: Diagram viewer with Mermaid

**Deliverable:** Full analysis workflow with visualizations

---

### Phase 3: Search & Files (Weeks 5-6)
**Focus:** File browsing and semantic search

**Backend:**
- #26: Qdrant setup
- #27: Code chunking
- #28: Embedding generation
- #29: Semantic search API

**Frontend:**
- #16: File browser
- #17: Search UI

**Deliverable:** Users can browse files and search semantically

---

### Phase 4: AI Chat (Weeks 7-8)
**Focus:** Natural language Q&A with RAG

**Backend:**
- #30: RAG pipeline implementation

**Frontend:**
- #18: Chat interface
- #19: Session management

**Deliverable:** Conversational AI about the codebase

---

### Phase 5: Enhancements (Ongoing)
**Focus:** Additional providers, polish, performance

- #32: Multiple LLM providers
- Epic #8: Polish & developer experience

---

## Current Status

- ✅ **Phase 1 Foundation:** API client, types, error handling, health check (completed)
- 🎯 **Next Up:** Phase 1 Core Integration (#9, #10, #11, #33, #21-23, #31)
- 📝 **Architecture Decision:** Hybrid approach with generic analyzer + language-specific enhancements

## Labels

- `epic` - Major feature area
- `story` - User story or feature task
- `phase-2` through `phase-6` - Integration phases
- `backend` - Backend work
- `frontend` - Frontend work
