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
- `POST /api/projects/{id}/chat` - Send chat message
- `GET /api/projects/{id}/chat/sessions` - List chat sessions
- `GET /api/projects/{id}/chat/sessions/{id}` - Get session history
- `DELETE /api/projects/{id}/chat/sessions/{id}` - Delete session

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
│   ├── mock_data.py         # Mock data for MVP
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
│   └── schemas/             # Pydantic models
│       ├── project.py
│       ├── analysis.py
│       ├── report.py
│       ├── diagram.py
│       ├── chat.py
│       ├── search.py
│       ├── files.py
│       └── settings.py
├── requirements.txt
├── .env.example
└── README.md
```

## Development

### Running Tests

```bash
pytest
```

### Code Style

This project follows PEP 8 style guidelines.

## MVP Status

This is an MVP implementation using mock data. The following features return static responses:
- All endpoints return pre-defined mock data
- No actual database integration (SQLite/Qdrant)
- No real code analysis or LLM integration
- No git cloning or file system operations

These will be implemented in future iterations according to the PRD.

## License

See main repository LICENSE file.
