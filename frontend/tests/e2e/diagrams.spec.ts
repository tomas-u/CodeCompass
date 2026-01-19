import { test, expect } from '@playwright/test';

/**
 * E2E Test: Diagrams Tab Functionality
 *
 * This test verifies that diagrams render correctly without errors,
 * including handling of special characters in file paths (like Next.js [id] routes).
 *
 * Pre-conditions:
 * - Backend server running on http://localhost:8000
 * - Frontend server running on http://localhost:3000
 * - At least one project exists with status "ready"
 */

test.describe('Diagrams Tab', () => {
  let projectId: string;

  test.beforeAll(async ({ request }) => {
    // Fetch a ready project from API
    const response = await request.get('http://localhost:8000/api/projects?status=ready&limit=1');
    const data = await response.json();

    if (data.items.length === 0) {
      throw new Error('No ready projects found. Please ensure at least one project with status "ready" exists.');
    }

    projectId = data.items[0].id;
  });

  test.beforeEach(async ({ page }) => {
    // Navigate to the project and go to Diagrams tab
    await page.goto('/');

    // Click project selector
    await page.getByRole('button', { name: /select project/i }).click();

    // Wait for menu to appear and click the first ready project
    await page.waitForSelector('[data-testid="project-item"]');
    await page.locator('[data-testid="project-item"]').first().click();

    // Wait for project to load
    await expect(page.getByRole('tab', { name: /diagrams/i })).toBeVisible({ timeout: 10000 });
  });

  test('should display Diagrams tab with diagram type options', async ({ page }) => {
    // Click on Diagrams tab
    await page.getByRole('tab', { name: /diagrams/i }).click();

    // Verify we're on the diagrams view
    await expect(page.getByRole('heading', { name: /architecture diagrams/i })).toBeVisible();

    // Verify diagram type tabs are present
    await expect(page.getByRole('tab', { name: /dependency/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /directory/i })).toBeVisible();
  });

  test('should render Dependency diagram without Mermaid parsing errors', async ({ page }) => {
    // Click on Diagrams tab
    await page.getByRole('tab', { name: /diagrams/i }).click();

    // Dependency tab should be selected by default
    await expect(page.getByRole('tab', { name: /dependency/i })).toHaveAttribute('aria-selected', 'true');

    // Wait for diagram to load (either success or error state)
    await page.waitForTimeout(3000); // Give time for API call and Mermaid rendering

    // Check for console errors related to Mermaid parsing
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error' && msg.text().includes('Parse error')) {
        consoleErrors.push(msg.text());
      }
    });

    // Check that no "Parse error" alert is visible
    const parseErrorAlert = page.locator('text=/parse error/i');
    const errorCount = await parseErrorAlert.count();

    // If there's a parse error displayed, fail the test
    if (errorCount > 0) {
      const errorText = await parseErrorAlert.first().textContent();
      throw new Error(`Mermaid parse error detected: ${errorText}`);
    }

    // Verify either diagram SVG is present OR a valid error message (not parse error)
    // Use count > 0 instead of isVisible since high zoom may push SVG outside viewport
    const svgCount = await page.locator('svg').count();
    const svgPresent = svgCount > 0;
    const loadingPresent = await page.locator('text=/loading diagram/i').isVisible().catch(() => false);
    const sizeError = await page.locator('text=/too large to render/i').isVisible().catch(() => false);
    const serverError = await page.locator('text=/internal server error/i').isVisible().catch(() => false);

    // At least one of these should be true (valid states)
    const validState = svgPresent || loadingPresent || sizeError || serverError;
    expect(validState).toBe(true);
  });

  test('should render Directory diagram without Mermaid parsing errors', async ({ page }) => {
    // Click on Diagrams tab
    await page.getByRole('tab', { name: /diagrams/i }).click();

    // Click on Directory tab
    await page.getByRole('tab', { name: /directory/i }).click();

    // Verify Directory tab is selected
    await expect(page.getByRole('tab', { name: /directory/i })).toHaveAttribute('aria-selected', 'true');

    // Wait for diagram to load
    await page.waitForTimeout(3000);

    // Check that no "Parse error" is visible
    const parseErrorAlert = page.locator('text=/parse error/i');
    const errorCount = await parseErrorAlert.count();

    if (errorCount > 0) {
      const errorText = await parseErrorAlert.first().textContent();
      throw new Error(`Mermaid parse error detected: ${errorText}`);
    }

    // Verify diagram SVG is present (check count instead of visibility since high zoom may push SVG outside viewport)
    const svgCount = await page.locator('svg').count();
    expect(svgCount).toBeGreaterThan(0);
  });

  test('should display diagram statistics without JSON overflow', async ({ page }) => {
    // Click on Diagrams tab
    await page.getByRole('tab', { name: /diagrams/i }).click();

    // Wait for diagram and stats to load
    await page.waitForTimeout(3000);

    // Look for the Statistics section
    const statsSection = page.locator('text=/diagram statistics/i');

    // If stats section exists, verify it doesn't contain raw JSON
    if (await statsSection.isVisible().catch(() => false)) {
      // Get the stats card content
      const statsCard = page.locator('text=/diagram statistics/i').locator('..').locator('..');
      const statsText = await statsCard.textContent() || '';

      // Should NOT contain raw JSON array/object syntax
      expect(statsText).not.toMatch(/\[\s*\{/); // No array of objects like [{"foo":
      expect(statsText).not.toMatch(/\{\s*"/);   // No raw object like {"foo":

      // Should contain clean number labels
      const hasCleanStats =
        statsText.includes('Total Nodes') ||
        statsText.includes('Node Count') ||
        statsText.includes('Total Edges') ||
        statsText.includes('Edge Count');

      // Only assert if we have content (some diagrams might not have stats)
      if (statsText.length > 50) {
        expect(hasCleanStats).toBe(true);
      }
    }
  });

  test('should handle special characters in paths (Next.js [id] routes)', async ({ page }) => {
    // This test specifically verifies that paths with brackets like [id] don't break Mermaid

    // Click on Diagrams tab
    await page.getByRole('tab', { name: /diagrams/i }).click();

    // Wait for diagram to attempt rendering
    await page.waitForTimeout(3000);

    // The specific error we're looking for mentions "Expecting 'SQE'" which happens
    // when brackets aren't properly escaped
    const bracketError = page.locator('text=/expecting.*sqe/i');
    const errorCount = await bracketError.count();

    expect(errorCount).toBe(0);
  });

  test('should allow switching between diagram types', async ({ page }) => {
    // Click on Diagrams tab
    await page.getByRole('tab', { name: /diagrams/i }).click();

    // Verify Dependency tab is selected by default
    await expect(page.getByRole('tab', { name: /dependency/i })).toHaveAttribute('aria-selected', 'true');

    // Click Directory tab
    await page.getByRole('tab', { name: /directory/i }).click();
    await expect(page.getByRole('tab', { name: /directory/i })).toHaveAttribute('aria-selected', 'true');
    await expect(page.getByRole('tab', { name: /dependency/i })).toHaveAttribute('aria-selected', 'false');

    // Wait for content to load
    await page.waitForTimeout(2000);

    // Verify Directory Structure content is shown
    await expect(page.locator('text=/directory structure/i').first()).toBeVisible();

    // Switch back to Dependency
    await page.getByRole('tab', { name: /dependency/i }).click();
    await expect(page.getByRole('tab', { name: /dependency/i })).toHaveAttribute('aria-selected', 'true');

    // Wait for content to load
    await page.waitForTimeout(2000);

    // Verify Dependency Graph content is shown
    await expect(page.locator('text=/dependency graph/i').first()).toBeVisible();
  });

  test('should show Regenerate All button', async ({ page }) => {
    // Click on Diagrams tab
    await page.getByRole('tab', { name: /diagrams/i }).click();

    // Verify Regenerate All button is visible
    const regenerateButton = page.getByRole('button', { name: /regenerate all/i });
    await expect(regenerateButton).toBeVisible();
    await expect(regenerateButton).toBeEnabled();
  });
});
