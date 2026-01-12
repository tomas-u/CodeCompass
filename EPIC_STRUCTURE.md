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
**Goal:** Polish the application with LSP semantic analysis, incremental updates, performance optimizations, and export features.

**LSP Integration (Hybrid Tree-sitter + LSP):**
- Adds semantic layer on top of Tree-sitter syntax analysis
- Optional enhancement - graceful fallback if unavailable
- Provides type information, cross-file references, diagnostics

**Stories:**
- #32: Implement multiple LLM provider support
- #34: Build LSP infrastructure for language server management
- #35: Integrate Python LSP for semantic analysis
- #36: Integrate JavaScript/TypeScript LSP for semantic analysis
- #37: Merge LSP semantic data with Tree-sitter analysis
- #38: Generate LSP-enhanced reports with type information
- #39: Implement type-aware and semantic search with LSP
- (Future: Incremental re-analysis, performance optimizations, exports, UI polish)

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

### Phase 5: Enhancements (Weeks 9-10)
**Focus:** LLM providers and LSP semantic analysis

**Backend:**
- #32: Multiple LLM providers (Ollama, OpenAI, Claude)
- #34: LSP infrastructure
- #35: Python LSP integration
- #36: JavaScript/TypeScript LSP integration

**Deliverable:** Flexible LLM configuration and optional semantic analysis layer

---

### Phase 6: Polish (Weeks 11-12+)
**Focus:** LSP-enhanced features, performance, exports

**Backend:**
- #37: Merge LSP data with analysis
- #38: LSP-enhanced reports
- #39: Type-aware search

**Frontend:**
- UI for type-based search
- Export functionality
- Performance optimizations
- Dark mode

**Deliverable:** Production-ready application with semantic features

---

## Current Status

- ✅ **Phase 1 Foundation:** API client, types, error handling, health check (completed)
- 🎯 **Next Up:** Phase 1 Core Integration (#9, #10, #11, #33, #21-23, #31)
- 📝 **Architecture Decisions:**
  - Hybrid analyzer: Generic Tree-sitter + language-specific enhancements
  - Hybrid semantic: Tree-sitter (syntax) + LSP (semantics, optional)

## Labels

- `epic` - Major feature area
- `story` - User story or feature task
- `phase-2` through `phase-6` - Integration phases
- `backend` - Backend work
- `frontend` - Frontend work

---

## Summary

### Total Work Breakdown
- **8 Epics** covering all major feature areas
- **30 User Stories** with acceptance criteria and dependencies
  - Frontend stories: 11
  - Backend stories: 18
  - Full-stack stories: 1
- **6-phase implementation** (12+ weeks)
- **2 major architecture decisions:**
  1. Generic Tree-sitter analyzer + language-specific extensions
  2. Optional LSP semantic layer on top of Tree-sitter

### Hybrid Analysis Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Analysis Pipeline                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Phase 1-4: Tree-sitter (Fast, Always Available)            │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Generic Analyzer (#33)                            │     │
│  │  ├─ Python Enhancements (#21)                      │     │
│  │  ├─ JavaScript/TypeScript Enhancements (#22)       │     │
│  │  └─ Dependency Graph (#23)                         │     │
│  │                                                      │     │
│  │  Results: Syntax, structure, imports, metrics       │     │
│  └────────────────────────────────────────────────────┘     │
│                           │                                  │
│                           ▼                                  │
│  Phase 5-6: LSP (Optional, Semantic Layer)                  │
│  ┌────────────────────────────────────────────────────┐     │
│  │  LSP Infrastructure (#34)                          │     │
│  │  ├─ Python LSP (#35) - Pyright                     │     │
│  │  ├─ JS/TS LSP (#36) - typescript-language-server   │     │
│  │  └─ Analysis Enrichment (#37)                      │     │
│  │                                                      │     │
│  │  Adds: Types, references, diagnostics, cross-file   │     │
│  └────────────────────────────────────────────────────┘     │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Enhanced Features                                 │     │
│  │  ├─ Reports with type info (#38)                   │     │
│  │  └─ Type-aware search (#39)                        │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Key Benefits of Hybrid Approach

**Tree-sitter Alone (MVP):**
- ✅ Fast analysis
- ✅ Works offline
- ✅ Supports 50+ languages immediately
- ✅ No external dependencies
- ✅ 70-80% of value

**Tree-sitter + LSP (Enhanced):**
- ✅ All Tree-sitter benefits
- ✅ Accurate type information
- ✅ Cross-file references
- ✅ Real compiler diagnostics
- ✅ Dead code detection
- ✅ Breaking change analysis
- ✅ Type-aware search
- ✅ 90-95% of value

**Graceful Degradation:**
- LSP is optional enhancement
- Application fully functional without LSP
- Users can enable LSP per language as needed
