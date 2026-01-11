# Claude Instructions

When working on this project:
- Always refer to the architecture in section 4 below
- Follow the implementation phases in section 9
- Use the tech stack decisions in the Quick Reference table
- Check the verification plan (section 14) before completing tasks
- Respect the decisions made in section 10 (LLM providers, database, etc.)

Key commands:
- Backend: `cd backend && uvicorn app.main:app --reload`
- Frontend: `cd frontend && npm run dev`
- Full stack: `docker-compose up`

---

# CodeCompass - Product Requirements Document

## Quick Reference

| Aspect | Decision |
|--------|----------|
| **Stack** | FastAPI (Python) + Next.js + Tailwind |
| **Database** | SQLite (MVP) + Qdrant (vectors) |
| **LLM (Phase 1)** | `microsoft/Phi-3.5-mini-instruct` (self-hosted) |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` |
| **LLM (Later)** | Ollama/LM Studio → Cloud APIs (optional) |
| **Languages** | Python + JavaScript/TypeScript analyzers |
| **Tasks** | FastAPI BackgroundTasks (no Redis/Celery) |
| **Auth** | None (local single-user) |
| **Deployment** | Docker Compose (local only) |

---

## Executive Summary

CodeCompass is an intelligent code analysis platform that helps developers and architects understand complex codebases through automated analysis, visual diagrams, and AI-powered Q&A. It transforms unfamiliar repositories into navigable knowledge bases.

---

## 1. Product Vision

**Mission:** Enable any developer to quickly understand and navigate unfamiliar codebases through intelligent analysis and natural language interaction.

**Problem Statement:**
- Developers spend 60%+ of time reading/understanding code rather than writing it
- Onboarding to new codebases takes weeks or months
- Documentation is often outdated or missing
- Understanding system architecture requires significant tribal knowledge

**Solution:** An automated platform that:
1. Analyzes git repositories to extract structure, patterns, and relationships
2. Generates comprehensive reports with visual Mermaid diagrams
3. Creates a semantic vector database for intelligent code search
4. Enables natural language Q&A about the codebase

---

## 2. User Personas

### Primary: New Team Member
- Just joined a project, needs to understand codebase quickly
- Wants to know "where does X happen?" and "how does Y work?"

### Secondary: Tech Lead / Architect
- Needs high-level system overview for decision-making
- Wants to identify patterns, dependencies, and potential issues

### Tertiary: External Auditor / Consultant
- Limited time to understand a system
- Needs quick architectural understanding

---

## 3. Core Features

### 3.1 Repository Ingestion
- **Git Clone/Import:** Support public/private repos (GitHub, GitLab, Bitbucket, local)
- **Smart Filtering:** Respect `.gitignore`, exclude build artifacts, node_modules, etc.
- **Language Detection:** Auto-detect programming languages and frameworks
- **Incremental Updates:** Re-analyze only changed files on subsequent scans

### 3.2 Code Analysis Engine
- **Static Analysis:**
  - File structure and organization
  - Module/package dependencies
  - Class/function relationships
  - Import/export analysis
  - Entry points detection (main files, API routes, etc.)

- **Pattern Detection:**
  - Design patterns (MVC, Repository, Factory, etc.)
  - Architectural patterns (Microservices, Monolith, etc.)
  - Framework conventions (React components, FastAPI routes, etc.)

- **Metrics:**
  - Lines of code per module
  - Complexity indicators
  - Dependency depth
  - File coupling analysis

### 3.3 Report Generation
- **Executive Summary:** High-level overview for non-technical stakeholders
- **Architecture Report:** System design, layers, and component interactions
- **Developer Guide:** Entry points, key files, common patterns
- **Dependency Analysis:** External packages, internal modules, circular deps

### 3.4 Mermaid Diagram Generation
- **System Architecture Diagram:** High-level component overview
- **Module Dependency Graph:** How packages/modules relate
- **Class Diagrams:** OOP relationships (for applicable languages)
- **Sequence Diagrams:** Key flows (API request handling, etc.)
- **Entity Relationship Diagrams:** Database schema visualization
- **Directory Tree Diagrams:** File structure visualization

### 3.5 Vector Database & Semantic Search
- **Code Embedding:** Convert code chunks to vectors using code-aware models
- **Multi-level Chunking:**
  - File level (whole file context)
  - Function/class level (semantic units)
  - Block level (logical sections)
- **Metadata Storage:** File paths, language, type, relationships
- **Hybrid Search:** Combine semantic + keyword search

### 3.6 AI-Powered Q&A
- **Natural Language Queries:** "How does authentication work?"
- **Code-Aware Responses:** Include relevant code snippets
- **Context-Aware:** Understands project structure and relationships
- **Citation:** Always reference source files and line numbers

---

## 4. Technical Architecture

### 4.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐│
│  │Dashboard │ │ Reports  │ │ Diagrams │ │    Chat Interface    ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │ REST/WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │
│  │ Repo Service │ │Analysis Svc  │ │      Q&A Service         │ │
│  └──────────────┘ └──────────────┘ └──────────────────────────┘ │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │
│  │Report Gen    │ │ Diagram Gen  │ │    Embedding Service     │ │
│  └──────────────┘ └──────────────┘ └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │                │                      │
         ▼                ▼                      ▼
┌──────────────┐  ┌──────────────┐      ┌──────────────┐
│  PostgreSQL  │  │    Redis     │      │    Qdrant    │
│  (metadata)  │  │   (cache)    │      │  (vectors)   │
└──────────────┘  └──────────────┘      └──────────────┘
```

### 4.2 Technology Stack

**Frontend:**
- Next.js 14+ (App Router)
- Tailwind CSS
- TypeScript
- Mermaid.js for diagram rendering
- React Query for data fetching
- Zustand for state management

**Backend:**
- Python 3.11+
- FastAPI
- Pydantic for validation
- SQLAlchemy for ORM
- FastAPI BackgroundTasks for async jobs
- Tree-sitter for code parsing

**Databases:**
- SQLite: Projects, analysis metadata, reports (simple, file-based)
- Qdrant: Vector embeddings for semantic search

**AI/ML - Flexible LLM Architecture:**
```
┌─────────────────────────────────────────────────────────────────┐
│                    LLM Provider Interface                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Abstract LLMProvider Base Class              │   │
│  │  - generate(prompt) -> str                                │   │
│  │  - embed(text) -> List[float]                             │   │
│  │  - get_model_info() -> dict                               │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  LocalProvider  │  │  OllamaProvider │  │  CloudProvider  │
│  (HuggingFace   │  │  (API to local  │  │  (OpenAI,       │
│   Transformers) │  │   Ollama/LM     │  │   Claude, etc.) │
│                 │  │   Studio)       │  │                 │
│  Phase 1: MVP   │  │  Phase 2        │  │  Phase 3        │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

**Phase 1 - Self-hosted models:**
- Text Generation: `microsoft/Phi-3.5-mini-instruct` (3.8B params, strong instruction following)
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2` (384 dims, fast)
- Libraries: `transformers`, `sentence-transformers`, `torch`
- Background Tasks: FastAPI BackgroundTasks (simple, no Redis needed)

**Phase 2 - Local model servers:**
- Support Ollama API (`http://localhost:11434`)
- Support LM Studio API (`http://localhost:1234`)
- Same interface, just different backend

**Phase 3 - Cloud providers (optional):**
- OpenAI API
- Anthropic Claude API
- Configurable via environment variables

**Infrastructure:**
- Docker & Docker Compose (local development)
- Single-user, no authentication

### 4.3 Backend Service Breakdown

```
backend/
├── app/
│   ├── main.py                 # FastAPI app initialization
│   ├── config.py               # Settings and configuration
│   ├── database.py             # SQLAlchemy setup
│   ├── api/
│   │   ├── routes/
│   │   │   ├── projects.py     # Project CRUD
│   │   │   ├── analysis.py     # Trigger/status analysis
│   │   │   ├── reports.py      # Report generation/retrieval
│   │   │   ├── diagrams.py     # Diagram generation
│   │   │   ├── chat.py         # Q&A endpoints
│   │   │   ├── search.py       # Code search
│   │   │   └── settings.py     # LLM provider settings
│   │   └── deps.py             # Dependency injection
│   ├── services/
│   │   ├── git_service.py      # Clone, pull, file operations
│   │   ├── llm/                # LLM Provider Abstraction
│   │   │   ├── base.py         # Abstract LLMProvider class
│   │   │   ├── local_provider.py    # HuggingFace transformers
│   │   │   ├── ollama_provider.py   # Ollama API client
│   │   │   ├── lmstudio_provider.py # LM Studio API client
│   │   │   ├── cloud_provider.py    # OpenAI/Claude (future)
│   │   │   └── factory.py      # Provider factory
│   │   ├── analyzer/
│   │   │   ├── base.py         # Abstract analyzer
│   │   │   ├── python_analyzer.py
│   │   │   ├── javascript_analyzer.py
│   │   │   └── generic_analyzer.py
│   │   ├── report_generator.py
│   │   ├── diagram_generator.py
│   │   ├── embedding_service.py
│   │   ├── vector_service.py   # Qdrant operations
│   │   └── chat_service.py     # RAG implementation
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   └── tasks/                  # Background tasks
├── tests/
├── requirements.txt
└── Dockerfile
```

### 4.4 Frontend Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx            # Landing/Dashboard
│   │   ├── projects/
│   │   │   ├── page.tsx        # Project list
│   │   │   ├── [id]/
│   │   │   │   ├── page.tsx    # Project overview
│   │   │   │   ├── reports/
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── diagrams/
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── chat/
│   │   │   │   │   └── page.tsx
│   │   │   │   └── files/
│   │   │   │       └── page.tsx
│   │   │   └── new/
│   │   │       └── page.tsx
│   │   └── settings/
│   │       └── page.tsx        # LLM provider configuration
│   ├── components/
│   │   ├── ui/                 # Base components (shadcn/ui)
│   │   ├── diagrams/           # Mermaid wrappers
│   │   ├── chat/               # Chat interface
│   │   ├── reports/            # Report viewers
│   │   └── files/              # File tree, code viewer
│   ├── lib/
│   │   ├── api.ts              # API client
│   │   └── utils.ts
│   └── hooks/
├── public/
├── package.json
├── tailwind.config.js
├── tsconfig.json
├── next.config.js
└── Dockerfile
```

---

## 5. Data Models

### 5.1 Core Entities

**Project**
```
- id: UUID
- name: string
- description: string
- git_url: string
- branch: string
- status: enum (pending, analyzing, ready, failed)
- created_at: datetime
- updated_at: datetime
- settings: JSON (ignore patterns, analysis options)
```

**Analysis**
```
- id: UUID
- project_id: FK
- status: enum (queued, running, completed, failed)
- started_at: datetime
- completed_at: datetime
- stats: JSON (files analyzed, LOC, etc.)
- error: string (if failed)
```

**Report**
```
- id: UUID
- project_id: FK
- analysis_id: FK
- type: enum (summary, architecture, developer, dependency)
- content: JSON/Markdown
- created_at: datetime
```

**Diagram**
```
- id: UUID
- project_id: FK
- type: enum (architecture, dependency, class, sequence, erd)
- mermaid_code: text
- metadata: JSON
- created_at: datetime
```

**CodeChunk** (for vector DB)
```
- id: UUID
- project_id: FK
- file_path: string
- chunk_type: enum (file, function, class, block)
- content: text
- start_line: int
- end_line: int
- language: string
- embedding: vector[1536]
- metadata: JSON
```

**ChatSession**
```
- id: UUID
- project_id: FK
- created_at: datetime
```

**ChatMessage**
```
- id: UUID
- session_id: FK
- role: enum (user, assistant)
- content: text
- sources: JSON (file references)
- created_at: datetime
```

---

## 6. API Endpoints

### Projects
- `POST /api/projects` - Create new project
- `GET /api/projects` - List projects
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project
- `POST /api/projects/{id}/sync` - Trigger git sync

### Analysis
- `POST /api/projects/{id}/analyze` - Start analysis
- `GET /api/projects/{id}/analysis` - Get latest analysis
- `GET /api/projects/{id}/analysis/{analysis_id}` - Get specific analysis

### Reports
- `GET /api/projects/{id}/reports` - List reports
- `GET /api/projects/{id}/reports/{type}` - Get specific report
- `POST /api/projects/{id}/reports/generate` - Regenerate reports

### Diagrams
- `GET /api/projects/{id}/diagrams` - List diagrams
- `GET /api/projects/{id}/diagrams/{type}` - Get specific diagram
- `POST /api/projects/{id}/diagrams/generate` - Regenerate diagrams

### Search & Chat
- `POST /api/projects/{id}/search` - Semantic code search
- `POST /api/projects/{id}/chat` - Send chat message
- `GET /api/projects/{id}/chat/sessions` - List chat sessions
- `GET /api/projects/{id}/chat/sessions/{session_id}` - Get session history

### Files
- `GET /api/projects/{id}/files` - Get file tree
- `GET /api/projects/{id}/files/{path}` - Get file content

### Settings (LLM Provider)
- `GET /api/settings` - Get current settings (provider, model, etc.)
- `PUT /api/settings` - Update settings
- `GET /api/settings/providers` - List available providers
- `GET /api/settings/models` - List available models for current provider
- `POST /api/settings/test` - Test LLM connection

---

## 7. Key User Flows

### Flow 1: New Project Analysis
1. User enters git URL (or uploads local repo)
2. System clones repository
3. System runs analysis (background job)
4. User sees progress indicator
5. Analysis completes → Reports and diagrams generated
6. Code indexed into vector DB
7. User can view reports, diagrams, and start chatting

### Flow 2: Ask a Question
1. User types natural language question
2. System generates embedding for question
3. System searches Qdrant for relevant code chunks
4. System constructs prompt with context
5. LLM generates answer with code references
6. Response displayed with clickable file links

### Flow 3: Explore Diagram
1. User navigates to diagrams section
2. User selects diagram type (architecture, dependencies, etc.)
3. Mermaid diagram rendered
4. User can zoom, pan, and click nodes
5. Clicking node shows related code/details

---

## 8. Non-Functional Requirements

### Performance
- Repository cloning: < 2 minutes for repos < 500MB
- Analysis: < 5 minutes for repos < 10k files
- Search response: < 2 seconds
- Chat response: Depends on local hardware (5-30 seconds for small models)

### Scalability
- Support repos up to 1GB / 100k files
- Single-user local deployment (no multi-tenancy needed)

### Security (Local Deployment)
- No authentication required (local-only, single user)
- Input validation on all endpoints
- Never execute analyzed code
- Git credentials handled via user's local git config

### Reliability
- Background job retry on failure
- Graceful degradation if LLM unavailable
- SQLite database with file-based backups

---

## 9. Implementation Phases

### Phase 1: Foundation (MVP)
- [ ] Project setup (monorepo structure with Docker Compose)
- [ ] Basic FastAPI backend with project CRUD
- [ ] SQLite database setup with SQLAlchemy
- [ ] Git cloning service (local path or URL)
- [ ] Basic file tree analysis
- [ ] Simple Next.js frontend with project list/dashboard
- [ ] **LLM Provider abstraction** with LocalProvider (HuggingFace small model)
- [ ] Basic Python analyzer (using Tree-sitter)

### Phase 2: Core Analysis & Reports
- [ ] JavaScript/TypeScript analyzer (Tree-sitter)
- [ ] Dependency graph extraction (imports/exports)
- [ ] Basic report generation (markdown)
- [ ] Mermaid diagram generation (file structure, dependencies)
- [ ] Report viewing UI with Mermaid rendering

### Phase 3: Vector Search & Embeddings
- [ ] Qdrant integration (Docker container)
- [ ] Code chunking strategy (file/function/class level)
- [ ] Local embedding pipeline (sentence-transformers)
- [ ] Semantic search API
- [ ] Search UI with code highlighting

### Phase 4: AI Chat (RAG)
- [ ] RAG implementation with retrieved context
- [ ] Chat API endpoints (streaming optional)
- [ ] Chat UI with conversation history
- [ ] Source citations with file links

### Phase 5: LLM Provider Expansion
- [ ] OllamaProvider implementation
- [ ] LM Studio provider implementation
- [ ] Provider switching via settings UI
- [ ] Model selection UI

### Phase 6: Polish & Enhancements
- [ ] Incremental re-analysis (changed files only)
- [ ] Additional diagram types (class, sequence)
- [ ] Export functionality (PDF/HTML reports)
- [ ] Performance optimization
- [ ] CloudProvider (OpenAI/Claude) - optional

---

## 10. Decisions Made

| Question | Decision |
|----------|----------|
| **LLM Provider** | Self-hosted first → Ollama/LM Studio → Cloud APIs (optional) |
| **Text Generation Model** | `microsoft/Phi-3.5-mini-instruct` (3.8B params) |
| **Embedding Model** | `sentence-transformers/all-MiniLM-L6-v2` (384 dims) |
| **Authentication** | None - local single-user deployment |
| **Hosting** | Local Docker Compose only |
| **Languages** | Python + JavaScript/TypeScript analyzers |
| **Database** | SQLite (simple, file-based) |
| **Background Tasks** | FastAPI BackgroundTasks (no Redis/Celery) |

---

## 11. Success Metrics

- Time to first insight: < 15 minutes from URL to answers
- Chat accuracy: 80%+ relevant responses
- User onboarding: < 5 minutes to analyze first repo
- Report usefulness: 4+/5 user rating

---

## 12. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Large repos overwhelm system | Size limits, incremental processing, .gitignore respect |
| Local LLM quality insufficient | Design provider abstraction to easily switch to better models |
| Slow local inference | Use smaller models, cache embeddings, async processing |
| Poor analysis accuracy | Language-specific Tree-sitter analyzers, iterative improvement |
| Hardware requirements too high | Start with smallest viable models, GPU optional |

---

## 13. Files to Create (Phase 1 MVP)

### Root
```
/docker-compose.yml          # Backend, Frontend, Qdrant services
/.gitignore
/.env.example                # LLM_PROVIDER, MODEL_NAME, etc.
/README.md
```

### Backend
```
/backend/
├── requirements.txt         # fastapi, uvicorn, sqlalchemy, tree-sitter, etc.
├── Dockerfile
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, CORS, routes
│   ├── config.py            # Pydantic Settings
│   ├── database.py          # SQLAlchemy engine, session
│   ├── models/
│   │   ├── __init__.py
│   │   └── project.py       # Project, Analysis, Report models
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── project.py       # Pydantic request/response schemas
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── projects.py
│   │       └── settings.py
│   └── services/
│       ├── __init__.py
│       ├── git_service.py
│       └── llm/
│           ├── __init__.py
│           ├── base.py
│           └── local_provider.py
```

### Frontend
```
/frontend/
├── package.json
├── Dockerfile
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── projects/
│   │   │   ├── page.tsx
│   │   │   └── new/page.tsx
│   │   └── settings/page.tsx
│   ├── components/
│   │   └── ui/              # Button, Card, Input (shadcn/ui)
│   └── lib/
│       └── api.ts
```

---

## 14. Verification Plan

### Automated Testing
- **Backend:** pytest with test fixtures for small repos
- **Frontend:** Jest + React Testing Library for components
- **API:** pytest-asyncio for endpoint testing

### Manual Testing Checklist
1. **Project Creation:**
   - Add a project via local path
   - Add a project via git URL
   - Verify .gitignore patterns respected

2. **Analysis:**
   - Trigger analysis on small Python project
   - Verify file tree extracted correctly
   - Check analysis status updates in UI

3. **Reports & Diagrams:**
   - View generated architecture report
   - Render Mermaid dependency diagram
   - Verify diagrams are interactive

4. **Search & Chat:**
   - Search for a function name
   - Ask "How does X work?"
   - Verify code snippets in response have correct file links

5. **LLM Provider:**
   - Test with local small model
   - Switch to Ollama (if installed)
   - Verify settings persist

### Test Repositories
- Small: This project itself (CodeCompass)
- Medium: A real open-source project (e.g., FastAPI repo)
- Edge case: Monorepo with multiple languages
