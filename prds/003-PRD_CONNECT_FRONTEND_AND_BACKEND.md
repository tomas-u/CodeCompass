# Frontend-Backend Integration - Product Requirements Document

## Document Info
| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Status** | Draft |
| **Author** | Product Manager |
| **Last Updated** | 2026-01-11 |
| **Related Documents** | 000-PRD_LANDING_PAGE.md, 001-PRD_BACKEND_API.md |

---

## 1. Executive Summary

This document outlines the strategy for integrating the CodeCompass frontend (Next.js) with the backend (FastAPI), replacing all mock data with real API calls. The integration must maintain the current user experience while adding proper loading states, error handling, and real-time updates.

### Current State
- **Frontend**: Fully functional UI with Zustand state management and mock data
- **Backend**: Complete API with 40+ endpoints returning mock data
- **Gap**: No connection between the two - both systems operate independently

### Goal
Create a seamless integration where:
1. Frontend fetches real data from backend API
2. User actions trigger backend operations
3. Loading and error states provide clear feedback
4. System gracefully handles failures
5. Development workflow remains smooth

---

## 2. Current State Analysis

### 2.1 Frontend Mock Data Locations

| Component | Mock Data Source | API Endpoint Needed |
|-----------|------------------|---------------------|
| **Header.tsx** | `mockProjects` from store | `GET /api/projects` |
| **WelcomePage.tsx** | Creates projects in store only | `POST /api/projects` |
| **AnalysisProgress.tsx** | Simulated progress in store | `GET /api/projects/{id}/analysis` |
| **OverviewTab.tsx** | `mockArchitectureReport` | `GET /api/projects/{id}` |
| **DiagramsTab.tsx** | `mockDiagrams` | `GET /api/projects/{id}/diagrams/{type}` |
| **FilesTab.tsx** | `mockFileTree`, `mockFileContent` | `GET /api/projects/{id}/files` |
| **ReportsTab.tsx** | Hardcoded markdown strings | `GET /api/projects/{id}/reports/{type}` |
| **ChatPanel.tsx** | `mockChatMessages`, simulated responses | `POST /api/projects/{id}/chat` |

### 2.2 Backend Mock Data

All endpoints in `app/api/routes/*` return data from:
- `app/mock_data.py` - Contains `MOCK_PROJECTS`, `MOCK_DIAGRAMS`, etc.
- Hardcoded responses in route handlers

### 2.3 Key Observations

**Strengths:**
- Both systems have matching data structures
- Pydantic schemas ensure type safety on backend
- Frontend state management is already centralized in Zustand

**Challenges:**
- No API client infrastructure in frontend
- No loading/error state handling
- No TypeScript types matching backend schemas
- Backend returns ISO datetime strings, frontend expects Date objects
- Analysis progress is simulated, needs polling mechanism
- Chat responses are instant, need streaming support (future)

---

## 3. Integration Architecture

### 3.1 High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                        │
│                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │  Components  │─────→│ API Client   │─────→│  Zustand  │ │
│  │              │      │ (lib/api.ts) │      │   Store   │ │
│  │ - Display    │      │              │      │           │ │
│  │ - User Input │←─────│ - Fetch      │←─────│ - State   │ │
│  └──────────────┘      │ - Error      │      │ - Actions │ │
│                        │ - Transform  │      └───────────┘ │
│                        └──────────────┘                     │
└─────────────────────────────────────────────────────────────┘
                              │ HTTP/REST
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                          │
│                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │   Routes     │─────→│   Services   │─────→│   Mock    │ │
│  │              │      │              │      │   Data    │ │
│  │ - Validate   │      │ - Business   │      │           │ │
│  │ - Response   │←─────│   Logic      │←─────│ - Static  │ │
│  └──────────────┘      └──────────────┘      └───────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 API Client Layer

**Location:** `frontend/src/lib/api.ts`

**Responsibilities:**
1. **HTTP Communication**
   - Configure base URL (env variable)
   - Set headers (Content-Type, etc.)
   - Handle CORS

2. **Request Transformation**
   - Convert frontend models to API format
   - Add authentication headers (future)

3. **Response Transformation**
   - Parse JSON responses
   - Convert ISO strings to Date objects
   - Handle pagination metadata

4. **Error Handling**
   - Network errors (timeout, connection refused)
   - HTTP errors (4xx, 5xx)
   - Parse backend error format
   - Retry logic for transient failures

5. **Type Safety**
   - TypeScript interfaces matching backend Pydantic schemas
   - Request/response typing

### 3.3 State Management Strategy

**Current:** Zustand store with mock data and sync actions

**New:** Zustand store with async actions that call API

```typescript
// Current (mock)
addProject: (project) => set((state) => ({
  projects: [...state.projects, project]
}))

// New (API-backed)
addProject: async (projectData) => {
  try {
    const project = await api.createProject(projectData)
    set((state) => ({ projects: [...state.projects, project] }))
    return project
  } catch (error) {
    // Handle error
    throw error
  }
}
```

**Benefits:**
- Centralized API logic
- Components don't know about API details
- Easy to add caching, optimistic updates later

---

## 4. Technical Implementation Details

### 4.1 API Client Configuration

```typescript
// frontend/src/lib/api-config.ts
export const API_CONFIG = {
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
}
```

### 4.2 HTTP Client Choice

**Options:**

| Library | Pros | Cons | Recommendation |
|---------|------|------|----------------|
| **fetch (native)** | No dependencies, built-in, modern | Verbose error handling, no interceptors | ✅ **Use for MVP** |
| **axios** | Interceptors, auto JSON parsing, great error handling | 14kb bundle size, extra dependency | 🔶 Consider for Phase 2 |
| **ky** | Lightweight (4kb), modern API, retry built-in | Less ecosystem support | ❌ Not needed yet |

**Decision:** Start with **fetch** wrapped in helper functions, migrate to axios if complexity grows.

### 4.3 Type Definitions

**Strategy:** Manually create TypeScript types matching backend Pydantic schemas

```typescript
// frontend/src/types/api.ts

// Match backend schemas/project.py
export interface Project {
  id: string
  name: string
  description?: string
  source_type: 'git_url' | 'local_path'
  source: string
  branch: string
  status: 'pending' | 'cloning' | 'scanning' | 'analyzing' | 'ready' | 'failed'
  stats?: ProjectStats
  created_at: string // ISO datetime string
  updated_at: string
  last_analyzed_at?: string
}

export interface ProjectStats {
  files: number
  directories: number
  lines_of_code: number
  languages: Record<string, LanguageStats>
}

// ... more types
```

**Future Enhancement:** Auto-generate types from OpenAPI spec using tools like:
- `openapi-typescript`
- `swagger-typescript-api`

### 4.4 Error Handling Strategy

**Backend Error Format** (from PRD):
```json
{
  "error": {
    "code": "PROJECT_NOT_FOUND",
    "message": "Project with ID 'xyz' not found",
    "details": { "project_id": "xyz" }
  },
  "request_id": "uuid-string",
  "timestamp": "2026-01-10T12:00:00Z"
}
```

**Frontend Error Class:**
```typescript
export class ApiError extends Error {
  code: string
  details?: any
  statusCode: number

  constructor(response: ErrorResponse, statusCode: number) {
    super(response.error.message)
    this.code = response.error.code
    this.details = response.error.details
    this.statusCode = statusCode
  }
}
```

**Error Display Strategy:**

| Error Type | User Feedback | Action |
|------------|---------------|--------|
| Network Error | Toast: "Unable to connect. Check your connection." | Retry button |
| 404 Not Found | Inline: "Project not found" | Back to list |
| 400 Validation | Form errors on specific fields | Highlight fields |
| 500 Server Error | Toast: "Something went wrong. Try again." | Retry button |
| Timeout | Toast: "Request timed out" | Retry button |

### 4.5 Loading States

**Component-Level Loading:**
```typescript
const [isLoading, setIsLoading] = useState(false)
const [error, setError] = useState<Error | null>(null)

// In component
if (isLoading) return <LoadingSkeleton />
if (error) return <ErrorMessage error={error} />
```

**Global Loading (for page transitions):**
- Use Next.js `loading.tsx` files
- Skeleton screens for each view

**Granular Loading (for specific actions):**
```typescript
const [loadingStates, setLoadingStates] = useState({
  projects: false,
  analysis: false,
  reports: false,
})
```

### 4.6 Real-Time Updates

**Analysis Progress Polling:**

```typescript
// Poll every 2 seconds while analysis is running
useEffect(() => {
  if (!analysisInProgress) return

  const interval = setInterval(async () => {
    const status = await api.getAnalysisStatus(projectId)
    updateAnalysisProgress(status)

    if (status.status === 'completed' || status.status === 'failed') {
      clearInterval(interval)
    }
  }, 2000)

  return () => clearInterval(interval)
}, [analysisInProgress, projectId])
```

**Alternative (Future):** WebSocket for real-time push updates

---

## 5. Implementation Phases

### Phase 1: Foundation (Day 1)
**Goal:** Establish basic connectivity

- [ ] Create API client infrastructure (`lib/api.ts`)
- [ ] Add environment variable for API URL
- [ ] Implement health check endpoint call
- [ ] Create TypeScript types for core models (Project, Analysis)
- [ ] Add error handling utilities
- [ ] Create loading state components (Skeleton, ErrorMessage)

**Success Criteria:**
- Health check displays backend status on frontend
- Error states render correctly
- Loading skeletons show during fetch

---

### Phase 2: Projects (Day 2)
**Goal:** Replace project management with API

- [ ] `GET /api/projects` - List projects
- [ ] `POST /api/projects` - Create project from Welcome page
- [ ] `GET /api/projects/{id}` - Get project details for Overview tab
- [ ] `PUT /api/projects/{id}` - Update project settings
- [ ] `DELETE /api/projects/{id}` - Delete project

**Zustand Actions to Implement:**
```typescript
// Before: mockProjects array
// After: API-backed
fetchProjects: async () => { ... }
createProject: async (data) => { ... }
updateProject: async (id, data) => { ... }
deleteProject: async (id) => { ... }
```

**UI Updates:**
- Welcome page submits to backend
- Header dropdown loads from API
- Projects list reflects server state
- Delete confirmation actually deletes from backend

**Success Criteria:**
- Creating project triggers API call and updates UI
- Project list loads from backend on refresh
- Deleting project removes from backend

---

### Phase 3: Analysis Flow (Day 3)
**Goal:** Real analysis triggering and progress monitoring

- [ ] `POST /api/projects/{id}/analyze` - Start analysis
- [ ] `GET /api/projects/{id}/analysis` - Poll for progress
- [ ] `DELETE /api/projects/{id}/analysis` - Cancel analysis

**New Functionality:**
- Analysis starts when project created
- Progress bar shows real backend progress
- Current step updates from backend
- Auto-refresh every 2 seconds during analysis
- Stop polling when complete/failed

**UI Updates:**
- AnalysisProgress shows real data from backend
- Progress simulation removed
- File count, current file from backend
- Error handling for failed analysis

**Success Criteria:**
- Creating project triggers backend analysis
- Progress updates reflect backend state
- Analysis completion shows ready dashboard

---

### Phase 4: Reports & Diagrams (Day 4)
**Goal:** Display real generated reports and diagrams

- [ ] `GET /api/projects/{id}/reports` - List reports
- [ ] `GET /api/projects/{id}/reports/{type}` - Get report content
- [ ] `GET /api/projects/{id}/diagrams` - List diagrams
- [ ] `GET /api/projects/{id}/diagrams/{type}` - Get diagram code

**UI Updates:**
- ReportsTab loads from API
- DiagramsTab renders backend Mermaid code
- Copy/download uses backend data

**Success Criteria:**
- Reports tab shows backend-generated content
- Diagrams render from backend Mermaid code
- Download exports backend data

---

### Phase 5: Files & Search (Day 5)
**Goal:** Real file browsing and search

- [ ] `GET /api/projects/{id}/files` - Get file tree
- [ ] `GET /api/projects/{id}/files/{path}` - Get file content
- [ ] `POST /api/projects/{id}/search` - Search code

**UI Updates:**
- FilesTab loads real file tree from backend
- Clicking file loads actual content from backend
- Search queries backend and displays results

**Success Criteria:**
- File tree reflects actual project structure
- File content loads from backend
- Search returns relevant results

---

### Phase 6: Chat (Day 6)
**Goal:** Real AI chat interaction

- [ ] `POST /api/projects/{id}/chat` - Send message
- [ ] `GET /api/projects/{id}/chat/sessions` - List sessions
- [ ] `GET /api/projects/{id}/chat/sessions/{id}` - Load history
- [ ] `DELETE /api/projects/{id}/chat/sessions/{id}` - Delete session

**UI Updates:**
- Chat sends to backend
- Response displays from backend
- Sources show real file references
- Session persistence

**Success Criteria:**
- Chat messages sent to backend
- AI responses displayed
- Session history persisted
- Sources clickable

---

## 6. Data Transformation Challenges

### 6.1 Date Handling

**Backend:** Returns ISO 8601 strings
```json
{
  "created_at": "2026-01-11T14:30:00Z"
}
```

**Frontend:** Needs Date objects for formatting

**Solution:**
```typescript
function parseApiResponse<T>(data: any): T {
  // Recursively convert ISO strings to Date objects
  const dateFields = ['created_at', 'updated_at', 'last_analyzed_at']

  Object.keys(data).forEach(key => {
    if (dateFields.includes(key) && typeof data[key] === 'string') {
      data[key] = new Date(data[key])
    }
  })

  return data as T
}
```

### 6.2 Enum Consistency

**Backend Pydantic:**
```python
class ProjectStatus(str, Enum):
    pending = "pending"
    ready = "ready"
```

**Frontend TypeScript:**
```typescript
type ProjectStatus = 'pending' | 'ready' // String literal union
```

**Challenge:** Keep in sync manually or generate from backend

### 6.3 Nested Objects

**Backend:** Returns nested stats
```json
{
  "stats": {
    "languages": {
      "Python": {"files": 80, "lines": 15000}
    }
  }
}
```

**Frontend:** Needs proper typing
```typescript
interface ProjectStats {
  languages: Record<string, LanguageStats>
}
```

**Solution:** Careful type definitions matching backend schemas

---

## 7. User Experience Considerations

### 7.1 Loading States

| View | Loading State | Duration |
|------|---------------|----------|
| Project List | Skeleton cards | < 500ms |
| Dashboard | Full-page skeleton | < 1s |
| File Content | Spinner in content area | < 300ms |
| Chat Response | Typing indicator | 2-5s |
| Analysis Progress | Progress bar (always visible) | 1-5 min |

**Design Principles:**
- Show skeleton for > 200ms loads
- Instant feedback for user actions
- Preserve scroll position during updates
- Optimistic UI for mutations (future)

### 7.2 Error Recovery

**Strategies:**

1. **Automatic Retry** (transient errors)
   - Network timeout: Retry 3 times with exponential backoff
   - 502/503 errors: Retry 2 times

2. **User-Triggered Retry** (persistent errors)
   - Show error message with "Retry" button
   - Log error details for debugging

3. **Graceful Degradation**
   - If reports fail to load, show "Reports unavailable"
   - Allow other tabs to work

4. **Error Boundaries**
   - Catch React errors in ErrorBoundary
   - Show fallback UI
   - Report to console (future: error tracking service)

### 7.3 Offline Handling

**Phase 1 (MVP):**
- Show clear error: "Unable to connect to server"
- Disable actions that require connection
- Don't cache data

**Future:**
- Service worker for offline support
- IndexedDB for local caching
- Sync when reconnected

### 7.4 Performance Optimization

**Strategies:**

1. **Debouncing** - Search queries wait 300ms after typing stops
2. **Caching** - Store project list in Zustand, refetch on demand
3. **Pagination** - Load 20 projects at a time
4. **Lazy Loading** - Load reports/diagrams only when tab opened
5. **Code Splitting** - Next.js automatic route-based splitting

---

## 8. Environment Configuration

### 8.1 Environment Variables

**Frontend (.env.local):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_TIMEOUT=30000
```

**Backend (.env):**
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

### 8.2 Development Workflow

**Option 1: Two Terminal Windows**
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

**Option 2: Docker Compose (Recommended)**
```yaml
# docker-compose.yml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - CORS_ORIGINS=http://localhost:3000

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Command:** `docker-compose up`

---

## 9. Testing Strategy

### 9.1 Integration Testing

**Frontend Tests (Playwright/Cypress):**
```typescript
describe('Project Creation', () => {
  it('creates project and starts analysis', async () => {
    // Visit welcome page
    await page.goto('/')

    // Fill form
    await page.fill('[name="gitUrl"]', 'https://github.com/test/repo.git')

    // Submit
    await page.click('button[type="submit"]')

    // Verify API call was made
    const request = await page.waitForRequest(req =>
      req.url().includes('/api/projects') && req.method() === 'POST'
    )

    // Verify redirect to analysis
    await expect(page).toHaveURL(/.*analysis/)
  })
})
```

**Backend Tests (pytest):**
```python
def test_create_project(client):
    response = client.post("/api/projects", json={
        "name": "test-project",
        "source_type": "git_url",
        "source": "https://github.com/test/repo.git"
    })
    assert response.status_code == 201
    assert response.json()["name"] == "test-project"
```

### 9.2 Error Scenario Testing

| Scenario | Expected Behavior |
|----------|-------------------|
| Backend offline | Error toast: "Unable to connect" |
| 404 Project not found | Redirect to projects list |
| Network timeout | Retry automatically, then show error |
| Invalid form data | Show field-level validation errors |
| Session expired (future) | Redirect to login |

### 9.3 Manual Testing Checklist

**Before Each Phase:**
- [ ] Start backend, verify `/health` returns 200
- [ ] Start frontend, verify UI loads
- [ ] Open browser console, check for errors
- [ ] Test happy path for new features
- [ ] Test error scenarios (kill backend, invalid data)
- [ ] Verify loading states show correctly
- [ ] Check mobile responsiveness

---

## 10. Migration Strategy

### 10.1 Incremental Migration Approach

**Philosophy:** Replace one feature at a time, keep system always working

**Process:**
1. Create new API-backed Zustand action
2. Keep old mock action as fallback
3. Add feature flag to switch between mock/API
4. Test API version thoroughly
5. Remove mock version when confident

**Example:**
```typescript
const useAppStore = create<AppState>((set, get) => ({
  // Feature flag
  useApi: process.env.NEXT_PUBLIC_USE_API === 'true',

  // Projects
  fetchProjects: async () => {
    if (get().useApi) {
      // API version
      const projects = await api.getProjects()
      set({ projects })
    } else {
      // Mock version (fallback)
      set({ projects: mockProjects })
    }
  }
}))
```

**Benefits:**
- Can toggle back to mock if API has issues
- Gradual rollout
- Easy debugging (compare mock vs API)

### 10.2 Rollback Plan

If integration causes critical issues:

1. **Immediate:** Set `NEXT_PUBLIC_USE_API=false` to revert to mock
2. **Fix:** Debug and fix API integration
3. **Re-enable:** Set back to `true` after fix

---

## 11. Performance Targets

### 11.1 Response Time Goals

| Operation | Target (p95) | Acceptable (p99) |
|-----------|-------------|------------------|
| Load project list | < 500ms | < 1s |
| Load project details | < 300ms | < 800ms |
| Start analysis | < 200ms | < 500ms |
| Load report | < 1s | < 2s |
| Render diagram | < 800ms | < 1.5s |
| Chat response (first token) | < 500ms | < 1s |
| Search results | < 1s | < 2s |

### 11.2 Monitoring (Future)

**Metrics to Track:**
- API response times (per endpoint)
- Error rates (by error type)
- User action success rates
- Time to interactive
- Largest contentful paint

**Tools:**
- Vercel Analytics (frontend performance)
- Custom logging to console (MVP)
- Future: Sentry, LogRocket, or similar

---

## 12. Security Considerations

### 12.1 CORS Configuration

**Backend must allow frontend origin:**
```python
# backend/app/config.py
cors_origins = [
    "http://localhost:3000",  # Development
    "https://codecompass.example.com",  # Production (future)
]
```

### 12.2 Input Validation

**Frontend:**
- Validate before sending (better UX)
- Use Zod or Yup for schema validation

**Backend:**
- Pydantic validates all inputs (already implemented)
- Never trust client data

### 12.3 Sensitive Data

**For MVP (local-only):**
- No authentication/authorization
- No sensitive data stored
- All data local to user's machine

**Future (if deployed):**
- API keys in environment variables only
- Never log sensitive data
- HTTPS in production

---

## 13. Documentation Requirements

### 13.1 Developer Documentation

**Update README.md with:**
- Environment setup instructions
- How to run frontend + backend together
- API endpoint documentation (link to `/docs`)
- Troubleshooting common issues

**Example:**
```markdown
## Running the Full Stack

1. Start backend:
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

2. Start frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Open http://localhost:3000

Backend API docs: http://localhost:8000/docs
```

### 13.2 API Client Documentation

**Document in `frontend/src/lib/api.ts`:**
```typescript
/**
 * API Client for CodeCompass Backend
 *
 * Usage:
 *   import { api } from '@/lib/api'
 *   const projects = await api.getProjects()
 *
 * Error handling:
 *   try {
 *     const project = await api.getProject(id)
 *   } catch (error) {
 *     if (error instanceof ApiError) {
 *       console.log(error.code) // e.g., "PROJECT_NOT_FOUND"
 *     }
 *   }
 */
```

---

## 14. Open Questions & Decisions Needed

### 14.1 Technical Decisions

| Question | Options | Recommendation | Rationale |
|----------|---------|----------------|-----------|
| **HTTP Client** | fetch, axios, ky | **fetch** (native) | No dependencies, sufficient for MVP |
| **Type Generation** | Manual, openapi-typescript | **Manual** for MVP | Fast to start, auto-gen later |
| **Polling Interval** | 1s, 2s, 5s | **2s** | Balance between freshness and load |
| **Error Toast Library** | react-hot-toast, sonner | **sonner** | Modern, small, good UX |
| **Retry Strategy** | Manual, exponential backoff | **Exponential backoff** | Industry standard |

### 14.2 Product Decisions

| Question | Decision | Impact |
|----------|----------|--------|
| Should we cache project list? | Yes, refresh on demand | Faster UX, but might show stale data |
| Show loading for < 200ms requests? | No, feels janky | Better perceived performance |
| Allow offline work? | No (MVP), Yes (future) | Scope decision |
| Optimistic UI updates? | No (MVP), Yes (future) | Adds complexity |

---

## 15. Success Criteria

### 15.1 Functional Requirements

- [ ] All frontend components fetch data from backend API
- [ ] No remaining mock data in frontend
- [ ] Loading states show for all async operations
- [ ] Errors display user-friendly messages
- [ ] Analysis progress updates in real-time
- [ ] Chat sends messages to backend and displays responses
- [ ] File tree loads actual project structure
- [ ] Reports and diagrams show backend-generated content

### 15.2 Non-Functional Requirements

- [ ] API calls complete within performance targets (see 11.1)
- [ ] No console errors in browser
- [ ] Mobile responsive (unchanged from current)
- [ ] Accessibility maintained (keyboard nav, screen readers)
- [ ] Works in Chrome, Firefox, Safari, Edge

### 15.3 Developer Experience

- [ ] Clear error messages aid debugging
- [ ] Environment variables properly documented
- [ ] Easy to run both services locally
- [ ] TypeScript types prevent common mistakes
- [ ] Code is maintainable and well-commented

---

## 16. Implementation Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **Phase 1: Foundation** | 4-6 hours | API client, types, error handling |
| **Phase 2: Projects** | 4-6 hours | CRUD operations connected |
| **Phase 3: Analysis** | 6-8 hours | Analysis flow with polling |
| **Phase 4: Reports & Diagrams** | 4-6 hours | Display backend content |
| **Phase 5: Files & Search** | 4-6 hours | File browsing, search |
| **Phase 6: Chat** | 6-8 hours | Chat integration |
| **Testing & Polish** | 4-6 hours | Bug fixes, refinement |
| **Total** | **32-46 hours** | **~1 week full-time** |

---

## 17. Risks & Mitigation

### 17.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **CORS issues** | Medium | High | Test early, clear CORS docs |
| **Type mismatches** | High | Medium | Create types matching backend exactly |
| **Performance degradation** | Low | Medium | Monitor response times, optimize as needed |
| **WebSocket needed for chat** | Low | Low | Start with polling, upgrade later |
| **Date parsing bugs** | Medium | Low | Thorough testing of date fields |

### 17.2 Product Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **UX worse than mock** | Medium | High | Keep loading states fast and clear |
| **Breaking changes during integration** | High | Medium | Incremental migration with feature flags |
| **Scope creep** | Medium | Medium | Stick to phases, defer enhancements |

---

## 18. Future Enhancements (Post-MVP)

**Not in scope for initial integration, but plan for:**

1. **Optimistic UI Updates**
   - Update UI immediately, rollback if API fails
   - Better perceived performance

2. **WebSocket for Real-Time**
   - Replace polling with push notifications
   - Live chat streaming

3. **Request Caching**
   - React Query or SWR for intelligent caching
   - Stale-while-revalidate pattern

4. **Offline Support**
   - Service worker
   - IndexedDB for local storage
   - Sync queue for failed requests

5. **Type Generation**
   - Auto-generate TypeScript types from OpenAPI spec
   - Keep frontend/backend types in sync automatically

6. **Error Tracking**
   - Sentry or similar for production error monitoring
   - User session replay

7. **Performance Monitoring**
   - Real user monitoring (RUM)
   - API endpoint performance tracking

8. **Authentication**
   - JWT tokens
   - Refresh token flow
   - Protected routes

---

## 19. Appendix

### A. API Endpoint Checklist

Complete list of endpoints to integrate:

**Projects:**
- [ ] `GET /` - Root
- [ ] `GET /health` - Health check
- [ ] `POST /api/projects` - Create
- [ ] `GET /api/projects` - List
- [ ] `GET /api/projects/{id}` - Get
- [ ] `PUT /api/projects/{id}` - Update
- [ ] `DELETE /api/projects/{id}` - Delete

**Analysis:**
- [ ] `POST /api/projects/{id}/analyze` - Start
- [ ] `GET /api/projects/{id}/analysis` - Status
- [ ] `DELETE /api/projects/{id}/analysis` - Cancel

**Reports:**
- [ ] `GET /api/projects/{id}/reports` - List
- [ ] `GET /api/projects/{id}/reports/{type}` - Get

**Diagrams:**
- [ ] `GET /api/projects/{id}/diagrams` - List
- [ ] `GET /api/projects/{id}/diagrams/{type}` - Get
- [ ] `GET /api/projects/{id}/diagrams/{type}/svg` - SVG export

**Files:**
- [ ] `GET /api/projects/{id}/files` - Tree
- [ ] `GET /api/projects/{id}/files/{path}` - Content

**Search:**
- [ ] `POST /api/projects/{id}/search` - Search

**Chat:**
- [ ] `POST /api/projects/{id}/chat` - Send message
- [ ] `GET /api/projects/{id}/chat/sessions` - List sessions
- [ ] `GET /api/projects/{id}/chat/sessions/{id}` - Get session
- [ ] `DELETE /api/projects/{id}/chat/sessions/{id}` - Delete

**Settings:**
- [ ] `GET /api/settings` - Get
- [ ] `PUT /api/settings` - Update
- [ ] `GET /api/settings/providers` - List providers
- [ ] `POST /api/settings/test` - Test connection

### B. Example API Client Structure

```typescript
// frontend/src/lib/api.ts
class CodeCompassAPI {
  // Projects
  async getProjects(params?: ListParams): Promise<ProjectListResponse> {}
  async createProject(data: ProjectCreate): Promise<Project> {}
  async getProject(id: string): Promise<Project> {}
  async updateProject(id: string, data: ProjectUpdate): Promise<Project> {}
  async deleteProject(id: string): Promise<void> {}

  // Analysis
  async startAnalysis(projectId: string): Promise<AnalysisStartResponse> {}
  async getAnalysisStatus(projectId: string): Promise<Analysis> {}
  async cancelAnalysis(projectId: string): Promise<void> {}

  // Reports
  async listReports(projectId: string): Promise<Report[]> {}
  async getReport(projectId: string, type: ReportType): Promise<Report> {}

  // Diagrams
  async listDiagrams(projectId: string): Promise<Diagram[]> {}
  async getDiagram(projectId: string, type: DiagramType): Promise<Diagram> {}

  // Files
  async getFileTree(projectId: string): Promise<FileTree> {}
  async getFileContent(projectId: string, path: string): Promise<FileContent> {}

  // Search
  async search(projectId: string, query: string): Promise<SearchResults> {}

  // Chat
  async sendChatMessage(projectId: string, message: string, sessionId?: string): Promise<ChatResponse> {}
  async listChatSessions(projectId: string): Promise<ChatSession[]> {}
  async getChatSession(projectId: string, sessionId: string): Promise<ChatSession> {}
  async deleteChatSession(projectId: string, sessionId: string): Promise<void> {}

  // Settings
  async getSettings(): Promise<Settings> {}
  async updateSettings(settings: Partial<Settings>): Promise<Settings> {}
  async listProviders(): Promise<Provider[]> {}
  async testConnection(config: TestConfig): Promise<TestResult> {}
}

export const api = new CodeCompassAPI()
```

---

## 20. Conclusion

This integration bridges the gap between our fully functional frontend and backend, transforming CodeCompass from two independent systems into a cohesive application. By following the phased approach outlined in this document, we'll maintain stability while progressively replacing mock data with real API calls.

**Key Takeaways:**
1. **Incremental migration** - Replace one feature at a time
2. **User experience first** - Loading and error states are non-negotiable
3. **Type safety** - TypeScript types prevent integration bugs
4. **Performance awareness** - Monitor and optimize as we integrate
5. **Future-proof** - Design for WebSocket, caching, offline support

**Next Steps:**
1. Review and approve this PRD
2. Set up development environment (Docker Compose recommended)
3. Begin Phase 1: Foundation
4. Track progress against phase checklists
5. Test thoroughly at each phase before moving forward

The end result will be a production-ready MVP where users can analyze codebases, view reports, chat with AI, and explore files - all powered by our backend API.
