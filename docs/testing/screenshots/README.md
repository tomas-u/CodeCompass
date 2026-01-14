# E2E Test Snapshots Directory

This directory is reserved for optional YAML accessibility tree snapshots from E2E test execution.

## Important Note

**WSL users:** PNG screenshots will render as blank/white images due to GPU limitations in headless Chromium. This cannot be fixed with xvfb or virtual display solutions.

**Recommended approach:**
- Use `browser_snapshot()` WITHOUT filename parameter to get inline YAML output
- YAML accessibility trees provide complete structural validation
- Only save to files if you need persistent snapshot records

## If Saving YAML Snapshots

Format: `flowX-YY-description.md`

Example:
- flow1-01-homepage.md
- flow1-02-create-form.md
- flow1-03-pending.md
- flow2-01-project-list.md
- flow3-01-status-pending.md
- flow4-01-overview-tab.md
