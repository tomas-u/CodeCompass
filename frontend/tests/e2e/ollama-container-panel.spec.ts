import { test, expect } from '@playwright/test';

/**
 * E2E Tests: Ollama Container Panel
 *
 * Tests the Container Ollama configuration panel, including
 * hardware info display, model selection, and model pull.
 *
 * Pre-conditions:
 * - Backend server running on http://localhost:8000
 * - Frontend server running on http://localhost:3000
 * - Ollama service available (for model list/pull tests)
 *
 * NOTE: These tests are skipped until issue #92 (Header integration) is complete.
 */

test.describe.skip('Ollama Container Panel', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/CodeCompass/i);

    // Open settings dialog
    const settingsButton = page.locator('header').getByRole('button', { name: /settings/i });
    await settingsButton.click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // Ensure LLM tab is active and Container Ollama is selected (default)
    await expect(dialog.getByRole('tab', { name: 'LLM' })).toHaveAttribute('data-state', 'active');
  });

  test('displays hardware info card', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    // Hardware card should be visible
    await expect(dialog.getByText(/hardware detected/i)).toBeVisible();

    // Should show GPU, RAM, and recommendation info (or loading skeleton)
    // Wait for loading to complete
    await expect(dialog.getByText(/GPU:|Not detected/i)).toBeVisible({ timeout: 10000 });
  });

  test('displays hardware info fields when loaded', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    // Wait for hardware info to load
    await expect(dialog.getByText(/hardware detected/i)).toBeVisible();

    // Should show RAM info
    await expect(dialog.getByText(/RAM:/i)).toBeVisible({ timeout: 10000 });

    // Should show recommendation
    await expect(dialog.getByText(/recommended/i)).toBeVisible();

    // Should show inference mode
    await expect(dialog.getByText(/inference/i)).toBeVisible();
  });

  test('displays available models section', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    // Should show models section
    await expect(dialog.getByText(/available models/i)).toBeVisible();

    // Should have a refresh button
    await expect(dialog.getByRole('button', { name: /refresh/i })).toBeVisible();
  });

  test('shows model list or empty state', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    // Wait for models to load (either list or empty state)
    await expect(
      dialog.getByText(/no models installed|select a model/i).or(
        dialog.getByRole('radiogroup', { name: /select a model/i })
      )
    ).toBeVisible({ timeout: 10000 });
  });

  test('model selection works via radio buttons', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    // Wait for model list (skip if no models)
    const modelRadioGroup = dialog.getByRole('radiogroup', { name: /select a model/i });
    const isVisible = await modelRadioGroup.isVisible().catch(() => false);

    if (isVisible) {
      // Click first model
      const firstModel = modelRadioGroup.getByRole('radio').first();
      await firstModel.click();
      await expect(firstModel).toBeChecked();
    }
  });

  test('displays pull new model section', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    // Should show pull section
    await expect(dialog.getByText(/pull new model/i)).toBeVisible();

    // Should have input and pull button
    await expect(dialog.getByRole('textbox', { name: /model name/i })).toBeVisible();
    await expect(dialog.getByRole('button', { name: /pull/i })).toBeVisible();
  });

  test('pull button is disabled when input is empty', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    const pullButton = dialog.getByRole('button', { name: /pull/i });
    await expect(pullButton).toBeDisabled();
  });

  test('pull button is enabled when model name is entered', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    const input = dialog.getByRole('textbox', { name: /model name/i });
    await input.fill('phi3:latest');

    const pullButton = dialog.getByRole('button', { name: /pull/i });
    await expect(pullButton).toBeEnabled();
  });

  test('refresh button reloads model list', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    // Wait for initial load
    await expect(dialog.getByText(/available models/i)).toBeVisible();

    // Click refresh
    const refreshButton = dialog.getByRole('button', { name: /refresh/i });
    await refreshButton.click();

    // Refresh icon should animate (spin class)
    // The models section should still be visible after refresh
    await expect(dialog.getByText(/available models/i)).toBeVisible();
  });

  test('each model shows delete button', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    // Wait for model list
    const modelRadioGroup = dialog.getByRole('radiogroup', { name: /select a model/i });
    const isVisible = await modelRadioGroup.isVisible().catch(() => false);

    if (isVisible) {
      // Each model should have a delete button
      const deleteButtons = dialog.getByRole('button', { name: /delete/i });
      const count = await deleteButtons.count();
      expect(count).toBeGreaterThan(0);
    }
  });
});
