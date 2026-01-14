# End-to-End Test Scenarios

This document describes 4 critical E2E test flows for CodeCompass, executed using MCP Playwright tools for zero-config browser automation.

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

## Coverage Summary

These 4 E2E flows cover **60%+ of critical user functionality:**

| Flow | Coverage Area | % of Critical Paths |
|------|---------------|---------------------|
| Flow 1 | Project creation, analysis pipeline, dashboard | 25% |
| Flow 2 | Project management, filtering, deletion | 15% |
| Flow 3 | Real-time updates, polling mechanism | 10% |
| Flow 4 | Dashboard navigation, tab switching | 10% |
| **Total** | | **60%** |

**Not Covered (Lower Priority):**
- Chat/Q&A functionality
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

**Manual Execution:**
1. Start backend: `cd backend && uvicorn app.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Clear database: `curl -X DELETE http://localhost:8000/api/admin/database/clear`
4. Execute each flow using MCP Playwright tools
5. Use `browser_snapshot()` to validate page structure (returns YAML inline)
6. Verify expected results against YAML accessibility trees

**Automation (Future):**
- Install Playwright locally: `npm install -D @playwright/test`
- Create test files in `frontend/tests/e2e/`
- Run: `npx playwright test`
- Configure CI/CD pipeline

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
