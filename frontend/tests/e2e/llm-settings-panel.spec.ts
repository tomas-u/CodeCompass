import { test, expect } from '@playwright/test';

/**
 * E2E Tests: LLM Settings Panel
 *
 * Tests the LLM Settings Panel component with provider type selection.
 * The panel is displayed in the Settings Dialog's LLM tab.
 *
 * Pre-conditions:
 * - Backend server running on http://localhost:8000
 * - Frontend server running on http://localhost:3000
 *
 * NOTE: These tests are skipped until issue #92 (Header integration) is complete.
 * The tests require the Settings button in the header to open the Settings Dialog.
 */

test.describe.skip('LLM Settings Panel', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/CodeCompass/i);

    // Open settings dialog
    const settingsButton = page.locator('header').getByRole('button', { name: /settings/i });
    await settingsButton.click();

    // Wait for dialog to be visible
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();
  });

  test('displays provider type selector with 4 options', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    // Should have a radio group for provider selection
    const radioGroup = dialog.getByRole('radiogroup', { name: /provider type/i });
    await expect(radioGroup).toBeVisible();

    // Should have 4 radio options
    const radioItems = dialog.getByRole('radio');
    await expect(radioItems).toHaveCount(4);

    // Check each option is present
    await expect(dialog.getByRole('radio', { name: /container ollama/i })).toBeVisible();
    await expect(dialog.getByRole('radio', { name: /external local llm/i })).toBeVisible();
    await expect(dialog.getByRole('radio', { name: /openrouter.*your api key/i })).toBeVisible();
    await expect(dialog.getByRole('radio', { name: /openrouter.*managed/i })).toBeVisible();
  });

  test('Container Ollama is selected by default', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    // Container Ollama should be checked by default
    const containerOption = dialog.getByRole('radio', { name: /container ollama/i });
    await expect(containerOption).toBeChecked();
  });

  test('clicking provider option selects it', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    // Click External LLM option
    const externalOption = dialog.getByRole('radio', { name: /external local llm/i });
    await externalOption.click();
    await expect(externalOption).toBeChecked();

    // Container should no longer be checked
    const containerOption = dialog.getByRole('radio', { name: /container ollama/i });
    await expect(containerOption).not.toBeChecked();
  });

  test('shows Container Ollama panel when selected', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    // Container Ollama should be selected by default
    // Check for container panel content
    await expect(dialog.getByText(/container ollama configuration/i)).toBeVisible();
  });

  test('shows External LLM panel when selected', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    // Select External LLM
    const externalOption = dialog.getByRole('radio', { name: /external local llm/i });
    await externalOption.click();

    // Check for external panel content
    await expect(dialog.getByText(/external llm configuration/i)).toBeVisible();
  });

  test('shows OpenRouter BYOK panel when selected', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    // Select OpenRouter BYOK
    const byokOption = dialog.getByRole('radio', { name: /openrouter.*your api key/i });
    await byokOption.click();

    // Check for OpenRouter BYOK panel content
    await expect(dialog.getByText(/openrouter configuration.*your api key/i)).toBeVisible();
  });

  test('shows OpenRouter Managed panel when selected', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    // Select OpenRouter Managed
    const managedOption = dialog.getByRole('radio', { name: /openrouter.*managed/i });
    await managedOption.click();

    // Check for OpenRouter Managed panel content
    await expect(dialog.getByText(/openrouter configuration.*managed/i)).toBeVisible();
  });

  test('provider selector is keyboard accessible', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    // Focus the radio group
    const containerOption = dialog.getByRole('radio', { name: /container ollama/i });
    await containerOption.focus();

    // Navigate with arrow keys
    await page.keyboard.press('ArrowDown');

    // External option should now be focused/checked
    const externalOption = dialog.getByRole('radio', { name: /external local llm/i });
    await expect(externalOption).toBeFocused();
  });

  test('selected provider has visual indication', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    // The selected option's label should have different styling
    // We check for the border-primary class on the label wrapper
    const containerLabel = dialog.locator('label').filter({ hasText: /container ollama/i });
    await expect(containerLabel).toHaveClass(/border-primary/);

    // Select a different option
    const externalOption = dialog.getByRole('radio', { name: /external local llm/i });
    await externalOption.click();

    // Now external should have the selected styling
    const externalLabel = dialog.locator('label').filter({ hasText: /external local llm/i });
    await expect(externalLabel).toHaveClass(/border-primary/);

    // And container should not
    await expect(containerLabel).not.toHaveClass(/border-primary/);
  });
});
