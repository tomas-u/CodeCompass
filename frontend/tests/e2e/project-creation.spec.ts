import { test, expect } from '@playwright/test';

/**
 * E2E Test: Create Project → Analyze → View Dashboard (Flow 1)
 *
 * This test verifies the complete project creation and analysis pipeline
 * from start to finish.
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

  test('should create project, analyze, and display dashboard', async ({ page }) => {
    // Step 1: Navigate to homepage and verify landing page loads
    await expect(page).toHaveTitle(/CodeCompass/i);

    // Step 2: Click "Create New Project" button
    const createButton = page.getByRole('button', { name: /create.*project/i });
    await expect(createButton).toBeVisible({ timeout: 10000 });
    await createButton.click();

    // Verify we're on the create project page or form is visible
    await expect(page.getByRole('heading', { name: /create.*project|new project/i })).toBeVisible({ timeout: 5000 });

    // Step 3: Fill project creation form
    const projectName = `E2E Test Project ${Date.now()}`;

    // Fill project name
    const nameInput = page.getByLabel(/project name|name/i);
    await nameInput.fill(projectName);

    // Select source type: "Local Path"
    const sourceTypeSelect = page.getByLabel(/source type|type/i);
    await sourceTypeSelect.click();
    const localPathOption = page.getByRole('option', { name: /local.*path/i });
    await localPathOption.click();

    // Fill path
    const pathInput = page.getByLabel(/path|directory/i);
    await pathInput.fill('/home/tomas/dev/streampower/codeCompass/backend');

    // Branch should default to "main" (no need to fill)

    // Step 4: Submit the form
    const submitButton = page.getByRole('button', { name: /create|submit/i });
    await submitButton.click();

    // Step 5: Verify redirect to project detail page
    await expect(page).toHaveURL(/\/projects\/[a-f0-9-]+/, { timeout: 10000 });

    // Step 6: Verify project name displayed in header
    await expect(page.getByRole('heading', { name: projectName })).toBeVisible();

    // Step 7: Monitor status progression
    // Initial status should be "Pending"
    const pendingBadge = page.locator('text=/pending/i').first();
    await expect(pendingBadge).toBeVisible({ timeout: 5000 });

    // Wait for "Cloning" status (may be brief)
    const cloningBadge = page.locator('text=/cloning/i').first();
    await expect(cloningBadge).toBeVisible({ timeout: 10000 });

    // Wait for "Scanning" status
    const scanningBadge = page.locator('text=/scanning/i').first();
    await expect(scanningBadge).toBeVisible({ timeout: 15000 });

    // Wait for "Analyzing" status
    const analyzingBadge = page.locator('text=/analyzing/i').first();
    await expect(analyzingBadge).toBeVisible({ timeout: 20000 });

    // Step 8: Wait for "Ready" status (final state)
    const readyBadge = page.locator('text=/ready/i').first();
    await expect(readyBadge).toBeVisible({ timeout: 60000 }); // 60s timeout for full analysis

    // Step 9: Verify dashboard displays stats
    // Check for files count (~104 files for backend)
    await expect(page.getByText(/files/i)).toBeVisible();

    // Check for lines of code
    await expect(page.getByText(/lines|loc/i)).toBeVisible();

    // Check for languages count
    await expect(page.getByText(/languages/i)).toBeVisible();

    // Step 10: Verify dashboard tabs are visible
    const overviewTab = page.getByRole('tab', { name: /overview/i });
    const diagramsTab = page.getByRole('tab', { name: /diagrams/i });
    const filesTab = page.getByRole('tab', { name: /files/i });
    const reportsTab = page.getByRole('tab', { name: /reports/i });

    await expect(overviewTab).toBeVisible();
    await expect(diagramsTab).toBeVisible();
    await expect(filesTab).toBeVisible();
    await expect(reportsTab).toBeVisible();

    // Step 11: Verify Overview tab is active by default
    await expect(overviewTab).toHaveAttribute('data-state', 'active');

    // Step 12: Click through each tab to verify content loads
    await diagramsTab.click();
    await expect(diagramsTab).toHaveAttribute('data-state', 'active');

    await filesTab.click();
    await expect(filesTab).toHaveAttribute('data-state', 'active');

    await reportsTab.click();
    await expect(reportsTab).toHaveAttribute('data-state', 'active');

    // Return to Overview tab
    await overviewTab.click();
    await expect(overviewTab).toHaveAttribute('data-state', 'active');
  });

  test('should validate required fields in project creation form', async ({ page }) => {
    // Navigate to create project page
    const createButton = page.getByRole('button', { name: /create.*project/i });
    await createButton.click();

    // Try to submit without filling required fields
    const submitButton = page.getByRole('button', { name: /create|submit/i });
    await submitButton.click();

    // Verify validation errors appear
    // HTML5 validation should prevent submission
    const nameInput = page.getByLabel(/project name|name/i);
    const isInvalid = await nameInput.evaluate((el: HTMLInputElement) => !el.validity.valid);
    expect(isInvalid).toBeTruthy();
  });

  test('should handle invalid repository path gracefully', async ({ page }) => {
    // Navigate to create project page
    const createButton = page.getByRole('button', { name: /create.*project/i });
    await createButton.click();

    // Fill form with invalid path
    const nameInput = page.getByLabel(/project name|name/i);
    await nameInput.fill('Invalid Path Test');

    const sourceTypeSelect = page.getByLabel(/source type|type/i);
    await sourceTypeSelect.click();
    const localPathOption = page.getByRole('option', { name: /local.*path/i });
    await localPathOption.click();

    const pathInput = page.getByLabel(/path|directory/i);
    await pathInput.fill('/nonexistent/path/to/nowhere');

    const submitButton = page.getByRole('button', { name: /create|submit/i });
    await submitButton.click();

    // Wait for redirect to project detail page
    await expect(page).toHaveURL(/\/projects\/[a-f0-9-]+/, { timeout: 10000 });

    // Verify status eventually becomes "Failed"
    const failedBadge = page.locator('text=/failed/i').first();
    await expect(failedBadge).toBeVisible({ timeout: 30000 });
  });

  test('should allow navigation back to project list', async ({ page }) => {
    // Navigate to projects page
    await page.goto('/projects');

    // Click on first project
    const firstProject = page.locator('[data-testid="project-item"]').first();
    await firstProject.click();

    // Verify we're on project detail page
    await expect(page).toHaveURL(/\/projects\/[a-f0-9-]+/);

    // Click back button
    const backButton = page.getByRole('button', { name: /back/i }).first();
    await backButton.click();

    // Verify we're back on projects list
    await expect(page).toHaveURL(/\/projects$/);
  });
});
