import { test, expect } from '@playwright/test';

/**
 * E2E Tests: Settings Dialog
 *
 * Tests the Settings Dialog component with tabbed interface.
 * The dialog is opened from the header settings button or LLM status indicator.
 *
 * Pre-conditions:
 * - Backend server running on http://localhost:8000
 * - Frontend server running on http://localhost:3000
 *
 * NOTE: These tests are skipped until issue #92 (Header integration) is complete.
 * The tests require the Settings button in the header to have an onClick handler
 * and accessible name, which will be added in #92.
 */

test.describe.skip('Settings Dialog', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/CodeCompass/i);
  });

  test('opens settings dialog from header', async ({ page }) => {
    // Click the settings button in the header
    const settingsButton = page.locator('header').getByRole('button', { name: /settings/i });
    await settingsButton.click();

    // Dialog should be visible
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // Should have "Settings" title
    await expect(dialog.getByRole('heading', { name: 'Settings' })).toBeVisible();
  });

  test('has three tabs: LLM, Embedding, Analysis', async ({ page }) => {
    // Open settings dialog
    const settingsButton = page.locator('header').getByRole('button', { name: /settings/i });
    await settingsButton.click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // Check all three tabs are present
    await expect(dialog.getByRole('tab', { name: 'LLM' })).toBeVisible();
    await expect(dialog.getByRole('tab', { name: 'Embedding' })).toBeVisible();
    await expect(dialog.getByRole('tab', { name: 'Analysis' })).toBeVisible();
  });

  test('switches between tabs', async ({ page }) => {
    // Open settings dialog
    const settingsButton = page.locator('header').getByRole('button', { name: /settings/i });
    await settingsButton.click();

    const dialog = page.getByRole('dialog');

    // LLM tab should be active by default
    const llmTab = dialog.getByRole('tab', { name: 'LLM' });
    await expect(llmTab).toHaveAttribute('data-state', 'active');

    // Click Embedding tab
    const embeddingTab = dialog.getByRole('tab', { name: 'Embedding' });
    await embeddingTab.click();
    await expect(embeddingTab).toHaveAttribute('data-state', 'active');
    await expect(llmTab).toHaveAttribute('data-state', 'inactive');

    // Click Analysis tab
    const analysisTab = dialog.getByRole('tab', { name: 'Analysis' });
    await analysisTab.click();
    await expect(analysisTab).toHaveAttribute('data-state', 'active');
  });

  test('has footer buttons: Cancel, Test Connection, Save', async ({ page }) => {
    // Open settings dialog
    const settingsButton = page.locator('header').getByRole('button', { name: /settings/i });
    await settingsButton.click();

    const dialog = page.getByRole('dialog');

    // Check footer buttons
    await expect(dialog.getByRole('button', { name: 'Cancel' })).toBeVisible();
    await expect(dialog.getByRole('button', { name: 'Test Connection' })).toBeVisible();
    await expect(dialog.getByRole('button', { name: 'Save' })).toBeVisible();
  });

  test('Cancel button closes dialog', async ({ page }) => {
    // Open settings dialog
    const settingsButton = page.locator('header').getByRole('button', { name: /settings/i });
    await settingsButton.click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // Click Cancel
    await dialog.getByRole('button', { name: 'Cancel' }).click();

    // Dialog should be closed
    await expect(dialog).not.toBeVisible();
  });

  test('X button closes dialog', async ({ page }) => {
    // Open settings dialog
    const settingsButton = page.locator('header').getByRole('button', { name: /settings/i });
    await settingsButton.click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // Click the X close button
    await dialog.getByRole('button', { name: 'Close' }).click();

    // Dialog should be closed
    await expect(dialog).not.toBeVisible();
  });

  test('ESC key closes dialog', async ({ page }) => {
    // Open settings dialog
    const settingsButton = page.locator('header').getByRole('button', { name: /settings/i });
    await settingsButton.click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // Press ESC
    await page.keyboard.press('Escape');

    // Dialog should be closed
    await expect(dialog).not.toBeVisible();
  });

  test('Test Connection button shows loading state', async ({ page }) => {
    // Open settings dialog
    const settingsButton = page.locator('header').getByRole('button', { name: /settings/i });
    await settingsButton.click();

    const dialog = page.getByRole('dialog');
    const testButton = dialog.getByRole('button', { name: 'Test Connection' });

    // Click Test Connection
    await testButton.click();

    // Button should show loading (spinner icon appears)
    // Note: The button text should still be visible
    await expect(testButton).toBeDisabled();
  });

  test('Save button shows loading state', async ({ page }) => {
    // Open settings dialog
    const settingsButton = page.locator('header').getByRole('button', { name: /settings/i });
    await settingsButton.click();

    const dialog = page.getByRole('dialog');
    const saveButton = dialog.getByRole('button', { name: 'Save' });

    // Click Save
    await saveButton.click();

    // Button should show loading state
    await expect(saveButton).toBeDisabled();

    // Dialog should close after save completes
    await expect(dialog).not.toBeVisible({ timeout: 3000 });
  });

  test('dialog is accessible', async ({ page }) => {
    // Open settings dialog
    const settingsButton = page.locator('header').getByRole('button', { name: /settings/i });
    await settingsButton.click();

    const dialog = page.getByRole('dialog');

    // Dialog should have proper ARIA attributes
    await expect(dialog).toHaveAttribute('role', 'dialog');

    // Should be able to navigate with Tab key
    await page.keyboard.press('Tab');
    const focused = page.locator(':focus');
    await expect(focused).toBeVisible();
  });
});
