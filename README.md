# CodeCompass

An intelligent code analysis platform that helps developers understand complex codebases through automated analysis, visual diagrams, and AI-powered Q&A.

## Overview

CodeCompass transforms unfamiliar repositories into navigable knowledge bases by:

1. **Analyzing git repositories** to extract structure, patterns, and relationships
2. **Generating comprehensive reports** with visual Mermaid diagrams
3. **Creating semantic vector databases** for intelligent code search
4. **Enabling natural language Q&A** about the codebase

### Problem It Solves

- Developers spend 60%+ of time reading/understanding code rather than writing it
- Onboarding to new codebases takes weeks or months
- Documentation is often outdated or missing
- Understanding system architecture requires significant tribal knowledge

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OR: Python 3.11+, Node.js 18+, Ollama

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/codecompass.git
cd codecompass

# Start all services
docker compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Local Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Environment Variables

Create a `.env` file in the backend directory:

```bash
# LLM Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b

# Vector Database
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Embedding Service
EMBEDDING_SERVICE_URL=http://localhost:8001
```

## Features

### Repository Ingestion
- **Git Clone/Import:** Support public/private repos (GitHub, GitLab, Bitbucket, local)
- **Smart Filtering:** Respects `.gitignore`, excludes build artifacts, node_modules
- **Language Detection:** Auto-detects 30+ programming languages
- **Incremental Updates:** Re-analyzes only changed files

### Code Analysis Engine
- **Static Analysis:** File structure, module dependencies, class/function relationships
- **Pattern Detection:** Design patterns, architectural patterns, framework conventions
- **Metrics:** Lines of code, complexity indicators, dependency depth

### Report Generation
- **Executive Summary:** High-level overview for stakeholders
- **Architecture Report:** System design, layers, component interactions
- **Developer Guide:** Entry points, key files, common patterns
- **Dependency Analysis:** External packages, internal modules, circular deps

### Diagram Generation (Mermaid)
- System Architecture Diagram
- Module Dependency Graph
- Class Diagrams
- Sequence Diagrams
- Entity Relationship Diagrams
- Directory Tree Diagrams

### AI-Powered Chat (RAG)
- Natural language queries about the codebase
- Code-aware responses with relevant snippets
- Source citations with file links
- Streaming responses via SSE

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐│
│  │Dashboard │ │ Reports  │ │ Diagrams │ │    Chat Interface    ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │ REST/SSE
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │
│  │ Git Service  │ │Analysis Svc  │ │      RAG Service         │ │
│  └──────────────┘ └──────────────┘ └──────────────────────────┘ │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │
│  │Report Gen    │ │ Diagram Gen  │ │   Embedding Service      │ │
│  └──────────────┘ └──────────────┘ └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │                                       │
         ▼                                       ▼
┌──────────────┐                        ┌──────────────┐
│   SQLite     │                        │    Qdrant    │
│  (metadata)  │                        │  (vectors)   │
└──────────────┘                        └──────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | FastAPI (Python 3.11+) |
| **Frontend** | Next.js 14+ (App Router), Tailwind CSS, TypeScript |
| **Database** | SQLite (metadata), Qdrant (vectors) |
| **ORM** | SQLAlchemy |
| **Code Parsing** | Tree-sitter (30+ languages) |
| **LLM** | Ollama (configurable) |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 |
| **Diagrams** | Mermaid.js |
| **State Management** | Zustand, React Query |

## API Overview

### Projects
```
POST   /api/projects              Create project
GET    /api/projects              List projects
GET    /api/projects/{id}         Get project
PUT    /api/projects/{id}         Update project
DELETE /api/projects/{id}         Delete project
```

### Analysis
```
POST   /api/projects/{id}/analyze    Start analysis
GET    /api/projects/{id}/analysis   Get analysis status
```

### Reports & Diagrams
```
GET    /api/projects/{id}/reports           List reports
GET    /api/projects/{id}/reports/{type}    Get report
GET    /api/projects/{id}/diagrams          List diagrams
GET    /api/projects/{id}/diagrams/{type}   Get diagram
```

### Search & Chat
```
POST   /api/projects/{id}/search                     Semantic search
POST   /api/projects/{id}/chat                       Chat (supports SSE streaming)
GET    /api/projects/{id}/chat/sessions              List sessions
GET    /api/projects/{id}/chat/sessions/{session}    Get session
```

### Settings
```
GET    /api/settings              Get settings
PUT    /api/settings              Update settings
GET    /api/settings/providers    List LLM providers
POST   /api/settings/test         Test LLM connection
```

Full API documentation available at `http://localhost:8000/docs` when running.

## Project Structure

```
codecompass/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── api/routes/          # API endpoints
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   └── services/            # Business logic
│   │       ├── git_service.py
│   │       ├── analysis_service.py
│   │       ├── chunking_service.py
│   │       ├── vector_service.py
│   │       ├── rag_service.py
│   │       ├── analyzer/        # Language analyzers
│   │       └── llm/             # LLM providers
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js pages
│   │   ├── components/          # React components
│   │   ├── lib/                 # Utilities
│   │   └── hooks/               # Custom hooks
│   └── public/
├── docker-compose.yml
├── CLAUDE.md                    # AI assistant instructions
└── README.md                    # This file
```

## Data Models

### Project
```
id: UUID
name: string
description: string
git_url: string
branch: string
status: pending | analyzing | ready | failed
created_at: datetime
updated_at: datetime
```

### Analysis
```
id: UUID
project_id: FK → Project
status: queued | running | completed | failed
started_at: datetime
completed_at: datetime
stats: JSON (files analyzed, LOC, etc.)
```

### Report
```
id: UUID
project_id: FK → Project
type: summary | architecture | developer | dependency
content: Markdown
created_at: datetime
```

### Diagram
```
id: UUID
project_id: FK → Project
type: architecture | dependency | class | sequence | erd
mermaid_code: text
metadata: JSON
```

### CodeChunk (Vector DB)
```
id: UUID
project_id: FK
file_path: string
chunk_type: file | function | class | block
content: text
start_line: int
end_line: int
language: string
embedding: vector[384]
```

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific tests
pytest tests/unit/
pytest tests/integration/
pytest -m "not slow"
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm test -- --coverage

# Watch mode
npm test -- --watch
```

## User Flows

### Analyzing a New Repository

1. User enters git URL or local path
2. System clones repository
3. Analysis runs in background (progress shown)
4. Reports and diagrams generated
5. Code indexed into vector database
6. User can view results and start chatting

### Asking Questions

1. User types natural language question
2. System generates embedding
3. System searches Qdrant for relevant code
4. LLM generates answer with context
5. Response includes source file links

## Configuration

### LLM Providers

CodeCompass supports multiple LLM backends:

| Provider | Configuration |
|----------|---------------|
| **Ollama** | `OLLAMA_BASE_URL`, `OLLAMA_MODEL` |
| **LM Studio** | Same OpenAI-compatible API |
| **OpenAI** | `OPENAI_API_KEY` (future) |
| **Claude** | `ANTHROPIC_API_KEY` (future) |

### Supported Languages

Tree-sitter analyzers support 30+ languages including:
- Python, JavaScript, TypeScript
- Go, Rust, Java, C/C++
- Ruby, PHP, C#
- And many more

## Performance Targets

| Metric | Target |
|--------|--------|
| Repository cloning | < 2 min for repos < 500MB |
| Analysis | < 5 min for repos < 10k files |
| Search response | < 2 seconds |
| Chat response | 5-30 seconds (depends on LLM) |

## Contributing

1. Create a feature branch from `main`
2. Make your changes with tests
3. Ensure all tests pass
4. Create a pull request
5. Use squash merge

See `CLAUDE.md` for detailed coding standards.

## License

[License details here]

## Roadmap

### Completed
- [x] Project setup with Docker Compose
- [x] FastAPI backend with project CRUD
- [x] SQLite database with SQLAlchemy
- [x] Git cloning service
- [x] Tree-sitter code analysis (30+ languages)
- [x] Next.js frontend with dashboard
- [x] LLM provider abstraction (Ollama)
- [x] Qdrant vector search integration
- [x] RAG-powered chat with streaming
- [x] Report and diagram generation

### In Progress
- [ ] Additional diagram types
- [ ] Incremental re-analysis
- [ ] Export functionality (PDF/HTML)

### Planned
- [ ] Cloud LLM providers (OpenAI, Claude)
- [ ] Multi-user support
- [ ] Custom analysis rules
