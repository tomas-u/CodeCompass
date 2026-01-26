import { test, expect } from '@playwright/test';

/**
 * E2E Tests: OpenRouter Panel
 *
 * Tests the OpenRouter configuration panel in both BYOK and Managed modes.
 *
 * Pre-conditions:
 * - Backend server running on http://localhost:8000
 * - Frontend server running on http://localhost:3000
 *
 * The tests require the Settings button in the header (added in #92).
 */

test.describe('OpenRouter Panel - BYOK Mode', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/CodeCompass/i);

    // Open settings dialog
    const settingsButton = page.locator('header').getByRole('button', { name: /settings/i });
    await settingsButton.click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // Select OpenRouter (BYOK) provider
    const byokOption = dialog.getByRole('radio', { name: /openrouter.*your api key/i });
    await byokOption.click();
  });

  test('displays API key input with validate button', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    await expect(dialog.getByRole('textbox', { name: /api key/i })).toBeVisible();
    await expect(dialog.getByRole('button', { name: /validate/i })).toBeVisible();
  });

  test('API key input is password type', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    const input = dialog.locator('input[type="password"]');
    await expect(input).toBeVisible();
  });

  test('validate button is disabled without API key', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    const validateButton = dialog.getByRole('button', { name: /validate/i });
    await expect(validateButton).toBeDisabled();
  });

  test('validate button is enabled with API key', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    const input = dialog.getByRole('textbox', { name: /api key/i });
    await input.fill('sk-or-v1-test-key-12345');

    const validateButton = dialog.getByRole('button', { name: /validate/i });
    await expect(validateButton).toBeEnabled();
  });

  test('shows link to OpenRouter keys page', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    const link = dialog.getByRole('link', { name: /openrouter\.ai\/keys/i });
    await expect(link).toBeVisible();
    await expect(link).toHaveAttribute('href', 'https://openrouter.ai/keys');
    await expect(link).toHaveAttribute('target', '_blank');
  });

  test('model browser is hidden until key is validated', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    // Model browser should not be visible before validation
    await expect(dialog.getByText(/select model/i)).not.toBeVisible();
  });

  test('validate shows status feedback', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    const input = dialog.getByRole('textbox', { name: /api key/i });
    await input.fill('sk-or-v1-test-key');

    const validateButton = dialog.getByRole('button', { name: /validate/i });
    await validateButton.click();

    // Should show either valid or invalid status
    await expect(
      dialog.getByText(/valid api key/i).or(
        dialog.getByText(/invalid|validation failed/i)
      )
    ).toBeVisible({ timeout: 10000 });
  });
});

test.describe('OpenRouter Panel - Managed Mode', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/CodeCompass/i);

    // Open settings dialog
    const settingsButton = page.locator('header').getByRole('button', { name: /settings/i });
    await settingsButton.click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // Select OpenRouter (Managed) provider
    const managedOption = dialog.getByRole('radio', { name: /openrouter.*managed/i });
    await managedOption.click();
  });

  test('displays managed access alert', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    await expect(dialog.getByText(/managed access/i)).toBeVisible();
    await expect(dialog.getByText(/usage may be limited/i)).toBeVisible();
  });

  test('displays model selection', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    await expect(dialog.getByText(/select model/i)).toBeVisible();

    // Should have managed model options
    const radioGroup = dialog.getByRole('radiogroup', { name: /managed model/i });
    await expect(radioGroup).toBeVisible();
  });

  test('model selection works', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    const radioGroup = dialog.getByRole('radiogroup', { name: /managed model/i });
    const firstModel = radioGroup.getByRole('radio').first();
    await firstModel.click();
    await expect(firstModel).toBeChecked();
  });

  test('does not show API key input', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    // Managed mode should not have API key input
    await expect(dialog.getByRole('textbox', { name: /api key/i })).not.toBeVisible();
  });
});
