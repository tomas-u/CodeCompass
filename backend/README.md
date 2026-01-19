# CodeCompass Backend API

FastAPI backend for CodeCompass code analysis platform.

## Features

- **Projects API**: Create and manage code analysis projects
- **Analysis API**: Trigger and monitor code analysis jobs
- **Reports API**: Access generated architecture and dependency reports
- **Diagrams API**: Get Mermaid diagrams for visualization
- **Files API**: Browse file tree and view file contents
- **Search API**: Semantic code search
- **Chat API**: AI-powered Q&A about the codebase
- **Settings API**: Configure LLM providers and models

## Setup

### Prerequisites

- Python 3.11+
- pip

### Installation

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create environment file:
```bash
cp .env.example .env
```

### Running the Server

Development mode with auto-reload:
```bash
uvicorn app.main:app --reload
```

Production mode:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## API Endpoints

### Health & Info
- `GET /` - API information
- `GET /health` - Health check

### Projects
- `POST /api/projects` - Create project
- `GET /api/projects` - List projects
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

### Analysis
- `POST /api/projects/{id}/analyze` - Start analysis
- `GET /api/projects/{id}/analysis` - Get analysis status
- `DELETE /api/projects/{id}/analysis` - Cancel analysis

### Reports
- `GET /api/projects/{id}/reports` - List reports
- `GET /api/projects/{id}/reports/{type}` - Get specific report

### Diagrams
- `GET /api/projects/{id}/diagrams` - List diagrams
- `GET /api/projects/{id}/diagrams/{type}` - Get diagram
- `GET /api/projects/{id}/diagrams/{type}/svg` - Get SVG export

### Files
- `GET /api/projects/{id}/files` - Get file tree
- `GET /api/projects/{id}/files/{path}` - Get file content

### Search
- `POST /api/projects/{id}/search` - Search code

### Chat
- `POST /api/projects/{id}/chat` - Send chat message (supports streaming via SSE)
- `GET /api/projects/{id}/chat/sessions` - List chat sessions
- `GET /api/projects/{id}/chat/sessions/{id}` - Get session history
- `DELETE /api/projects/{id}/chat/sessions/{id}` - Delete session

**Streaming Chat:**
The chat endpoint supports Server-Sent Events (SSE) for real-time token streaming:
```bash
curl -N -X POST http://localhost:8000/api/projects/{id}/chat \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message": "How does auth work?", "stream": true}'
```

### Settings
- `GET /api/settings` - Get settings
- `PUT /api/settings` - Update settings
- `GET /api/settings/providers` - List LLM providers
- `POST /api/settings/test` - Test LLM connection

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── database.py          # SQLAlchemy database setup
│   ├── api/
│   │   └── routes/          # API route handlers
│   │       ├── projects.py
│   │       ├── analysis.py
│   │       ├── reports.py
│   │       ├── diagrams.py
│   │       ├── files.py
│   │       ├── search.py
│   │       ├── chat.py
│   │       └── settings_routes.py
│   ├── models/              # SQLAlchemy models
│   │   └── project.py
│   ├── schemas/             # Pydantic models
│   │   ├── project.py
│   │   ├── analysis.py
│   │   ├── report.py
│   │   ├── diagram.py
│   │   ├── chat.py
│   │   ├── search.py
│   │   ├── files.py
│   │   ├── settings.py
│   │   └── code_chunk.py    # Vector embeddings schema
│   └── services/            # Business logic
│       ├── git_service.py       # Git operations
│       ├── analysis_service.py  # Code analysis orchestration
│       ├── chunking_service.py  # Code chunking for embeddings
│       ├── vector_service.py    # Qdrant vector operations
│       ├── rag_service.py       # RAG pipeline for chat
│       ├── analyzer/            # Language analyzers
│       │   ├── generic_analyzer.py
│       │   └── ...
│       └── llm/                 # LLM provider abstraction
│           ├── base.py              # Abstract LLM provider
│           ├── factory.py           # Provider factory
│           ├── ollama_provider.py   # Ollama integration
│           └── embedding_provider.py # Embedding generation
├── tests/                   # Test suite
│   ├── conftest.py          # Global fixtures
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── requirements.txt
├── .env.example
└── README.md
```

## Development

### Running Tests

The project uses pytest for comprehensive test coverage.

**Run all tests:**
```bash
pytest
```

**Run with coverage:**
```bash
pytest --cov=app --cov-report=html --cov-report=term
```

**Run specific test file:**
```bash
pytest tests/unit/test_git_service.py
```

**Run specific test category:**
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Skip slow tests
pytest -m "not slow"
```

**Run with verbose output:**
```bash
pytest -v
```

**Run tests in parallel (after installing pytest-xdist):**
```bash
pytest -n auto
```

**View HTML coverage report:**
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

**Test Structure:**
```
tests/
├── conftest.py              # Global fixtures
├── pytest.ini               # Pytest configuration
├── unit/                    # Unit tests
│   └── test_analyzers/      # Analyzer tests
├── integration/             # Integration tests
└── fixtures/                # Test data and fixtures
    └── sample_repos/        # Sample repositories for testing
```

### Code Style

This project follows PEP 8 style guidelines.

## Implementation Status

The backend has progressed beyond MVP with real implementations:

**Implemented Features:**
- ✅ SQLite database with SQLAlchemy ORM
- ✅ Git cloning and repository management
- ✅ Tree-sitter code analysis (Python, JavaScript, TypeScript, and 30+ languages)
- ✅ Real-time status polling with background tasks
- ✅ LLM integration via Ollama provider
- ✅ Embedding generation with sentence-transformers
- ✅ Vector search with Qdrant
- ✅ RAG-powered chat with streaming SSE responses
- ✅ Code chunking for semantic search

**Docker Compose Setup:**
```bash
# Start all services (backend, frontend, Qdrant, embedding service)
docker compose up -d

# Or run locally:
cd backend && uvicorn app.main:app --reload
```

**Environment Variables:**
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

## License

See main repository LICENSE file.
