# Claude Instructions for CodeCompass

## Quick Reference

| Aspect | Decision |
|--------|----------|
| **Backend** | FastAPI + Python 3.11+ + SQLAlchemy |
| **Frontend** | Next.js 14+ + Tailwind + TypeScript |
| **Database** | SQLite (metadata) + Qdrant (vectors) |
| **LLM** | Ollama (primary), supports cloud providers |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 |
| **Code Parsing** | Tree-sitter (30+ languages) |

## Key Commands

```bash
# Backend
cd backend && uvicorn app.main:app --reload

# Frontend
cd frontend && npm run dev

# Full stack
docker compose up

# Tests
cd backend && pytest
cd frontend && npm test
```

---

## Critical Workflows

### GitHub Issue Validation (REQUIRED)

When implementing any GitHub issue:

1. **Before starting:** `gh issue view <number>` - understand all acceptance criteria
2. **During:** Work through each criterion systematically
3. **After completion:** Validate all work against the issue:
   - `gh issue edit <number> --body` to check off completed items `[x]`
   - Add completion summary with metrics (coverage %, test counts)
4. **Always verify:** Every checkbox must be validated before closing

### Git Branching (REQUIRED)

Branch protection is enabled on `main`. All changes require pull requests.

```bash
# Start new work
git checkout main && git pull
git checkout -b feature/<issue-number>-<description>

# Examples
feature/56-function-extraction
feature/dependency-dashboard
fix/diagram-caching
```

**During development:**
- Commit frequently with clear messages
- Push regularly: `git push -u origin <branch-name>`

**When complete:**
- Ensure tests pass and build succeeds
- Create PR: `gh pr create --base main --head <branch-name>`
- Merge with squash: `gh pr merge --squash`

**Never:**
- Push directly to `main`
- Use `git push --force` on `main`
- Merge without a pull request

### E2E Testing with MCP Playwright

When using MCP Playwright tools:

1. **Never use xvfb** - Headless Chromium in WSL cannot render visuals
2. **Use YAML accessibility snapshots** - Call `browser_snapshot()` WITHOUT filename
3. **Validate via YAML structure** - The accessibility tree provides complete validation
4. **Screenshots will be blank in WSL** - This is expected behavior

---

## Code Quality Standards

### Python (Backend)

```python
# Imports: standard lib, third-party, local (with blank lines between)
import os
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
```

- Use type hints for all function signatures
- Use Pydantic models for request/response schemas
- Use dependency injection for database sessions
- Async functions for I/O-bound operations
- Handle errors with HTTPException and appropriate status codes

### TypeScript (Frontend)

```typescript
// Imports: react, third-party, local components, local utils
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
```

- Use TypeScript strict mode
- Define interfaces for API responses
- Use React Query for data fetching
- Use Zustand for global state
- Tailwind for styling (no inline styles)

### Error Handling

```python
# Backend: Use HTTPException with clear messages
from fastapi import HTTPException

if not project:
    raise HTTPException(status_code=404, detail="Project not found")
```

```typescript
// Frontend: Handle loading and error states
const { data, isLoading, error } = useQuery(['project', id], fetchProject);
if (isLoading) return <Skeleton />;
if (error) return <ErrorMessage error={error} />;
```

### Testing Requirements

**Backend (pytest):**
- Unit tests for services in `tests/unit/`
- Integration tests for API routes in `tests/integration/`
- Use fixtures from `conftest.py`
- Mock external services (Git, LLM, Qdrant)
- Target: 80%+ coverage

**Frontend (Jest + RTL):**
- Component tests with React Testing Library
- Test user interactions, not implementation
- Mock API calls with MSW or jest mocks

```bash
# Run with coverage
cd backend && pytest --cov=app --cov-report=term
cd frontend && npm test -- --coverage
```

---

## Architecture Patterns

### Backend Service Layer

```
API Route → Service → Repository/External Service
     ↓          ↓              ↓
  Schemas    Business      Database/
  (Pydantic)   Logic       Qdrant/Git
```

- Routes handle HTTP concerns only
- Services contain business logic
- Use dependency injection for testability

### Key Services

| Service | Purpose |
|---------|---------|
| `git_service.py` | Clone repos, manage files |
| `analysis_service.py` | Orchestrate code analysis |
| `chunking_service.py` | Split code for embeddings |
| `vector_service.py` | Qdrant operations |
| `rag_service.py` | RAG pipeline for chat |
| `llm/` | LLM provider abstraction |

### Frontend Structure

```
src/app/           → Next.js App Router pages
src/components/ui/ → Reusable UI components (shadcn)
src/components/    → Feature-specific components
src/lib/api.ts     → API client
src/hooks/         → Custom React hooks
```

---

## Common Patterns

### Adding a New API Endpoint

1. Define Pydantic schemas in `backend/app/schemas/`
2. Create route in `backend/app/api/routes/`
3. Register route in `backend/app/main.py`
4. Add service logic in `backend/app/services/`
5. Write tests in `backend/tests/`

### Adding a New Frontend Page

1. Create page in `frontend/src/app/<route>/page.tsx`
2. Add API types in `frontend/src/lib/api.ts`
3. Create components in `frontend/src/components/`
4. Add React Query hooks if needed

### LLM Provider Pattern

All LLM interactions go through the provider abstraction:

```python
from app.services.llm.factory import get_llm_provider

provider = get_llm_provider()
response = await provider.generate(prompt)
```

---

## What NOT to Do

- Don't commit `.env` files or secrets
- Don't skip tests for "simple" changes
- Don't push directly to main
- Don't add features beyond what's requested
- Don't create documentation files unless asked
- Don't over-engineer - solve the current problem simply

---

## Documentation

For full project documentation, see:
- **README.md** - Project overview, setup, architecture
- **backend/README.md** - Backend API documentation
- **frontend/README.md** - Frontend documentation
