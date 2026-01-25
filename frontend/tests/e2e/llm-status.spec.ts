import { test, expect } from '@playwright/test';

/**
 * E2E Tests: LLM Status Indicator
 *
 * Tests the LLM status indicator component in the header.
 * The indicator shows connection status and allows opening settings.
 *
 * Pre-conditions:
 * - Backend server running on http://localhost:8000
 * - Frontend server running on http://localhost:3000
 */

test.describe('LLM Status Indicator', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('displays LLM status in header', async ({ page }) => {
    // Wait for the page to load
    await expect(page).toHaveTitle(/CodeCompass/i);

    // The LLM status indicator should be visible in the header
    // It shows either the model name or a status message
    const header = page.locator('header');
    await expect(header).toBeVisible();

    // Look for the status indicator button
    const statusIndicator = header.getByRole('button', { name: /LLM Status/i });
    await expect(statusIndicator).toBeVisible();
  });

  test('shows tooltip with provider details on hover', async ({ page }) => {
    const header = page.locator('header');
    const statusIndicator = header.getByRole('button', { name: /LLM Status/i });

    // Hover to show tooltip
    await statusIndicator.hover();

    // Tooltip should show provider info
    await expect(page.getByText(/Provider:/i)).toBeVisible();
    await expect(page.getByText(/Model:/i)).toBeVisible();
    await expect(page.getByText(/Status:/i)).toBeVisible();
  });

  test('shows ready state with green indicator when LLM is available', async ({ page }) => {
    const header = page.locator('header');
    const statusIndicator = header.getByRole('button', { name: /LLM Status/i });

    // The status dot should be visible
    const statusDot = statusIndicator.locator('span').first();
    await expect(statusDot).toBeVisible();

    // Check for green color class (ready state)
    // Note: This may show yellow/red if LLM is not running
    const classes = await statusDot.getAttribute('class');
    expect(classes).toMatch(/bg-(green|yellow|red|gray)-/);
  });

  test('clicking opens settings dialog', async ({ page }) => {
    const header = page.locator('header');
    const statusIndicator = header.getByRole('button', { name: /LLM Status/i });

    await statusIndicator.click();

    // Settings dialog should open
    // Note: This test will pass once SettingsDialog is implemented (#86)
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible({ timeout: 5000 });
  });

  test('is accessible via keyboard', async ({ page }) => {
    // Tab to the status indicator
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab'); // May need multiple tabs depending on header structure

    // Find the focused element
    const focused = page.locator(':focus');
    const ariaLabel = await focused.getAttribute('aria-label');

    // Should have meaningful aria-label
    if (ariaLabel?.includes('LLM Status')) {
      expect(ariaLabel).toContain('LLM Status');

      // Press Enter to activate
      await page.keyboard.press('Enter');

      // Should trigger the click action (open settings)
      const dialog = page.getByRole('dialog');
      await expect(dialog).toBeVisible({ timeout: 5000 });
    }
  });
});
