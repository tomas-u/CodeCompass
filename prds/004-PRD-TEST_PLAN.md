# CodeCompass Testing Strategy - Product Requirements Document

## Document Info
| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Status** | Approved |
| **Author** | Senior Test Manager |
| **Last Updated** | 2026-01-14 |
| **Related Documents** | 001-PRD_BACKEND_API.md, 003-PRD_CONNECT_FRONTEND_AND_BACKEND.md |

---

## 1. Executive Summary

This document defines the comprehensive testing strategy for CodeCompass, an intelligent code analysis platform. Currently at 0% test coverage across 3,546 lines of Python backend code and 30+ React frontend components, this plan establishes a phased approach to achieve 70% backend coverage and 60% E2E coverage of critical user flows over 3 weeks.

### Current State Assessment

| Aspect | Status | Details |
|--------|--------|---------|
| **Backend Tests** | 0% coverage | pytest installed but no test files exist |
| **Frontend Tests** | 0% coverage | No test framework configured |
| **Completed Features** | 5 stories | Stories #9, #10, #11, #33 + Git Service |
| **Lines of Code** | 3,546 (backend) | 36 Python files, 30+ React components |
| **Critical Dependencies** | Tree-sitter, FastAPI, SQLite | Real code analysis, API endpoints, database |

### Testing Objectives

**Primary Goals:**
1. Establish sustainable testing infrastructure with minimal overhead
2. Achieve 70% backend test coverage (line coverage)
3. Achieve 60% E2E coverage of critical user flows
4. Enable CI/CD integration for automated testing
5. Prevent regression bugs through comprehensive test suite

**Success Metrics:**
- 50% backend coverage by end of Week 1
- 65% backend coverage by end of Week 2
- 70% backend coverage by end of Week 3
- All critical user flows tested E2E
- Test execution time < 2 minutes (backend suite)
- Zero flaky tests

---

## 2. Technology Stack Decisions

### 2.1 Backend Testing Framework: pytest + pytest-asyncio

**Decision:** Use pytest as the primary testing framework for the Python backend.

**Rationale:**
- ✅ **Already Installed:** pytest==9.0.2 and pytest-asyncio==1.3.0 are in requirements.txt
- ✅ **Native FastAPI Support:** FastAPI provides TestClient built on httpx, seamlessly integrated with pytest
- ✅ **Async/Await Support:** pytest-asyncio handles async background tasks used throughout the codebase
- ✅ **Rich Ecosystem:** Extensive plugin system (pytest-cov, pytest-mock, pytest-xdist for parallel execution)
- ✅ **Industry Standard:** 90%+ of Python projects use pytest, easier hiring and onboarding
- ✅ **Excellent Fixtures:** Built-in fixture system perfect for database/service setup and teardown

**Additional Dependencies Required:**
```txt
pytest-cov==5.0.0          # Coverage reporting with branch analysis
pytest-mock==3.14.0        # Mocking utilities built on unittest.mock
faker==25.0.0              # Test data generation for realistic fixtures
pytest-xdist==3.5.0        # Parallel test execution (Phase 3)
```

**Alternative Considered:** unittest (standard library)
- ❌ Rejected: More verbose syntax, no async support out-of-box, less powerful fixtures

---

### 2.2 Frontend Testing Framework: Playwright (Phased Approach)

**Decision:** Use Playwright MCP Tools for Phase 1-2, optionally install locally in Phase 3.

**Phase 1-2: MCP Playwright Tools**

**Rationale:**
- ✅ **Zero Configuration:** Available immediately via Claude MCP integration
- ✅ **No npm Installation:** No package.json changes needed for MVP testing
- ✅ **Direct Browser Control:** Interactive testing against running dev server
- ✅ **Visual Feedback:** Screenshot capability for debugging and documentation
- ✅ **Rapid Prototyping:** Perfect for validating critical flows during development

**Use Cases:**
- Manual E2E test execution via Claude interface
- Quick validation of user flows
- Screenshot-based bug reports
- Real-time debugging during development

**Phase 3: Local Playwright Installation (Optional)**

**Dependencies:**
```bash
npm install -D @playwright/test @playwright/experimental-ct-react
```

**Benefits:**
- CI/CD integration via GitHub Actions
- Parallel test execution
- Automated test reports
- Component testing capabilities

**Migration Path:**
- Document E2E scenarios in Phase 2 using MCP tools
- Convert documented scenarios to local Playwright tests in Phase 3
- Maintain both approaches: MCP for rapid testing, local for CI/CD

---

## 3. Test Pyramid Strategy

### 3.1 Test Distribution

The testing strategy follows the industry-standard test pyramid to maximize coverage while minimizing execution time and maintenance overhead.

```
                    /\
                   /  \
                  / E2E\ 10% (4 critical flows)
                 /______\
                /        \
               /Integration\ 30% (15-20 test files)
              /______________\
             /                \
            /   Unit Tests     \ 60% (40+ test files)
           /____________________\
```

**Distribution Rationale:**
- **Unit Tests (60%):** Fast, isolated, cover business logic and utilities
- **Integration Tests (30%):** API endpoints, database operations, service integration
- **E2E Tests (10%):** Critical user flows, full stack verification

### 3.2 Coverage Targets

#### Backend Coverage

| Component | Target Coverage | Priority | Test Type |
|-----------|----------------|----------|-----------|
| **Overall Backend** | 70% line, 60% branch | High | All |
| GitService | 80%+ | P0 | Unit |
| GenericAnalyzer | 75%+ | P0 | Unit |
| Analysis Service | 65%+ | P0 | Integration |
| API Endpoints | 70%+ | P0 | Integration |
| Utilities (parsers, detectors) | 75%+ | P1 | Unit |
| Models & Schemas | 90%+ | P1 | Unit |
| Config & Constants | 50%+ | P2 | Unit |

**Coverage Approach:**
- **Line Coverage:** Percentage of code lines executed during tests
- **Branch Coverage:** Percentage of conditional branches tested (if/else, try/except)
- **Exclusions:** Test files, migrations, __init__.py, vendored code

#### Frontend Coverage

| Component | Target Coverage | Priority | Test Type |
|-----------|----------------|----------|-----------|
| **Critical User Flows** | 60% | High | E2E |
| Project Creation Flow | 100% | P0 | E2E |
| Analysis Polling | 100% | P0 | E2E |
| Dashboard Navigation | 80% | P1 | E2E |
| Project List Management | 80% | P1 | E2E |

**E2E Coverage Definition:**
- Percentage of critical user paths tested from UI to database
- Does NOT measure line coverage of frontend code
- Focuses on user-facing functionality and integration

---

## 4. Completed Features Requiring Test Coverage

### 4.1 Story #33: Generic Tree-sitter Analyzer

**Implementation:** `backend/app/services/analyzer/generic_analyzer.py` (282 lines)

**Completed:** 2026-01-14 (Commit 939d2b4)

**Test Coverage Needed:**

| Feature | Test Type | Priority | Estimated Tests |
|---------|-----------|----------|-----------------|
| Language detection (30+ extensions) | Unit | P0 | 5 tests |
| Tree-sitter parsing (Python, JS, TS, TSX) | Unit | P0 | 8 tests |
| Import extraction | Unit | P0 | 6 tests |
| .gitignore pattern filtering | Unit | P0 | 7 tests |
| Stats aggregation | Unit | P0 | 4 tests |
| Binary/malformed file handling | Unit | P1 | 3 tests |
| Large file skipping | Unit | P1 | 2 tests |
| **Total** | | | **35 tests** |

**Critical Test Scenarios:**
1. Analyze Python repository with imports
2. Analyze JavaScript repository with ES6 modules
3. Analyze mixed-language repository
4. Respect .gitignore (skip node_modules, venv)
5. Handle syntax errors gracefully
6. Skip files > 10MB
7. Count LOC accurately

---

### 4.2 Story #10: Project CRUD with SQLite

**Implementation:** Database models, API endpoints

**Completed:** 2026-01-12 (Commit 2157d34)

**Test Coverage Needed:**

| Feature | Test Type | Priority | Estimated Tests |
|---------|-----------|----------|-----------------|
| Create project (git_url) | Integration | P0 | 3 tests |
| Create project (local_path) | Integration | P0 | 3 tests |
| List projects with pagination | Integration | P0 | 4 tests |
| List projects with filters | Integration | P0 | 3 tests |
| Get project by ID | Integration | P0 | 2 tests |
| Update project | Integration | P1 | 2 tests |
| Delete project | Integration | P1 | 2 tests |
| Background task triggering | Integration | P0 | 2 tests |
| Validation errors | Integration | P1 | 4 tests |
| **Total** | | | **25 tests** |

**Critical Test Scenarios:**
1. Create project and verify database entry
2. Create project triggers background analysis
3. List projects with status filter
4. Pagination works correctly (limit, offset)
5. 404 on nonexistent project
6. Validation rejects invalid git URL
7. Delete removes project from database

---

### 4.3 Story #11: Real-time Status Polling

**Implementation:** `backend/app/services/analysis_service.py`, `frontend/src/hooks/useProjectStatus.ts`

**Completed:** 2026-01-12 (Commit 20dbfcc)

**Test Coverage Needed:**

| Feature | Test Type | Priority | Estimated Tests |
|---------|-----------|----------|-----------------|
| Analysis status progression | Integration | P0 | 5 tests |
| Status updates (pending→ready) | Integration | P0 | 4 tests |
| Git cloning integration | Integration | P0 | 3 tests |
| Analyzer integration | Integration | P0 | 3 tests |
| Error handling (failed status) | Integration | P0 | 4 tests |
| useProjectStatus hook | E2E | P0 | 1 flow |
| Polling every 2 seconds | E2E | P0 | 1 flow |
| Terminal state detection | E2E | P0 | 1 flow |
| **Total** | | | **19 tests + 3 E2E flows** |

**Critical Test Scenarios:**
1. Run analysis on local path → status reaches "ready"
2. Run analysis on git URL → status reaches "ready"
3. Invalid path → status reaches "failed"
4. Frontend polling stops on terminal state
5. No memory leaks from intervals

---

### 4.4 Git Service

**Implementation:** `backend/app/services/git_service.py` (236 lines)

**Completed:** 2026-01-14 (Commit 939d2b4)

**Test Coverage Needed:**

| Feature | Test Type | Priority | Estimated Tests |
|---------|-----------|----------|-----------------|
| Clone repository success | Unit | P0 | 2 tests |
| Clone repository failure | Unit | P0 | 2 tests |
| Clone timeout handling | Unit | P0 | 2 tests |
| Branch fallback (main→master) | Unit | P0 | 2 tests |
| Size limit enforcement | Unit | P0 | 2 tests |
| Repository validation | Unit | P0 | 2 tests |
| Get repository size | Unit | P1 | 2 tests |
| Pull repository | Unit | P1 | 2 tests |
| **Total** | | | **16 tests** |

**Critical Test Scenarios:**
1. Clone valid Git URL succeeds
2. Clone invalid URL fails gracefully
3. Clone timeout after 5 minutes
4. Repository exceeds 1GB limit → fails
5. Main branch not found → fallback to master
6. Validate cloned repository has .git directory

---

### 4.5 Additional Features

**Story #9: Project List from Backend** - Zustand store, API client
- API client method tests (5 tests)
- Store action tests (3 tests)
- E2E: Project list rendering (1 flow)

---

## 5. Implementation Phases

### 5.1 Phase 1: Foundation (Week 1) - HIGHEST PRIORITY

**Goal:** Cover critical backend services and basic API endpoints to reach 50% backend coverage.

**Timeline:** 5 days (20 hours of work)

#### Tasks

**Task 1: Setup Testing Infrastructure** (2 hours)

**Deliverables:**
- Create `backend/tests/` directory structure
- Write `backend/tests/conftest.py` with global fixtures
- Configure `backend/pytest.ini` for test discovery
- Configure `backend/.coveragerc` for coverage reporting
- Add test dependencies to `backend/requirements.txt`
- Update `backend/README.md` with test running commands

**Directory Structure:**
```
backend/tests/
├── __init__.py
├── conftest.py
├── pytest.ini
├── unit/
│   ├── __init__.py
│   └── test_analyzers/
│       └── __init__.py
├── integration/
│   ├── __init__.py
└── fixtures/
    ├── __init__.py
    ├── factories.py
    └── sample_repos/
```

**Test Commands to Document:**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/test_git_service.py

# Run with verbose output
pytest -v

# Run tests in parallel (Phase 3)
pytest -n auto
```

---

**Task 2: Unit Tests - GitService** (4 hours)

**File:** `backend/tests/unit/test_git_service.py`

**Tests to Write:**
1. `test_clone_repository_success` - Mock subprocess, verify clone succeeds
2. `test_clone_repository_with_main_branch` - Verify main branch used by default
3. `test_clone_repository_with_master_fallback` - Main fails → tries master
4. `test_clone_repository_failure_invalid_url` - Invalid URL returns error
5. `test_clone_repository_timeout` - Mock TimeoutExpired exception
6. `test_clone_repository_exceeds_size_limit` - Mock size check, verify rejection
7. `test_validate_repository_valid` - .git directory exists → returns True
8. `test_validate_repository_invalid` - No .git directory → returns False
9. `test_get_repo_size` - Calculate directory size in MB

**Example Test:**
```python
@patch("app.services.git_service.subprocess.run")
def test_clone_repository_success(mock_run, temp_repo_dir):
    """Test successful repository cloning."""
    mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

    service = GitService(timeout=300)
    success, error = service.clone_repository(
        git_url="https://github.com/test/repo.git",
        local_path=str(temp_repo_dir / "cloned"),
        branch="main"
    )

    assert success is True
    assert error is None
    mock_run.assert_called_once()
```

**Target:** 80% coverage of git_service.py

---

**Task 3: Unit Tests - GenericAnalyzer** (6 hours)

**File:** `backend/tests/unit/test_analyzers/test_generic_analyzer.py`

**Tests to Write:**
1. `test_analyze_simple_python_repo` - Analyze fixture with 3 Python files
2. `test_analyze_simple_javascript_repo` - Analyze fixture with 3 JS files
3. `test_analyze_mixed_language_repo` - Python + JavaScript files
4. `test_collect_files_respects_gitignore` - node_modules ignored
5. `test_language_detection` - .py → Python, .js → JavaScript
6. `test_analyze_file_counts_lines` - Non-empty line counting
7. `test_extract_python_imports` - Find import and from statements
8. `test_extract_javascript_imports` - Find ES6 import statements
9. `test_stats_aggregation` - Files, LOC, languages aggregated correctly
10. `test_skip_binary_files` - UnicodeDecodeError → skip file
11. `test_skip_large_files` - Files > 10MB skipped
12. `test_handle_syntax_errors` - Malformed code doesn't crash

**Example Test:**
```python
def test_analyze_simple_python_repo(sample_python_repo):
    """Test analyzing a simple Python repository."""
    analyzer = GenericAnalyzer(str(sample_python_repo))
    stats = analyzer.analyze()

    assert stats["files"] >= 2
    assert stats["lines_of_code"] > 0
    assert "Python" in stats["languages"]
    assert stats["languages"]["Python"]["files"] >= 2
```

**Target:** 75% coverage of generic_analyzer.py

---

**Task 4: Integration Tests - Project API** (4 hours)

**File:** `backend/tests/integration/test_api_projects.py`

**Tests to Write:**
1. `test_create_project_local_path` - POST /api/projects with local path
2. `test_create_project_git_url` - POST /api/projects with Git URL
3. `test_create_project_validation_error` - Invalid input → 422
4. `test_list_projects_empty` - GET /api/projects → empty list
5. `test_list_projects_with_data` - Create 5 projects → list returns all
6. `test_list_projects_with_pagination` - limit=3, offset=2 works
7. `test_list_projects_filter_by_status` - status=ready filter works
8. `test_get_project_by_id` - GET /api/projects/{id} returns project
9. `test_get_project_404` - Nonexistent ID → 404 error
10. `test_update_project` - PUT /api/projects/{id} updates fields
11. `test_delete_project` - DELETE /api/projects/{id} removes project

**Example Test:**
```python
def test_create_project_local_path(client, temp_repo_dir, mocker):
    """Test creating a project with local path."""
    # Mock background task
    mocker.patch("app.api.routes.projects.run_analysis")

    response = client.post(
        "/api/projects",
        json={
            "name": "Test Project",
            "source_type": "local_path",
            "source": str(temp_repo_dir),
            "branch": "main"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["status"] == "pending"
    assert "id" in data
```

**Target:** 70% coverage of projects.py routes

---

**Task 5: Integration Tests - Analysis Service** (4 hours)

**File:** `backend/tests/integration/test_analysis_service.py`

**Tests to Write:**
1. `test_run_analysis_local_path_success` - Full analysis succeeds
2. `test_run_analysis_git_url_success` - Clone + analyze succeeds
3. `test_status_transitions` - pending→cloning→scanning→analyzing→ready
4. `test_analysis_failure_invalid_path` - Path not found → status=failed
5. `test_analysis_failure_git_clone` - Clone fails → status=failed
6. `test_stats_populated` - Stats field populated with real data

**Example Test:**
```python
@pytest.mark.asyncio
async def test_run_analysis_local_path_success(
    test_db_session,
    project_factory,
    sample_python_repo,
    mocker
):
    """Test successful analysis with local path."""
    project = project_factory(
        source_type="local_path",
        source=str(sample_python_repo),
        status=ProjectStatus.pending
    )

    await run_analysis(project.id)

    test_db_session.refresh(project)
    assert project.status == ProjectStatus.ready
    assert project.stats["files"] > 0
    assert project.last_analyzed_at is not None
```

**Target:** 65% coverage of analysis_service.py

---

#### Phase 1 Deliverables

**Quantitative:**
- 40+ unit tests written and passing
- 15+ integration tests written and passing
- 50% overall backend coverage
- Test execution time < 2 minutes

**Qualitative:**
- All tests documented with clear docstrings
- README updated with test commands
- Fixtures reusable across test files
- CI-ready (tests run via simple `pytest` command)

**Verification:**
```bash
# Run coverage report
pytest --cov=app --cov-report=term

# Expected output:
# Name                          Stmts   Miss  Cover
# -----------------------------------------------
# app/services/git_service.py     85     15    82%
# app/services/analyzer/...       120     30    75%
# app/api/routes/projects.py      45     12    73%
# -----------------------------------------------
# TOTAL                          1800    900    50%
```

---

### 5.2 Phase 2: Core Features (Week 2)

**Goal:** Expand coverage to remaining services and add E2E tests to reach 65% backend coverage.

**Timeline:** 5 days (17 hours of work)

#### Tasks

**Task 1: Unit Tests - Utilities** (3 hours)

**Files:**
- `backend/tests/unit/test_analyzers/test_language_detector.py` (8 tests)
- `backend/tests/unit/test_analyzers/test_gitignore_parser.py` (10 tests)
- `backend/tests/unit/test_analyzers/test_tree_sitter_utils.py` (7 tests)

**Key Tests:**
- Language detection: .py → Python, .ts → TypeScript
- Grammar lookup: Python → "python"
- Gitignore pattern matching: node_modules/** ignored
- Default ignore patterns applied
- Tree-sitter grammar loading
- Parser caching

**Target:** 80% coverage of utils

---

**Task 2: Unit Tests - Models & Schemas** (2 hours)

**Files:**
- `backend/tests/unit/test_models.py` (6 tests)
- `backend/tests/unit/test_schemas.py` (5 tests)

**Key Tests:**
- Project model to_dict() serialization
- Enum conversions (ProjectStatus, SourceType)
- Pydantic validation (invalid inputs)
- Required field enforcement

**Target:** 90% coverage (straightforward code)

---

**Task 3: Integration Tests - Additional APIs** (4 hours)

**Files:**
- `backend/tests/integration/test_api_files.py` (5 tests)
- `backend/tests/integration/test_api_admin.py` (3 tests)
- `backend/tests/integration/test_database.py` (6 tests)

**Key Tests:**
- File listing endpoints
- Admin clear database
- Database query filters
- Transaction handling

**Target:** 60% coverage

---

**Task 4: E2E Tests with MCP Tools** (6 hours)

**Deliverable:** `docs/testing/e2e-tests.md`

**4 E2E Test Scenarios:**

**E2E Flow 1: Create Project → Analyze → View Dashboard** (90 minutes)

**Pre-conditions:**
- Backend running on http://localhost:8000
- Frontend running on http://localhost:3000
- Database cleared

**Test Steps:**
1. Navigate to http://localhost:3000
2. Take snapshot of welcome page
3. Click "Create New Project" button
4. Fill form:
   - Name: "Backend Analysis Test"
   - Type: "Local Path"
   - Path: "/home/tomas/dev/streampower/codeCompass/backend"
5. Click "Create Project" button
6. Verify redirect to project detail page (URL: /projects/[id])
7. Wait for status "Analyzing" to appear (max 2 seconds)
8. Take snapshot of analyzing state
9. Wait for status "Ready" to appear (max 30 seconds)
10. Take snapshot of ready state
11. Verify stats display: ~100 files, ~11k LOC
12. Click "Overview" tab
13. Verify language breakdown shows Python
14. Take snapshot of overview tab

**Expected Results:**
- Project created successfully
- Status progresses: pending→cloning→scanning→analyzing→ready
- Stats accurate: 104 files, 11,167 LOC
- Dashboard tabs visible and functional
- No console errors

**MCP Tool Calls:**
```javascript
browser_navigate(url="http://localhost:3000")
browser_snapshot()
browser_click(element="Create New Project button", ref="...")
browser_fill_form(fields=[...])
browser_click(element="Submit button", ref="...")
browser_wait_for(text="Analyzing", time=2)
browser_snapshot()
browser_wait_for(text="Ready", time=30)
browser_snapshot()
browser_click(element="Overview tab", ref="...")
browser_snapshot()
```

---

**E2E Flow 2: Project List Management** (60 minutes)

**Test Steps:**
1. Create 3 projects via API with different statuses
2. Navigate to home page
3. Verify 3 projects displayed
4. Filter by status="ready"
5. Verify only 1 project shown
6. Search by name "Test"
7. Verify search results
8. Delete a project
9. Confirm deletion in dialog
10. Verify project removed from list

**Expected Results:**
- Filtering works correctly
- Search returns matching results
- Delete confirmation appears
- Project removed after deletion

---

**E2E Flow 3: Real-time Status Polling** (60 minutes)

**Test Steps:**
1. Create project with Git URL (small public repo)
2. Observe status badge updates
3. Monitor network requests (every 2 seconds)
4. Verify progress bar updates
5. Verify phase transitions visible
6. Verify polling stops at "ready" status
7. Check for memory leaks (interval cleanup)

**Expected Results:**
- Status updates without page refresh
- Polling interval accurate (2 seconds)
- Progress bar increments
- No memory leaks

---

**E2E Flow 4: Dashboard Tab Switching** (30 minutes)

**Test Steps:**
1. Open project detail page
2. Click "Overview" tab → verify content
3. Click "Diagrams" tab → verify placeholder
4. Click "Files" tab → verify placeholder
5. Click "Reports" tab → verify placeholder
6. Navigate away and back
7. Verify last tab remembered (Zustand state)

**Expected Results:**
- All tabs render without errors
- Tab state persists
- No console errors

---

**Task 5: Test Data & Fixtures** (2 hours)

**Create Fixtures:**
- `backend/tests/fixtures/sample_repos/python_simple/` (minimal Python repo)
- `backend/tests/fixtures/sample_repos/javascript_simple/` (minimal JS repo)
- `backend/tests/fixtures/sample_repos/mixed_language/` (Python + JS)
- `backend/tests/fixtures/factories.py` (data factories for Projects)

**Sample Python Repo Structure:**
```
python_simple/
├── .gitignore
├── main.py           # 15 lines
├── utils.py          # 10 lines
└── requirements.txt  # 3 lines
```

---

#### Phase 2 Deliverables

**Quantitative:**
- 30+ additional tests written
- 65% overall backend coverage
- 4 E2E flows documented and executed
- Sample test repositories created

**Qualitative:**
- E2E documentation with screenshots
- Reusable test fixtures
- All critical user flows verified

---

### 5.3 Phase 3: Advanced Features (Week 3) - FUTURE

**Goal:** Polish, performance testing, optional CI/CD integration to reach 70%+ backend coverage.

**Timeline:** 5 days (12 hours of work)

#### Tasks

**Task 1: Performance Tests** (3 hours)

**Tests:**
- Analyze large repository (1000+ files)
- Concurrent analysis requests
- Database query performance
- Test execution speed

**Benchmarks:**
- Analysis < 5 minutes for 1000 files
- Project listing < 2 seconds
- Test suite < 2 minutes

---

**Task 2: Error Path Testing** (3 hours)

**Tests:**
- Network failures during git clone
- Malformed inputs (invalid URLs)
- Edge cases (empty repos, binary-only repos)
- Permission denied scenarios

---

**Task 3: Optional - Install Local Playwright** (4 hours)

**Setup:**
```bash
cd frontend
npm install -D @playwright/test
npx playwright install --with-deps
```

**Configure:** `frontend/playwright.config.ts`

**Migrate E2E Tests:**
- Convert Flow 1-4 from MCP documentation to Playwright test files
- Create GitHub Actions workflow
- Add to CI/CD pipeline

---

**Task 4: Test Optimization** (2 hours)

**Optimizations:**
- Enable pytest-xdist for parallel execution
- Use session-scoped fixtures for expensive setup
- Cache test data between runs
- Optimize database fixtures (in-memory SQLite)

**Commands:**
```bash
# Run tests in parallel
pytest -n auto

# Run only fast tests
pytest -m "not slow"
```

---

#### Phase 3 Deliverables

**Quantitative:**
- 70%+ backend coverage
- Performance benchmarks documented
- Optional: Local Playwright configured

**Qualitative:**
- CI/CD ready
- Performance baselines established
- Test execution optimized

---

## 6. Test Infrastructure Setup

### 6.1 Global Fixtures (conftest.py)

**File:** `backend/tests/conftest.py`

```python
"""Global pytest fixtures for CodeCompass tests."""

import pytest
import tempfile
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models.project import Project
from app.schemas.project import ProjectStatus, SourceType


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_db_engine():
    """Create in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create database session for testing."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def test_db(test_db_session):
    """Override get_db dependency with test database."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield test_db_session
    app.dependency_overrides.clear()


# ============================================================================
# API Client Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def client(test_db):
    """FastAPI test client with test database."""
    with TestClient(app) as test_client:
        yield test_client


# ============================================================================
# File System Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def temp_repo_dir():
    """Create temporary directory for test repositories."""
    temp_dir = tempfile.mkdtemp(prefix="codecompass_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def sample_python_repo(temp_repo_dir):
    """Create minimal Python repository for testing."""
    repo_path = temp_repo_dir / "python_sample"
    repo_path.mkdir()

    (repo_path / "main.py").write_text("""
import os
from utils import helper

def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
""")

    (repo_path / "utils.py").write_text("""
def helper():
    return "Helper function"

def calculate(a, b):
    return a + b
""")

    (repo_path / "requirements.txt").write_text("""
fastapi==0.128.0
pytest==9.0.2
""")

    return repo_path


# ============================================================================
# Data Factories
# ============================================================================

@pytest.fixture
def project_factory(test_db_session):
    """Factory for creating test projects."""
    def _create_project(
        name="Test Project",
        source_type=SourceType.local_path,
        source="/tmp/test",
        status=ProjectStatus.pending,
        **kwargs
    ):
        from uuid import uuid4
        project = Project(
            id=str(uuid4()),
            name=name,
            source_type=source_type,
            source=source,
            branch=kwargs.get("branch", "main"),
            local_path=kwargs.get("local_path", source),
            status=status,
            settings=kwargs.get("settings"),
            stats=kwargs.get("stats"),
        )
        test_db_session.add(project)
        test_db_session.commit()
        test_db_session.refresh(project)
        return project

    return _create_project
```

---

### 6.2 Pytest Configuration

**File:** `backend/pytest.ini`

```ini
[pytest]
# Test discovery
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Output options
addopts =
    -v
    --tb=short
    --strict-markers
    --disable-warnings

# Markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests

# Async settings
asyncio_mode = auto

# Coverage settings (when using --cov)
[coverage:run]
source = app
omit =
    */tests/*
    */venv/*
    */__pycache__/*

[coverage:report]
precision = 2
show_missing = True
skip_covered = False
```

---

### 6.3 Coverage Configuration

**File:** `backend/.coveragerc`

```ini
[run]
source = app
omit =
    */tests/*
    */venv/*
    */__pycache__/*
    */migrations/*

[report]
precision = 2
show_missing = True
skip_covered = False
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstract

[html]
directory = htmlcov
```

---

## 7. CI/CD Integration (Phase 3)

### 7.1 GitHub Actions Workflow

**File:** `.github/workflows/test.yml`

```yaml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-tests:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Cache pip dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        working-directory: ./backend
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests with coverage
        working-directory: ./backend
        run: |
          pytest tests/ \
            --cov=app \
            --cov-report=xml \
            --cov-report=html \
            --cov-report=term \
            -v

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: ./backend/coverage.xml
          flags: backend
          fail_ci_if_error: true

      - name: Check coverage threshold
        working-directory: ./backend
        run: |
          coverage report --fail-under=70

      - name: Upload HTML coverage report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: backend/htmlcov/

  frontend-tests:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Install Playwright
        working-directory: ./frontend
        run: |
          npm install -D @playwright/test
          npx playwright install --with-deps

      - name: Run E2E tests
        working-directory: ./frontend
        run: npx playwright test

      - name: Upload Playwright report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

---

### 7.2 Test Execution Schedule

**On Pull Request:**
- All unit tests (mandatory)
- All integration tests (mandatory)
- E2E smoke tests (critical flows only)
- Coverage threshold check (70%)
- Must pass before merge

**On Push to Main:**
- Full test suite
- Coverage report uploaded to Codecov
- Performance benchmarks
- Deploy preview environment

**Scheduled (Nightly):**
- Extended E2E suite
- Performance regression tests
- Dependency security scan (Snyk/Dependabot)
- Flaky test detection

---

## 8. Quality Metrics & Benchmarks

### 8.1 Performance Benchmarks

**Test Execution Time Targets:**

| Test Suite | Target Time | Max Time | Optimization |
|------------|-------------|----------|--------------|
| Unit Tests | < 20 seconds | 30 seconds | Session fixtures |
| Integration Tests | < 40 seconds | 60 seconds | In-memory DB |
| Full Backend Suite | < 90 seconds | 2 minutes | Parallel execution |
| E2E Tests (per flow) | < 2 minutes | 5 minutes | Fast backend |

**Optimization Techniques:**
1. **Parallel Execution:** `pytest -n auto` (pytest-xdist)
2. **Session-Scoped Fixtures:** Expensive setup once per session
3. **In-Memory Database:** SQLite `:memory:` for speed
4. **Mock External Calls:** Git, network, file system

---

### 8.2 Flaky Test Prevention

**Strategies:**

**1. Use Fixed Timestamps**
```python
# BAD: Time-dependent test
def test_project_recent(project):
    assert (datetime.utcnow() - project.created_at).seconds < 1  # Flaky!

# GOOD: Fixed time
@patch("app.models.project.datetime")
def test_project_timestamp(mock_datetime, project):
    fixed_time = datetime(2024, 1, 1, 12, 0, 0)
    mock_datetime.utcnow.return_value = fixed_time
    assert project.created_at == fixed_time
```

**2. Mock External Dependencies**
```python
# Mock git operations
@patch("app.services.git_service.subprocess.run")
def test_clone(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    # Test logic
```

**3. No Random Values in Assertions**
```python
# BAD: Random data
def test_create_project():
    name = f"test-{random.randint(0, 999)}"  # Non-deterministic!

# GOOD: Fixed data
def test_create_project():
    name = "test-project-123"
```

**4. Proper Cleanup**
```python
@pytest.fixture
def temp_dir():
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)  # Always cleanup
```

**5. Deterministic Test Data**
```python
# Use factories with consistent data
project = project_factory(name="Test Project", status=ProjectStatus.ready)
```

---

### 8.3 Coverage Tracking

**Tools:**
- **Local:** pytest-cov (HTML reports)
- **CI/CD:** Codecov.io (PR comments, trend charts)
- **Badges:** Coverage badges in README.md

**Coverage Reports:**
```bash
# Generate HTML report
pytest --cov=app --cov-report=html

# Open report
open htmlcov/index.html

# Terminal report
pytest --cov=app --cov-report=term-missing
```

**Example Output:**
```
Name                                 Stmts   Miss  Cover   Missing
--------------------------------------------------------------------
app/services/git_service.py             85     15    82%   45-47, 67-73
app/services/analyzer/generic...       120     30    75%   156-162, 200-215
app/api/routes/projects.py              45     12    73%   89-95
--------------------------------------------------------------------
TOTAL                                 1800    540    70%
```

---

## 9. Success Criteria

### 9.1 Phase 1 Success Criteria

**Must Achieve:**
- ✅ 40+ unit tests written and passing
- ✅ 15+ integration tests written and passing
- ✅ 50% overall backend coverage
- ✅ All tests run in < 2 minutes
- ✅ Zero test failures on main branch
- ✅ Test documentation in README
- ✅ Reusable fixtures created

**Measured By:**
```bash
pytest --cov=app --cov-report=term
# Expected: TOTAL >= 50%
```

---

### 9.2 Phase 2 Success Criteria

**Must Achieve:**
- ✅ 30+ additional tests written
- ✅ 65% overall backend coverage
- ✅ 4 E2E flows documented and executed
- ✅ Sample test repositories created
- ✅ Test data factories implemented
- ✅ All critical user flows verified

**Measured By:**
```bash
pytest --cov=app --cov-report=term
# Expected: TOTAL >= 65%

# E2E documentation exists
ls docs/testing/e2e-tests.md
```

---

### 9.3 Phase 3 Success Criteria

**Must Achieve:**
- ✅ 70%+ backend coverage
- ✅ Performance benchmarks documented
- ✅ Test execution time < 2 minutes
- ✅ Optional: CI/CD workflow configured
- ✅ Optional: Local Playwright installed

**Measured By:**
```bash
pytest --cov=app --cov-report=term
# Expected: TOTAL >= 70%

# Performance check
time pytest
# Expected: < 2 minutes
```

---

## 10. Appendix: Example Test Files

### 10.1 Unit Test Example

**File:** `backend/tests/unit/test_git_service.py`

```python
"""Unit tests for GitService."""

import pytest
from unittest.mock import MagicMock, patch
from subprocess import TimeoutExpired
from app.services.git_service import GitService


class TestGitService:
    """Test GitService methods."""

    @patch("app.services.git_service.subprocess.run")
    def test_clone_repository_success(self, mock_run, temp_repo_dir):
        """Test successful repository cloning."""
        mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

        service = GitService(timeout=300)
        success, error = service.clone_repository(
            git_url="https://github.com/test/repo.git",
            local_path=str(temp_repo_dir / "cloned"),
            branch="main",
            max_size_mb=1000
        )

        assert success is True
        assert error is None
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "git" in args
        assert "clone" in args
        assert "--branch" in args
        assert "main" in args

    @patch("app.services.git_service.subprocess.run")
    def test_clone_repository_timeout(self, mock_run, temp_repo_dir):
        """Test clone timeout handling."""
        mock_run.side_effect = TimeoutExpired(cmd="git", timeout=300)

        service = GitService(timeout=300)
        success, error = service.clone_repository(
            git_url="https://github.com/test/repo.git",
            local_path=str(temp_repo_dir / "cloned"),
            branch="main"
        )

        assert success is False
        assert "timeout" in error.lower()

    @patch("app.services.git_service.subprocess.run")
    def test_clone_repository_fallback_to_master(self, mock_run, temp_repo_dir):
        """Test fallback to master branch when main fails."""
        # First call fails (main branch not found)
        # Second call succeeds (master branch)
        mock_run.side_effect = [
            MagicMock(returncode=1, stderr="remote branch not found", stdout=""),
            MagicMock(returncode=0, stderr="", stdout="")
        ]

        service = GitService(timeout=300)
        success, error = service.clone_repository(
            git_url="https://github.com/test/repo.git",
            local_path=str(temp_repo_dir / "cloned"),
            branch="main"
        )

        assert success is True
        assert mock_run.call_count == 2
        # Verify second call used master
        second_call_args = mock_run.call_args_list[1][0][0]
        assert "master" in second_call_args
```

---

### 10.2 Integration Test Example

**File:** `backend/tests/integration/test_api_projects.py`

```python
"""Integration tests for project API endpoints."""

import pytest
from app.schemas.project import SourceType, ProjectStatus


class TestProjectCRUD:
    """Test project CRUD operations."""

    def test_create_project_with_local_path(self, client, temp_repo_dir, mocker):
        """Test creating a project with local path."""
        # Mock background task
        mocker.patch("app.api.routes.projects.run_analysis")

        response = client.post(
            "/api/projects",
            json={
                "name": "Test Project",
                "description": "A test project",
                "source_type": "local_path",
                "source": str(temp_repo_dir),
                "branch": "main"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["status"] == "pending"
        assert "id" in data
        assert data["source_type"] == "local_path"

    def test_list_projects(self, client, project_factory):
        """Test listing projects with pagination."""
        # Create test projects
        for i in range(5):
            project_factory(name=f"Project {i}")

        response = client.get("/api/projects?limit=3&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 5
        assert data["limit"] == 3
        assert data["offset"] == 0

    def test_list_projects_with_filters(self, client, project_factory):
        """Test filtering projects by status."""
        project_factory(name="Ready Project", status=ProjectStatus.ready)
        project_factory(name="Failed Project", status=ProjectStatus.failed)
        project_factory(name="Pending Project", status=ProjectStatus.pending)

        response = client.get("/api/projects?status=ready")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["status"] == "ready"
        assert data["items"][0]["name"] == "Ready Project"

    def test_get_nonexistent_project(self, client):
        """Test 404 error for nonexistent project."""
        response = client.get("/api/projects/nonexistent-id")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
```

---

## 11. Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-14 | Senior Test Manager | Initial version - Comprehensive test strategy approved |

---

## 12. References

**Internal Documents:**
- `001-PRD-BACKEND_API.md` - Backend API specifications
- `003-PRD_CONNECT_FRONTEND_AND_BACKEND.md` - Frontend-backend integration
- `CLAUDE.md` - Project architecture and implementation phases
- `EPIC_STRUCTURE.md` - Feature roadmap and story definitions

**External Resources:**
- pytest documentation: https://docs.pytest.org/
- FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/
- Playwright documentation: https://playwright.dev/
- Test Pyramid: https://martinfowler.com/articles/practical-test-pyramid.html

---

**End of Document**
