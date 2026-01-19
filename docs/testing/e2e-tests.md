# End-to-End Test Scenarios

This document describes 5 critical E2E test flows for CodeCompass, executed using MCP Playwright tools for zero-config browser automation.

## Important: Screenshot vs YAML Snapshots

**WSL Environment Limitation:**
- Visual PNG screenshots will render as blank/white images in WSL due to GPU limitations in headless Chromium
- This CANNOT be fixed with xvfb or other virtual display solutions
- Do NOT attempt to fix screenshot rendering in WSL environments

**Recommended Testing Approach:**
- Use `browser_snapshot()` WITHOUT filename parameter to get YAML accessibility tree output
- The YAML structure provides complete validation of page elements, content, and interactive states
- YAML snapshots are more reliable for automated testing than visual screenshots
- If visual validation is required, run tests on native Linux with GPU or Windows

**When to use filenames with browser_snapshot():**
- Only use `browser_snapshot(filename="path.md")` if you want to save YAML output to a file
- Do NOT use PNG screenshots for functional validation in WSL

## Prerequisites

**Servers Must Be Running:**
- Backend: `cd backend && source venv/bin/activate && uvicorn app.main:app --reload` (http://localhost:8000)
- Frontend: `cd frontend && npm run dev` (http://localhost:3000)

**Database State:**
- Clean database recommended: `curl -X DELETE http://localhost:8000/api/admin/database/clear`

**Test Environment:**
- Browser: Chromium (via MCP Playwright)
- Test data: Backend repository at `/home/tomas/dev/streampower/codeCompass/backend`

---

## Flow 1: Create Project → Analyze → View Dashboard

**Description:** Test the complete project creation and analysis pipeline from start to finish.

**Pre-conditions:**
- Both servers running
- Clean database (no existing projects)

**Test Steps:**

1. **Navigate to homepage**
   - Open http://localhost:3000
   - Verify landing page loads

2. **Create new project**
   - Click "Create New Project" button
   - Fill form:
     - Name: "Test Backend Analysis"
     - Source Type: "Local Path"
     - Path: `/home/tomas/dev/streampower/codeCompass/backend`
     - Branch: "main" (default)
   - Click "Create Project" button

3. **Verify redirect to project detail page**
   - URL should be `/projects/{uuid}`
   - Project name displayed in header

4. **Monitor status progression**
   - Initial status: "Pending" (yellow badge)
   - After 1-2s: "Cloning" (blue badge)
   - After 2-3s: "Scanning" (purple badge)
   - After 5-10s: "Analyzing" (orange badge)
   - Final: "Ready" (green badge)
   - Total time: ~15-30 seconds

5. **Verify dashboard displays stats**
   - Files count: ~104 files
   - Lines of code: ~11,000 LOC
   - Directories: ~20-30 directories
   - Languages breakdown: Python (primary)

6. **Verify dashboard tabs visible**
   - Overview tab (active)
   - Diagrams tab
   - Files tab
   - Reports tab

**Expected Results:**
- ✅ Project created successfully
- ✅ All 4 status phases complete: pending→cloning→scanning→analyzing→ready
- ✅ Stats display correctly (~104 files, ~11k LOC)
- ✅ Dashboard renders with all tabs
- ✅ No errors in browser console

**MCP Tool Sequence:**
```
browser_navigate(url="http://localhost:3000")
browser_snapshot()  # Returns YAML accessibility tree inline

browser_click(element="Create New Project button", ref="[data-testid='create-project']")
browser_snapshot()  # Validate form elements appear

browser_fill_form(fields=[
  {name: "Project Name", type: "textbox", ref: "[name='name']", value: "Test Backend Analysis"},
  {name: "Source Type", type: "combobox", ref: "[name='source_type']", value: "Local Path"},
  {name: "Path", type: "textbox", ref: "[name='source']", value: "/home/tomas/dev/streampower/codeCompass/backend"}
])

browser_click(element="Submit button", ref: "[type='submit']")
browser_wait_for(text="Pending", time=2)
browser_snapshot()  # Verify "Pending" badge visible

browser_wait_for(text="Analyzing", time=10)
browser_snapshot()  # Verify "Analyzing" badge visible

browser_wait_for(text="Ready", time=30)
browser_snapshot()  # Verify "Ready" badge and stats displayed

browser_click(element="Overview tab", ref: "[role='tab'][name='Overview']")
browser_snapshot()  # Verify overview content loaded
```

**Troubleshooting:**
- If analysis hangs: Check backend logs for errors
- If stats are 0: Verify path is correct and accessible
- If "Ready" never appears: Check that analysis service is running

---

## Flow 2: Project List Management

**Description:** Test project listing, filtering, searching, and deletion functionality.

**Pre-conditions:**
- Backend and frontend running
- Database can be empty or have existing projects

**Test Steps:**

1. **Navigate to projects page**
   - Go to http://localhost:3000/projects
   - Or click "Projects" link in navigation

2. **Create 3 test projects**
   - Project 1: Name="Alpha Project", Path=".", Status will be "Pending/Ready"
   - Project 2: Name="Beta Project", Path=".", Status will be "Pending/Ready"
   - Project 3: Name="Gamma Project", Path=".", Status will be "Pending/Ready"

3. **Verify project list displays**
   - All 3 projects visible
   - Each shows: name, status badge, created date
   - List is paginated if > 10 projects

4. **Test status filter**
   - Click "Status" filter dropdown
   - Select "Ready"
   - Verify only ready projects shown
   - Select "All" to reset

5. **Test search by name**
   - Type "Alpha" in search box
   - Verify only "Alpha Project" shown
   - Clear search to see all projects

6. **Test project deletion**
   - Click delete icon on "Gamma Project"
   - Verify confirmation dialog appears
   - Click "Confirm Delete"
   - Verify project removed from list
   - Verify count updated

**Expected Results:**
- ✅ Project list displays all projects
- ✅ Filtering by status works correctly
- ✅ Search by name returns matching results
- ✅ Delete confirmation dialog appears
- ✅ Project removed after confirmation
- ✅ List updates in real-time

**MCP Tool Sequence:**
```
browser_navigate(url="http://localhost:3000/projects")
browser_snapshot()  # Verify project list page loads

# Create projects (repeat 3x with different names)
browser_click(element="Create button", ref="[data-testid='create-project']")
browser_fill_form(fields=[...])
browser_click(element="Submit", ref="[type='submit']")
browser_navigate_back()

# Test filtering
browser_click(element="Status filter", ref="[data-testid='status-filter']")
browser_select_option(element="Status dropdown", ref="select[name='status']", values=["ready"])
browser_snapshot()  # Verify only ready projects shown

# Test search
browser_type(element="Search box", ref="input[placeholder*='Search']", text="Alpha", slowly=false)
browser_wait_for(time=1)
browser_snapshot()  # Verify only "Alpha Project" visible

# Test delete
browser_click(element="Delete button for Gamma", ref="[data-testid='delete-gamma']")
browser_snapshot()  # Verify confirmation dialog appears
browser_click(element="Confirm button", ref="[data-testid='confirm-delete']")
browser_wait_for(textGone="Gamma Project", time=2)
browser_snapshot()  # Verify project removed from list
```

**Troubleshooting:**
- If filtering doesn't work: Check if status values match enum values
- If search is slow: May need debouncing in frontend
- If delete fails: Check backend logs for constraint errors

---

## Flow 3: Real-time Status Polling

**Description:** Verify that project status updates automatically every 2 seconds without manual refresh.

**Pre-conditions:**
- Backend and frontend running
- Git repository URL available for cloning (or use local path)

**Test Steps:**

1. **Navigate to homepage**
   - Open http://localhost:3000

2. **Create project with Git URL**
   - Click "Create New Project"
   - Fill form:
     - Name: "FastAPI Repo"
     - Source Type: "Git URL"
     - URL: "https://github.com/tiangolo/fastapi.git"
     - Branch: "master"
   - Click "Create Project"

3. **Monitor automatic status updates**
   - Observe status badge changes every ~2 seconds
   - Status progression: pending→cloning→scanning→analyzing→ready
   - No manual page refresh required

4. **Verify progress bar (if visible)**
   - Progress bar should show percentage
   - Percentage increases as analysis progresses
   - Progress bar disappears when status is "Ready"

5. **Verify polling stops at terminal state**
   - Once status reaches "Ready" or "Failed"
   - Status should stop changing
   - Network tab shows polling requests stopped

6. **Test browser behavior**
   - Navigate away from page
   - Come back to project page
   - Verify polling resumes if status not terminal

**Expected Results:**
- ✅ Status updates automatically every 2 seconds
- ✅ No page refresh needed
- ✅ Progress bar visible during analysis
- ✅ Polling stops when status = "Ready" or "Failed"
- ✅ No memory leaks from uncancelled intervals
- ✅ Polling resumes when navigating back

**MCP Tool Sequence:**
```
browser_navigate(url="http://localhost:3000")
browser_click(element="Create button", ref="[data-testid='create-project']")

browser_fill_form(fields=[
  {name: "Name", type: "textbox", ref: "[name='name']", value: "FastAPI Repo"},
  {name: "Source Type", type: "combobox", ref: "[name='source_type']", value: "Git URL"},
  {name: "URL", type: "textbox", ref: "[name='source']", value: "https://github.com/tiangolo/fastapi.git"}
])

browser_click(element="Submit", ref="[type='submit']")

# Monitor status changes over time
browser_wait_for(time=2)
browser_snapshot()  # Verify "Pending" badge visible

browser_wait_for(time=2)
browser_snapshot()  # Verify "Cloning" badge visible

browser_wait_for(time=5)
browser_snapshot()  # Verify "Scanning" badge visible

browser_wait_for(time=5)
browser_snapshot()  # Verify "Analyzing" badge visible

browser_wait_for(text="Ready", time=30)
browser_snapshot()  # Verify "Ready" badge and complete status

# Check network activity
browser_network_requests(includeStatic=false)
# Verify polling requests stopped after reaching "Ready"
```

**Troubleshooting:**
- If status doesn't update: Check useProjectStatus hook implementation
- If polling doesn't stop: Check cleanup in useEffect
- If too many requests: Verify 2-second interval is correct

---

## Flow 4: Dashboard Tab Switching

**Description:** Verify all dashboard tabs load correctly and state persists.

**Pre-conditions:**
- Backend and frontend running
- At least one project with status "Ready"

**Test Steps:**

1. **Navigate to existing project**
   - Go to project list: http://localhost:3000/projects
   - Click on any project with status "Ready"
   - Should land on project detail page

2. **Test Overview tab**
   - Overview tab should be active by default
   - Verify displays:
     - Project name and description
     - Status badge
     - Statistics (files, LOC, directories)
     - Language breakdown chart/list
     - Last analyzed timestamp

3. **Test Diagrams tab**
   - Click "Diagrams" tab
   - Verify tab becomes active
   - Verify content loads:
     - List of available diagrams (Architecture, Dependencies, etc.)
     - Or placeholder if no diagrams generated

4. **Test Files tab**
   - Click "Files" tab
   - Verify tab becomes active
   - Verify content loads:
     - File tree structure
     - Directories expandable/collapsible
     - File counts displayed

5. **Test Reports tab**
   - Click "Reports" tab
   - Verify tab becomes active
   - Verify content loads:
     - List of available reports
     - Or placeholder if no reports generated

6. **Test tab state persistence**
   - Click "Files" tab
   - Navigate away (e.g., go to project list)
   - Navigate back to project detail
   - Verify "Files" tab is still active (if implemented)

7. **Test keyboard navigation**
   - Use Tab key to navigate between tabs
   - Use Enter key to activate tab
   - Verify accessibility

**Expected Results:**
- ✅ All 4 tabs clickable and functional
- ✅ Each tab renders unique content
- ✅ Only one tab active at a time
- ✅ No console errors when switching tabs
- ✅ Loading states display correctly
- ✅ Tab state persists in Zustand store (optional)

**MCP Tool Sequence:**
```
browser_navigate(url="http://localhost:3000/projects")
browser_click(element="First ready project", ref="[data-status='ready']:first")
browser_snapshot()  # Verify Overview tab content displayed

# Test Diagrams tab
browser_click(element="Diagrams tab", ref="[role='tab'][name='Diagrams']")
browser_wait_for(time=1)
browser_snapshot()  # Verify Diagrams tab content loaded

# Test Files tab
browser_click(element="Files tab", ref="[role='tab'][name='Files']")
browser_wait_for(time=1)
browser_snapshot()  # Verify Files tab content loaded

# Test Reports tab
browser_click(element="Reports tab", ref="[role='tab'][name='Reports']")
browser_wait_for(time=1)
browser_snapshot()  # Verify Reports tab content loaded

# Test persistence
browser_navigate_back()
browser_wait_for(time=1)
browser_click(element="Same project", ref="[data-status='ready']:first")
# Check if Reports tab is still active (if persistence implemented)
browser_snapshot()  # Verify tab persistence
```

**Troubleshooting:**
- If tabs don't switch: Check event handlers in Tab component
- If content doesn't load: Check API calls in tab components
- If state doesn't persist: Check Zustand store implementation

---

## Flow 5: Manual Analysis Trigger

**Description:** Test the manual "Analyze" button that allows users to restart or trigger analysis on a project that is in a ready or failed state.

**Pre-conditions:**
- Backend and frontend running
- At least one project exists with status "ready" or "failed"

**Test Steps:**

1. **Navigate to project detail page**
   - Go to http://localhost:3000/projects
   - Click on a project with status "ready"
   - Should land on project detail page

2. **Verify "Analyze" button visible**
   - Button should be visible in top-right header
   - Button should be enabled (not disabled)
   - Button should show "Analyze" text with play icon

3. **Click "Analyze" button**
   - Click the "Analyze" button
   - Verify confirmation dialog appears

4. **Verify confirmation dialog content**
   - Dialog title: "Start Code Analysis?"
   - Dialog shows description of what will happen
   - If project has stats, shows file count
   - "Cancel" button visible
   - "Start Analysis" button visible

5. **Click "Start Analysis" button**
   - Click "Start Analysis" in dialog
   - Verify button shows loading state ("Starting...")
   - Verify button is disabled during submission

6. **Verify analysis starts**
   - Dialog should close automatically
   - Project status badge should change to "Pending"
   - Status should progress through phases (pending→cloning→scanning→analyzing)
   - Progress updates should happen automatically every 2 seconds

7. **Monitor status progression**
   - Verify status badge updates without page refresh
   - Verify final status reaches "Ready" or "Failed"
   - Verify "Analyze" button becomes enabled again when complete

8. **Test disabled state (already analyzing)**
   - While analysis is running, verify button shows "Analyzing..."
   - Verify button is disabled during active analysis
   - Verify clicking button during analysis has no effect

**Expected Results:**
- ✅ "Analyze" button visible on ready/failed projects
- ✅ Confirmation dialog displays correctly with project stats
- ✅ Analysis starts successfully after confirmation
- ✅ Project status updates from "Ready" → "Pending" → ... → "Ready"
- ✅ Status polling works during re-analysis
- ✅ Button is disabled during active analysis states
- ✅ No console errors or API failures
- ✅ Dialog closes on successful submission

**MCP Tool Sequence:**
```
# Navigate to a ready project
browser_navigate(url="http://localhost:3000/projects")
browser_snapshot()  # Verify project list

browser_click(element="Ready project", ref="[data-status='ready']:first")
browser_snapshot()  # Verify project detail page loads

# Verify Analyze button present
browser_snapshot()  # Check for "Analyze" button in header

# Click Analyze button
browser_click(element="Analyze button", ref="[data-testid='analyze-button']")
browser_wait_for(time=1)
browser_snapshot()  # Verify confirmation dialog appears

# Verify dialog content shows file count and description
browser_snapshot()  # Validate dialog structure

# Click Start Analysis
browser_click(element="Start Analysis button", ref="button:has-text('Start Analysis')")
browser_wait_for(time=1)
browser_snapshot()  # Verify dialog closes

# Monitor status changes
browser_wait_for(text="Pending", time=2)
browser_snapshot()  # Verify "Pending" badge visible

browser_wait_for(text="Cloning", time=5)
browser_snapshot()  # Verify "Cloning" badge visible

browser_wait_for(text="Analyzing", time=10)
browser_snapshot()  # Verify "Analyzing" badge visible

browser_wait_for(text="Ready", time=30)
browser_snapshot()  # Verify final "Ready" badge

# Verify button re-enabled
browser_snapshot()  # Check "Analyze" button is enabled again
```

**Troubleshooting:**
- If button is disabled: Check project status is "ready" or "failed"
- If dialog doesn't appear: Check browser console for React errors
- If analysis doesn't start: Check backend logs for API errors
- If status doesn't update: Check useProjectStatus polling hook
- If 409 error: Analysis already running, wait for completion

**Error Scenarios to Test:**

1. **409 Conflict - Analysis Already Running**
   - Start analysis on a project
   - Immediately try to start again (force=false)
   - Should receive 409 error
   - Dialog should show error alert

2. **404 Not Found - Project Deleted**
   - Navigate to non-existent project ID
   - Should show 404 error page

3. **Network Failure**
   - Disconnect network during analysis start
   - Should show error in dialog
   - Dialog should remain open with error message

---

## Flow 6: AI Chat with Streaming Responses

**Description:** Test the AI chat interface with real-time streaming responses and RAG context.

**Pre-conditions:**
- Backend and frontend running
- Ollama running with a model (e.g., `qwen2.5-coder:7b`)
- Qdrant vector database running
- At least one project with status "Ready" (embeddings generated)

**Test Steps:**

1. **Navigate to project with chat**
   - Go to http://localhost:3000/projects
   - Click on a project with status "Ready"
   - Verify project detail page loads

2. **Open chat panel**
   - Click chat button (bottom-right) or press Ctrl+K
   - Verify chat panel opens
   - Verify input field is focused

3. **Send a message**
   - Type: "How does authentication work in this codebase?"
   - Press Enter or click send button
   - Verify user message appears in chat

4. **Observe streaming response**
   - Verify "thinking" indicator appears
   - Verify tokens stream in real-time (not all at once)
   - Verify response completes with sources

5. **Verify sources display**
   - Verify source files are listed under response
   - Verify sources are clickable links
   - Verify line numbers shown for each source

6. **Test keyboard shortcuts**
   - Press Ctrl+K to toggle chat open/close
   - Press Escape to minimize chat
   - Press Shift+Enter for newline in message

7. **Test clear chat**
   - Click "Clear" button
   - Verify confirmation if messages exist
   - Verify chat history cleared

8. **Test error handling**
   - Stop Ollama service
   - Send a message
   - Verify error message displayed gracefully
   - Restart Ollama, verify recovery

**Expected Results:**
- ✅ Chat panel opens with Ctrl+K shortcut
- ✅ Messages sent and displayed correctly
- ✅ Streaming tokens appear in real-time
- ✅ Sources displayed with file paths and line numbers
- ✅ Keyboard navigation works (Ctrl+K, Escape, Shift+Enter)
- ✅ Clear chat works with confirmation
- ✅ Graceful error handling when LLM unavailable
- ✅ No console errors during streaming

**MCP Tool Sequence:**
```
browser_navigate(url="http://localhost:3000/projects")
browser_click(element="Ready project", ref="[data-status='ready']:first")
browser_snapshot()  # Verify project page loads

# Open chat with keyboard shortcut
browser_press_key(key="Control+k")
browser_wait_for(time=1)
browser_snapshot()  # Verify chat panel opens

# Type and send message
browser_type(
  element="Chat input",
  ref="[data-testid='chat-input']",
  text="How does authentication work?",
  slowly=false
)
browser_press_key(key="Enter")
browser_wait_for(time=2)
browser_snapshot()  # Verify user message appears

# Wait for streaming response
browser_wait_for(text="Sources", time=30)
browser_snapshot()  # Verify response with sources

# Test minimize
browser_press_key(key="Escape")
browser_snapshot()  # Verify chat minimized

# Test reopen
browser_press_key(key="Control+k")
browser_snapshot()  # Verify chat reopens with history
```

**Playwright Test File:** `frontend/tests/e2e/chat.spec.ts`

The chat E2E tests cover:
- Panel open/close with Ctrl+K shortcut
- Message input enable/disable states
- Send button visibility based on input
- Shift+Enter for newlines
- Clear chat functionality
- Mock data display when no real messages

**Troubleshooting:**
- If chat doesn't open: Check Ctrl+K event listener
- If streaming fails: Check Ollama is running, verify OLLAMA_BASE_URL
- If sources empty: Check Qdrant has embeddings, verify project was analyzed
- If response slow: Check Ollama model is loaded (first request loads model)

---

## Coverage Summary

These 6 E2E flows cover **80%+ of critical user functionality:**

| Flow | Coverage Area | % of Critical Paths |
|------|---------------|---------------------|
| Flow 1 | Project creation, analysis pipeline, dashboard | 25% |
| Flow 2 | Project management, filtering, deletion | 15% |
| Flow 3 | Real-time updates, polling mechanism | 10% |
| Flow 4 | Dashboard navigation, tab switching | 10% |
| Flow 5 | Manual analysis trigger, confirmation workflow | 10% |
| Flow 6 | AI chat with streaming, RAG, keyboard shortcuts | 15% |
| **Total** | | **85%** |

**Not Covered (Lower Priority):**
- Diagram generation details
- Report generation details
- Settings configuration
- Error recovery flows

---

## Test Execution Summary

**Last Executed:** [To be filled after execution]

**Results:**
- Flow 1: ⏳ Pending
- Flow 2: ⏳ Pending
- Flow 3: ⏳ Pending
- Flow 4: ⏳ Pending
- Flow 5: ⏳ Pending

**Environment:**
- Backend: v0.1.0
- Frontend: v0.1.0
- Browser: Chromium (MCP Playwright)
- OS: Linux WSL2

**Notes:**
- [To be added after test execution]

---

## Best Practices for E2E Testing

1. **Isolation:** Each test should be independent
2. **Cleanup:** Clear database between test runs
3. **Timing:** Use `wait_for` instead of fixed delays
4. **Assertions:** Verify both UI state and network responses
5. **YAML Snapshots:** Use `browser_snapshot()` to validate page structure at critical steps
6. **Error Handling:** Document common failure modes

---

## Running E2E Tests

### Manual Execution (MCP Playwright Tools)

**Steps:**
1. Start backend: `cd backend && uvicorn app.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Clear database: `curl -X DELETE http://localhost:8000/api/admin/database/clear`
4. Execute each flow using MCP Playwright tools
5. Use `browser_snapshot()` to validate page structure (returns YAML inline)
6. Verify expected results against YAML accessibility trees

**Advantages:**
- Zero configuration needed
- Visual feedback via Claude interface
- Perfect for exploratory testing
- Can capture screenshots (though blank in WSL)

### Automated Execution (Playwright Test Framework)

**Prerequisites:**
1. Ensure backend is running: `cd backend && uvicorn app.main:app --reload`
   - Or let Playwright auto-start frontend (configured in `playwright.config.ts`)
2. Install Playwright browsers (first time only): `cd frontend && npx playwright install`

**Running Tests:**

```bash
cd frontend

# Run all E2E tests (headless mode)
npm run test:e2e

# Run tests with UI mode (interactive, recommended for development)
npm run test:e2e:ui

# Run tests in headed mode (see browser)
npm run test:e2e:headed

# Run tests in debug mode (step through with Playwright Inspector)
npm run test:e2e:debug

# View last test report (opens HTML report in browser)
npm run test:e2e:report

# Run specific test file
npx playwright test tests/e2e/analyze-workflow.spec.ts

# Run tests matching a pattern
npx playwright test --grep "analyze"
```

**Test Output:**

Playwright will:
- Show progress in terminal
- Generate HTML report in `playwright-report/`
- Capture screenshots on failure in `test-results/`
- Record videos on failure (if configured)

**CI/CD Integration:**

The tests are ready for CI/CD. Example GitHub Actions workflow:

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install backend dependencies
        working-directory: backend
        run: pip install -r requirements.txt

      - name: Start backend server
        working-directory: backend
        run: |
          uvicorn app.main:app --host 0.0.0.0 --port 8000 &
          sleep 5

      - name: Install frontend dependencies
        working-directory: frontend
        run: npm ci

      - name: Install Playwright
        working-directory: frontend
        run: npx playwright install --with-deps

      - name: Run E2E tests
        working-directory: frontend
        run: npm run test:e2e

      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

**Automated Test Coverage:**

| Test File | Flows Covered | Test Count |
|-----------|---------------|------------|
| `project-creation.spec.ts` | Flow 1 | 4 tests |
| `analyze-workflow.spec.ts` | Flow 5 | 4 tests |
| `chat.spec.ts` | Flow 6 | 11 tests |
| **Total** | **3 of 6 flows** | **19 tests** |

**Future Automation:**
- Flow 2: Project list management
- Flow 3: Real-time status polling
- Flow 4: Dashboard tab switching

---

## Troubleshooting

### Backend Issues
- **Port already in use:** Kill process on port 8000: `lsof -ti:8000 | xargs kill -9`
- **Database locked:** Stop all backend processes, delete `backend/codecompass.db`, restart
- **Analysis fails:** Check file permissions on analyzed directory

### Frontend Issues
- **Port already in use:** Kill process on port 3000: `lsof -ti:3000 | xargs kill -9`
- **Blank page:** Check browser console for errors, verify API_URL in .env.local
- **API calls fail:** Verify backend is running, check CORS settings

### MCP Playwright Issues
- **Browser won't open:** Run `browser_install()` to install Chromium
- **Elements not found:** Use `browser_snapshot()` to inspect page structure
- **Timeouts:** Increase wait time, check network tab for slow requests

---

## Future Enhancements

1. **Automated E2E Suite:** Convert to Playwright test files
2. **Structural Regression:** Compare YAML accessibility trees between runs
3. **Performance Testing:** Measure load times, API response times
4. **Mobile Testing:** Test responsive design on mobile viewports
5. **CI/CD Integration:** Run E2E tests on every PR
