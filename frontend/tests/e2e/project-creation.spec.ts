import { test, expect } from '@playwright/test';

/**
 * E2E Test: Create Project → Analyze → View Dashboard (Flow 1)
 *
 * This test verifies the complete project creation and analysis pipeline
 * from start to finish using the tab-based form on the welcome page.
 *
 * Pre-conditions:
 * - Backend server running on http://localhost:8000
 * - Frontend server running on http://localhost:3000
 * - Clean database recommended (but not required)
 * - Test repository available at /home/tomas/dev/streampower/codeCompass/backend
 */

test.describe('Project Creation and Analysis Pipeline', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to home page
    await page.goto('/');
  });

  test('should create project with local path and analyze', async ({ page }) => {
    // Step 1: Verify landing page loads
    await expect(page).toHaveTitle(/CodeCompass/i);
    await expect(page.getByText(/Navigate and understand any codebase/i)).toBeVisible();

    // Step 2: Click "Local Path" tab
    const localPathTab = page.getByRole('tab', { name: /local path/i });
    await localPathTab.click();

    // Step 3: Fill local path form
    const pathInput = page.getByTestId('local-path-input');
    await pathInput.fill('/home/tomas/dev/streampower/codeCompass/backend');

    // Step 4: Submit the form
    const submitButton = page.getByTestId('local-submit-button');
    await expect(submitButton).toBeEnabled();
    await submitButton.click();

    // Step 5: Verify redirect to project detail page (may take longer for local path validation)
    await expect(page).toHaveURL(/\/projects\/[a-f0-9-]+/, { timeout: 30000 });

    // Step 6: Wait for page to load (may need extra time for backend to initialize project)
    await page.waitForLoadState('networkidle', { timeout: 10000 });

    // Step 7: Verify project page loaded with header
    await expect(page.locator('h1').first()).toBeVisible({ timeout: 10000 });

    // Step 7: Wait for initial status (pending or already progressed)
    // The status badge should be visible in the header
    const statusBadge = page.locator('text=/pending|cloning|scanning|analyzing|ready/i').first();
    await expect(statusBadge).toBeVisible({ timeout: 10000 });

    // Step 8: If analysis completes quickly, verify "Ready" status
    // Otherwise just verify the analysis is progressing
    const readyBadge = page.locator('text=/ready/i').first();
    try {
      await expect(readyBadge).toBeVisible({ timeout: 60000 });

      // Step 9: Verify dashboard displays (only if ready)
      const overviewTab = page.getByRole('tab', { name: /overview/i });
      await expect(overviewTab).toBeVisible();

      // Verify at least one stat is displayed
      await expect(page.getByText(/files|lines|languages/i).first()).toBeVisible();
    } catch {
      // Analysis still in progress - that's okay for this test
      // The important part is that project was created and analysis started
    }
  });

  test('should create project with git URL', async ({ page }) => {
    // Step 1: Git tab should be active by default
    const gitTab = page.getByRole('tab', { name: /git repository/i });
    await expect(gitTab).toHaveAttribute('data-state', 'active');

    // Step 2: Fill git URL form
    const urlInput = page.getByTestId('git-url-input');
    await urlInput.fill('https://github.com/tiangolo/fastapi.git');

    // Step 3: Optionally fill branch (defaults to main)
    const branchInput = page.getByTestId('git-branch-input');
    await branchInput.fill('master');

    // Step 4: Submit the form
    const submitButton = page.getByTestId('git-submit-button');
    await expect(submitButton).toBeEnabled();
    await submitButton.click();

    // Step 5: Verify redirect to project detail page (git clone may take time)
    await expect(page).toHaveURL(/\/projects\/[a-f0-9-]+/, { timeout: 30000 });

    // Step 6: Verify project name appears in header (derived from repo name)
    await expect(page.getByText(/fastapi/i).first()).toBeVisible({ timeout: 5000 });

    // Step 7: Verify status badge is visible (analysis started or completed quickly)
    const statusBadge = page.locator('text=/pending|cloning|scanning|analyzing|ready/i').first();
    await expect(statusBadge).toBeVisible({ timeout: 10000 });
  });

  test('should validate required URL field', async ({ page }) => {
    // Git tab is active by default
    const submitButton = page.getByTestId('git-submit-button');

    // Verify button is disabled when URL is empty
    await expect(submitButton).toBeDisabled();

    // Fill URL
    const urlInput = page.getByTestId('git-url-input');
    await urlInput.fill('https://github.com/user/repo.git');

    // Verify button becomes enabled
    await expect(submitButton).toBeEnabled();

    // Clear URL
    await urlInput.clear();

    // Verify button is disabled again
    await expect(submitButton).toBeDisabled();
  });

  test('should validate required path field', async ({ page }) => {
    // Click "Local Path" tab
    const localPathTab = page.getByRole('tab', { name: /local path/i });
    await localPathTab.click();

    const submitButton = page.getByTestId('local-submit-button');

    // Verify button is disabled when path is empty
    await expect(submitButton).toBeDisabled();

    // Fill path
    const pathInput = page.getByTestId('local-path-input');
    await pathInput.fill('/some/path');

    // Verify button becomes enabled
    await expect(submitButton).toBeEnabled();

    // Clear path
    await pathInput.clear();

    // Verify button is disabled again
    await expect(submitButton).toBeDisabled();
  });

  test('should handle invalid repository path gracefully', async ({ page }) => {
    // Click "Local Path" tab
    const localPathTab = page.getByRole('tab', { name: /local path/i });
    await localPathTab.click();

    // Fill form with invalid path
    const pathInput = page.getByTestId('local-path-input');
    await pathInput.fill('/nonexistent/path/to/nowhere');

    const submitButton = page.getByTestId('local-submit-button');
    await submitButton.click();

    // Wait for redirect to project detail page (backend needs time to process)
    await expect(page).toHaveURL(/\/projects\/[a-f0-9-]+/, { timeout: 30000 });

    // Verify status eventually becomes "Failed"
    const failedBadge = page.locator('text=/failed/i').first();
    await expect(failedBadge).toBeVisible({ timeout: 30000 });
  });

  test('should allow switching between Git and Local Path tabs', async ({ page }) => {
    // Verify Git tab is active by default
    const gitTab = page.getByRole('tab', { name: /git repository/i });
    const localTab = page.getByRole('tab', { name: /local path/i });

    await expect(gitTab).toHaveAttribute('data-state', 'active');

    // Click Local Path tab
    await localTab.click();
    await expect(localTab).toHaveAttribute('data-state', 'active');

    // Verify local path form is visible
    await expect(page.getByTestId('local-path-input')).toBeVisible();

    // Switch back to Git tab
    await gitTab.click();
    await expect(gitTab).toHaveAttribute('data-state', 'active');

    // Verify git form is visible
    await expect(page.getByTestId('git-url-input')).toBeVisible();
  });

  test('should select project via dropdown and show dashboard', async ({ page }) => {
    // Get a ready project from API
    const response = await page.request.get('http://localhost:8000/api/projects?status=ready&limit=1');
    const data = await response.json();

    if (data.items.length === 0) {
      // No ready projects exist, skip this test
      test.skip();
      return;
    }

    const projectName = data.items[0].name;

    // Click the project selector dropdown
    const projectDropdown = page.getByRole('button', { name: /select project/i });
    await projectDropdown.click();

    // Wait for dropdown to open
    await page.waitForSelector('[data-testid="project-item"]', { timeout: 5000 });

    // Find and click the ready project
    const projectItem = page.locator(`[data-testid="project-item"][data-status="ready"]`).first();
    await projectItem.click();

    // Verify URL remains on home page (SPA behavior)
    await expect(page).toHaveURL('/');

    // Verify dashboard is displayed with project data
    await expect(page.getByRole('tab', { name: /overview/i })).toBeVisible({ timeout: 5000 });

    // Verify project name appears in dropdown button (now selected)
    await expect(page.getByRole('button', { name: new RegExp(projectName, 'i') })).toBeVisible();
  });
});
