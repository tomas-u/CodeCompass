import { Project, ChatMessage } from './store';

export const mockProjects: Project[] = [
  {
    id: '1',
    name: 'fastapi-example',
    sourceType: 'git_url',
    source: 'https://github.com/tiangolo/fastapi',
    branch: 'main',
    status: 'ready',
    stats: {
      files: 245,
      linesOfCode: 48500,
      languages: ['Python', 'Markdown', 'YAML']
    },
    createdAt: '2026-01-08T10:00:00Z',
    lastAnalyzedAt: '2026-01-10T14:30:00Z'
  },
  {
    id: '2',
    name: 'react-app',
    sourceType: 'local_path',
    source: '/home/user/projects/react-app',
    branch: 'develop',
    status: 'ready',
    stats: {
      files: 89,
      linesOfCode: 12300,
      languages: ['TypeScript', 'JavaScript', 'CSS']
    },
    createdAt: '2026-01-09T15:00:00Z',
    lastAnalyzedAt: '2026-01-10T09:00:00Z'
  }
];

export const mockChatMessages: ChatMessage[] = [
  {
    id: '1',
    role: 'user',
    content: 'How does authentication work in this codebase?',
    createdAt: '2026-01-10T14:00:00Z'
  },
  {
    id: '2',
    role: 'assistant',
    content: `Authentication in this codebase is handled by the \`AuthService\` class in \`src/services/auth.py\`. Here's how it works:

1. **JWT Token Generation**: When a user logs in, the \`create_access_token()\` function generates a JWT token.

2. **Token Validation**: The \`get_current_user()\` dependency validates tokens on protected routes.

3. **Password Hashing**: Passwords are hashed using bcrypt via the \`get_password_hash()\` function.

\`\`\`python
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials"
    )
    # Token validation logic here
\`\`\`

The main authentication flow is:
1. User submits credentials to \`/api/auth/login\`
2. Server validates and returns JWT + refresh token
3. Client includes JWT in Authorization header
4. Protected routes use \`Depends(get_current_user)\``,
    sources: [
      {
        filePath: 'src/services/auth.py',
        startLine: 15,
        endLine: 45,
        snippet: 'class AuthService:\n    def create_access_token(self, data: dict):\n        ...'
      },
      {
        filePath: 'src/api/deps.py',
        startLine: 20,
        endLine: 35,
        snippet: 'async def get_current_user(token: str = Depends(oauth2_scheme)):\n    ...'
      }
    ],
    createdAt: '2026-01-10T14:00:05Z'
  },
  {
    id: '3',
    role: 'user',
    content: 'Where are the API routes defined?',
    createdAt: '2026-01-10T14:01:00Z'
  },
  {
    id: '4',
    role: 'assistant',
    content: `API routes are organized in the \`src/api/routes/\` directory. Here's the structure:

\`\`\`
src/api/routes/
├── __init__.py      # Router aggregation
├── auth.py          # Authentication endpoints
├── users.py         # User management
├── projects.py      # Project CRUD
└── health.py        # Health check
\`\`\`

All routers are imported and included in \`src/api/routes/__init__.py\`:

\`\`\`python
from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
\`\`\`

The main app includes this in \`src/main.py\`:
\`\`\`python
app.include_router(api_router, prefix="/api")
\`\`\``,
    sources: [
      {
        filePath: 'src/api/routes/__init__.py',
        startLine: 1,
        endLine: 20,
        snippet: 'from fastapi import APIRouter\n...'
      }
    ],
    createdAt: '2026-01-10T14:01:05Z'
  }
];

export const mockFileTree = {
  name: 'fastapi-example',
  type: 'directory' as const,
  children: [
    {
      name: 'src',
      type: 'directory' as const,
      children: [
        {
          name: 'api',
          type: 'directory' as const,
          children: [
            {
              name: 'routes',
              type: 'directory' as const,
              children: [
                { name: '__init__.py', type: 'file' as const, language: 'python', lines: 25 },
                { name: 'auth.py', type: 'file' as const, language: 'python', lines: 85 },
                { name: 'users.py', type: 'file' as const, language: 'python', lines: 120 },
                { name: 'projects.py', type: 'file' as const, language: 'python', lines: 150 },
              ]
            },
            { name: 'deps.py', type: 'file' as const, language: 'python', lines: 45 },
          ]
        },
        {
          name: 'services',
          type: 'directory' as const,
          children: [
            { name: 'auth.py', type: 'file' as const, language: 'python', lines: 95 },
            { name: 'user_service.py', type: 'file' as const, language: 'python', lines: 110 },
          ]
        },
        {
          name: 'models',
          type: 'directory' as const,
          children: [
            { name: '__init__.py', type: 'file' as const, language: 'python', lines: 5 },
            { name: 'user.py', type: 'file' as const, language: 'python', lines: 45 },
            { name: 'project.py', type: 'file' as const, language: 'python', lines: 60 },
          ]
        },
        { name: 'main.py', type: 'file' as const, language: 'python', lines: 55 },
        { name: 'config.py', type: 'file' as const, language: 'python', lines: 40 },
      ]
    },
    {
      name: 'tests',
      type: 'directory' as const,
      children: [
        { name: 'test_auth.py', type: 'file' as const, language: 'python', lines: 80 },
        { name: 'test_users.py', type: 'file' as const, language: 'python', lines: 95 },
      ]
    },
    { name: 'README.md', type: 'file' as const, language: 'markdown', lines: 120 },
    { name: 'requirements.txt', type: 'file' as const, language: 'text', lines: 25 },
    { name: 'Dockerfile', type: 'file' as const, language: 'dockerfile', lines: 30 },
    { name: '.gitignore', type: 'file' as const, language: 'text', lines: 15 },
  ]
};

export const mockArchitectureReport = {
  overview: {
    name: 'fastapi-example',
    description: 'A production-ready FastAPI application with authentication, user management, and project features.',
    stats: {
      files: 245,
      directories: 32,
      linesOfCode: 48500,
      languages: {
        Python: { files: 180, lines: 42000 },
        Markdown: { files: 15, lines: 3500 },
        YAML: { files: 10, lines: 800 },
        Dockerfile: { files: 2, lines: 60 }
      }
    }
  },
  techStack: {
    languages: ['Python 3.11'],
    frameworks: ['FastAPI', 'SQLAlchemy', 'Pydantic'],
    databases: ['PostgreSQL', 'Redis'],
    tools: ['Docker', 'pytest', 'black', 'mypy']
  },
  architecturePattern: 'Layered Architecture (Clean Architecture)',
  entryPoints: [
    { file: 'src/main.py', description: 'FastAPI application entry point' },
    { file: 'src/api/routes/__init__.py', description: 'API router aggregation' }
  ],
  keyFiles: [
    { file: 'src/main.py', description: 'Application initialization and middleware setup' },
    { file: 'src/config.py', description: 'Configuration management using Pydantic Settings' },
    { file: 'src/api/deps.py', description: 'Dependency injection for routes' },
    { file: 'src/services/auth.py', description: 'Authentication service with JWT handling' }
  ],
  dependencies: {
    external: [
      { name: 'fastapi', version: '0.109.0' },
      { name: 'sqlalchemy', version: '2.0.25' },
      { name: 'pydantic', version: '2.5.3' },
      { name: 'python-jose', version: '3.3.0' },
      { name: 'passlib', version: '1.7.4' },
      { name: 'redis', version: '5.0.1' }
    ],
    internal: [
      { module: 'api', dependsOn: ['services', 'models'] },
      { module: 'services', dependsOn: ['models'] },
      { module: 'models', dependsOn: [] }
    ]
  }
};

export const mockDiagrams = {
  architecture: `graph TB
    subgraph Client
        UI[Web UI / Mobile App]
    end

    subgraph API Layer
        MAIN[main.py<br/>FastAPI App]
        AUTH[auth.py<br/>Auth Routes]
        USERS[users.py<br/>User Routes]
        PROJ[projects.py<br/>Project Routes]
    end

    subgraph Service Layer
        AUTH_SVC[AuthService]
        USER_SVC[UserService]
        PROJ_SVC[ProjectService]
    end

    subgraph Data Layer
        MODELS[SQLAlchemy Models]
        DB[(PostgreSQL)]
        CACHE[(Redis)]
    end

    UI --> MAIN
    MAIN --> AUTH
    MAIN --> USERS
    MAIN --> PROJ
    AUTH --> AUTH_SVC
    USERS --> USER_SVC
    PROJ --> PROJ_SVC
    AUTH_SVC --> MODELS
    USER_SVC --> MODELS
    PROJ_SVC --> MODELS
    MODELS --> DB
    AUTH_SVC --> CACHE`,

  dependency: `graph LR
    subgraph api
        routes[routes/]
        deps[deps.py]
    end

    subgraph services
        auth[auth.py]
        user[user_service.py]
    end

    subgraph models
        user_model[user.py]
        project_model[project.py]
    end

    routes --> deps
    routes --> auth
    routes --> user
    deps --> auth
    auth --> user_model
    user --> user_model
    user --> project_model`,

  directory: `graph TD
    ROOT[fastapi-example/]
    SRC[src/]
    API[api/]
    ROUTES[routes/]
    SERVICES[services/]
    MODELS[models/]
    TESTS[tests/]

    ROOT --> SRC
    ROOT --> TESTS
    ROOT --> README[README.md]
    ROOT --> REQ[requirements.txt]
    ROOT --> DOCKER[Dockerfile]

    SRC --> API
    SRC --> SERVICES
    SRC --> MODELS
    SRC --> MAIN[main.py]
    SRC --> CONFIG[config.py]

    API --> ROUTES
    API --> DEPS[deps.py]

    ROUTES --> INIT[__init__.py]
    ROUTES --> AUTH_R[auth.py]
    ROUTES --> USER_R[users.py]`
};

export const mockFileContent = `"""
Authentication Service Module

This module handles all authentication-related operations including
JWT token generation, validation, and password hashing.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.config import settings
from src.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")


class AuthService:
    """Service class for authentication operations."""

    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Generate a hash for the given password."""
        return pwd_context.hash(password)

    def create_access_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a new JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.access_token_expire_minutes
            )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm
        )
        return encoded_jwt

    async def get_current_user(
        self,
        token: str = Depends(oauth2_scheme)
    ) -> User:
        """Get the current authenticated user from JWT token."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        # Get user from database
        user = await self.get_user_by_username(username)
        if user is None:
            raise credentials_exception
        return user


auth_service = AuthService()
`;
