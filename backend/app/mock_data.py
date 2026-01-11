"""Mock data for MVP backend."""

from datetime import datetime, timedelta
from uuid import uuid4

# Mock projects
MOCK_PROJECTS = {
    "proj-1": {
        "id": "proj-1",
        "name": "fastapi-example",
        "description": "A production-ready FastAPI application with authentication",
        "source_type": "git_url",
        "source": "https://github.com/example/fastapi-example.git",
        "branch": "main",
        "local_path": "/app/repos/proj-1",
        "status": "ready",
        "settings": {
            "ignore_patterns": ["*.log", "node_modules", "__pycache__"],
            "analyze_languages": ["python", "javascript", "typescript"]
        },
        "stats": {
            "files": 150,
            "directories": 25,
            "lines_of_code": 25000,
            "languages": {
                "Python": {"files": 80, "lines": 15000},
                "JavaScript": {"files": 50, "lines": 8000},
                "TypeScript": {"files": 20, "lines": 2000}
            }
        },
        "created_at": (datetime.utcnow() - timedelta(days=5)).isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "last_analyzed_at": datetime.utcnow().isoformat()
    }
}

# Mock diagrams
MOCK_DIAGRAMS = {
    "architecture": """graph TB
    Client[Client Application]
    API[FastAPI Backend]
    Auth[Auth Service]
    DB[(PostgreSQL)]
    Cache[(Redis)]

    Client -->|HTTP/REST| API
    API --> Auth
    API --> DB
    API --> Cache
    Auth --> DB""",

    "dependency": """graph LR
    app[app] --> services[services]
    app --> models[models]
    services --> models
    services --> utils[utils]
    api[api] --> services
    api --> models""",

    "directory": """graph TD
    root[fastapi-example]
    root --> src[src/]
    root --> tests[tests/]
    root --> docs[docs/]
    src --> api[api/]
    src --> services[services/]
    src --> models[models/]
    src --> utils[utils/]"""
}

# Mock architecture report
MOCK_ARCHITECTURE_REPORT = """# Architecture Report: fastapi-example

## Overview

This is a **production-ready FastAPI application** with authentication, user management, and project features.

## Tech Stack

### Languages
- Python 3.11

### Frameworks
- **FastAPI** - Modern, fast web framework
- **SQLAlchemy** - SQL toolkit and ORM
- **Pydantic** - Data validation

### Databases
- **PostgreSQL** - Primary database
- **Redis** - Caching and sessions

## Architecture Pattern

**Layered Architecture (Clean Architecture)**

1. API Layer (`src/api/`)
2. Service Layer (`src/services/`)
3. Data Layer (`src/models/`)

## Entry Points

- `src/main.py` - Application entry point
- `src/api/routes/__init__.py` - API router aggregation

## Dependencies

### External Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.109.0 | Web framework |
| sqlalchemy | 2.0.25 | Database ORM |
| pydantic | 2.5.3 | Data validation |
"""

# Mock file tree
MOCK_FILE_TREE = {
    "name": "fastapi-example",
    "type": "directory",
    "children": [
        {
            "name": "src",
            "type": "directory",
            "children": [
                {
                    "name": "main.py",
                    "type": "file",
                    "language": "python",
                    "size_bytes": 2500,
                    "lines": 85
                },
                {
                    "name": "config.py",
                    "type": "file",
                    "language": "python",
                    "size_bytes": 1200,
                    "lines": 45
                },
                {
                    "name": "api",
                    "type": "directory",
                    "children": [
                        {
                            "name": "routes",
                            "type": "directory",
                            "children": [
                                {
                                    "name": "auth.py",
                                    "type": "file",
                                    "language": "python",
                                    "size_bytes": 3500,
                                    "lines": 120
                                },
                                {
                                    "name": "users.py",
                                    "type": "file",
                                    "language": "python",
                                    "size_bytes": 2800,
                                    "lines": 95
                                }
                            ]
                        }
                    ]
                },
                {
                    "name": "services",
                    "type": "directory",
                    "children": [
                        {
                            "name": "auth_service.py",
                            "type": "file",
                            "language": "python",
                            "size_bytes": 4200,
                            "lines": 145
                        }
                    ]
                },
                {
                    "name": "models",
                    "type": "directory",
                    "children": [
                        {
                            "name": "user.py",
                            "type": "file",
                            "language": "python",
                            "size_bytes": 1800,
                            "lines": 65
                        }
                    ]
                }
            ]
        },
        {
            "name": "tests",
            "type": "directory",
            "children": [
                {
                    "name": "test_auth.py",
                    "type": "file",
                    "language": "python",
                    "size_bytes": 2100,
                    "lines": 75
                }
            ]
        },
        {
            "name": "README.md",
            "type": "file",
            "language": "markdown",
            "size_bytes": 1200,
            "lines": 45
        },
        {
            "name": "requirements.txt",
            "type": "file",
            "language": "text",
            "size_bytes": 350,
            "lines": 15
        }
    ]
}

# Mock file content
MOCK_FILE_CONTENT = """\"\"\"FastAPI application entry point.\"\"\"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import api_router

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    \"\"\"Root endpoint.\"\"\"
    return {
        "name": settings.app_name,
        "version": settings.version,
        "docs_url": "/docs"
    }


@app.get("/health")
async def health():
    \"\"\"Health check endpoint.\"\"\"
    return {"status": "healthy"}
"""

# Mock chat sessions
MOCK_CHAT_SESSIONS = {
    "session-1": {
        "id": "session-1",
        "title": "Authentication Discussion",
        "messages": [
            {
                "id": "msg-1",
                "role": "user",
                "content": "How does authentication work in this codebase?",
                "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat()
            },
            {
                "id": "msg-2",
                "role": "assistant",
                "content": """The authentication flow in this codebase works as follows:

1. **Login Request**: User sends credentials to `/api/auth/login`
2. **Validation**: AuthService validates credentials against the database
3. **Token Generation**: JWT tokens are created using python-jose
4. **Response**: Access token is returned to the client

Here's the relevant code from `src/services/auth_service.py`:

```python
async def login(credentials: Credentials):
    user = await get_user_by_username(credentials.username)
    if not verify_password(credentials.password, user.hashed_password):
        raise InvalidCredentialsError()

    token = create_access_token(user.id)
    return {"access_token": token}
```""",
                "sources": [
                    {
                        "file_path": "src/services/auth_service.py",
                        "start_line": 15,
                        "end_line": 45,
                        "snippet": "async def login(credentials: Credentials)...",
                        "relevance_score": 0.95
                    }
                ],
                "created_at": (datetime.utcnow() - timedelta(hours=2, minutes=1)).isoformat()
            }
        ],
        "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat()
    }
}

# Mock search results
MOCK_SEARCH_RESULTS = [
    {
        "score": 0.92,
        "file_path": "src/services/auth_service.py",
        "chunk_type": "class",
        "name": "AuthService",
        "start_line": 15,
        "end_line": 85,
        "content": """class AuthService:
    \"\"\"Authentication service.\"\"\"

    async def login(self, credentials: Credentials):
        \"\"\"Authenticate user and return token.\"\"\"
        user = await self.get_user_by_username(credentials.username)
        if not self.verify_password(credentials.password, user.hashed_password):
            raise InvalidCredentialsError()

        token = self.create_access_token(user.id)
        return {"access_token": token}""",
        "language": "python",
        "context": {
            "module": "services",
            "imports": ["models.User", "utils.jwt"]
        }
    },
    {
        "score": 0.85,
        "file_path": "src/api/routes/auth.py",
        "chunk_type": "function",
        "name": "login",
        "start_line": 25,
        "end_line": 45,
        "content": """@router.post("/login")
async def login(credentials: Credentials):
    \"\"\"Login endpoint.\"\"\"
    result = await auth_service.login(credentials)
    return result""",
        "language": "python",
        "context": {
            "module": "api.routes",
            "imports": ["services.AuthService"]
        }
    }
]


def get_mock_project(project_id: str = "proj-1"):
    """Get mock project by ID."""
    return MOCK_PROJECTS.get(project_id)


def get_all_mock_projects():
    """Get all mock projects."""
    return list(MOCK_PROJECTS.values())
