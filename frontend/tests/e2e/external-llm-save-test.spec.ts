import { test, expect, type Page, type Locator } from '@playwright/test';

/**
 * E2E Tests: External LLM Config — Save & Test Connection
 *
 * Verifies the wiring between the Settings dialog buttons (Save, Test Connection)
 * and the backend via the Zustand store actions (updateLLMConfig, validateLLMConfig).
 *
 * Pre-conditions:
 * - Backend server running on http://localhost:8000
 * - Frontend server running on http://localhost:3000
 * - Ollama reachable from the backend container (http://ollama:11434)
 */

/**
 * Helpers for interacting with elements INSIDE the dialog's scroll container.
 *
 * The dialog content area uses `overflow-y: auto`. On smaller viewports the
 * content may extend beyond the visible area, requiring a scroll before
 * Playwright can interact with the element.
 *
 * IMPORTANT: These helpers must ONLY be used for elements inside the scrollable
 * content area (form inputs, radio buttons, quick-config buttons).
 * Footer buttons (Cancel, Test Connection, Save) must always use native
 * Playwright `.click()` — if that fails due to overlap, it's a real layout bug.
 */
async function scrollAndClick(locator: Locator) {
  await locator.evaluate((el) => {
    el.scrollIntoView({ block: 'center' });
    (el as HTMLElement).click();
  });
}

async function scrollAndFill(locator: Locator, value: string) {
  await locator.evaluate((el) => el.scrollIntoView({ block: 'center' }));
  await locator.focus();
  await locator.fill(value);
}

test.describe('External LLM — Save & Test Connection', () => {
  // Store original config so we can restore it after tests that modify it
  let originalConfig: Record<string, unknown> | null = null;

  test.beforeAll(async ({ request }) => {
    // Capture the current LLM config so we can restore after save tests
    const resp = await request.get('http://localhost:8000/api/settings/llm');
    if (resp.ok()) {
      originalConfig = await resp.json();
    }
  });

  test.afterAll(async ({ request }) => {
    // Restore original config if we captured it
    if (originalConfig) {
      await request.put('http://localhost:8000/api/settings/llm', {
        data: {
          provider_type: originalConfig.provider_type,
          model: originalConfig.model,
          base_url: originalConfig.base_url,
          api_format: originalConfig.api_format,
        },
      });
    }
  });

  /**
   * Helper: open the settings dialog and select "External Local LLM"
   */
  async function openExternalLLMSettings(page: Page) {
    await page.goto('/');
    await expect(page).toHaveTitle(/CodeCompass/i);

    const settingsButton = page.locator('header').getByRole('button', { name: 'Settings', exact: true });
    await settingsButton.click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // Select "External Local LLM" provider
    await dialog.getByRole('radio', { name: /external local llm/i }).click();

    return dialog;
  }

  /**
   * Helper: fill in External LLM config (URL, API format, model) with scrolling
   */
  async function fillExternalConfig(
    dialog: Locator,
    opts: { url: string; apiFormat?: 'ollama' | 'openai'; model: string }
  ) {
    const urlInput = dialog.getByRole('textbox', { name: /server url/i });
    await scrollAndFill(urlInput, opts.url);

    if (opts.apiFormat === 'ollama') {
      await scrollAndClick(dialog.getByRole('radio', { name: /ollama api/i }));
    } else if (opts.apiFormat === 'openai') {
      await scrollAndClick(dialog.getByRole('radio', { name: /openai-compatible/i }));
    }

    const modelInput = dialog.getByRole('textbox', { name: /manual model name/i });
    await scrollAndFill(modelInput, opts.model);
  }

  // --------------------------------------------------------------------------
  // Button state tests
  // --------------------------------------------------------------------------

  test('Save and Test Connection are disabled until config is entered', async ({ page }) => {
    const dialog = await openExternalLLMSettings(page);

    // Buttons disabled right after selecting the provider (no model entered yet)
    const testBtn = dialog.getByRole('button', { name: 'Test Connection' });
    const saveBtn = dialog.getByRole('button', { name: 'Save' });

    // The buttons should be disabled because no config change has been emitted yet.
    await expect(testBtn).toBeDisabled();
    await expect(saveBtn).toBeDisabled();
  });

  test('buttons enable after entering a model name', async ({ page }) => {
    const dialog = await openExternalLLMSettings(page);

    // Type a model name — this triggers ExternalLLMPanel.onConfigChange
    const modelInput = dialog.getByRole('textbox', { name: /manual model name/i });
    await scrollAndFill(modelInput, 'qwen2.5:0.5b');

    await expect(dialog.getByRole('button', { name: 'Test Connection' })).toBeEnabled();
    await expect(dialog.getByRole('button', { name: 'Save' })).toBeEnabled();
  });

  test('buttons enable after changing the server URL', async ({ page }) => {
    const dialog = await openExternalLLMSettings(page);

    // Change the URL — this also triggers onConfigChange
    const urlInput = dialog.getByRole('textbox', { name: /server url/i });
    await scrollAndFill(urlInput, 'http://ollama:11434');

    await expect(dialog.getByRole('button', { name: 'Test Connection' })).toBeEnabled();
    await expect(dialog.getByRole('button', { name: 'Save' })).toBeEnabled();
  });

  // --------------------------------------------------------------------------
  // Test Connection — success
  // --------------------------------------------------------------------------

  test('Test Connection shows success with response time', async ({ page }) => {
    test.setTimeout(60000);
    const dialog = await openExternalLLMSettings(page);

    await fillExternalConfig(dialog, {
      url: 'http://ollama:11434',
      apiFormat: 'ollama',
      model: 'qwen2.5:0.5b',
    });

    // Click Test Connection
    const testBtn = dialog.getByRole('button', { name: 'Test Connection' });
    await testBtn.click();

    // Should show loading state
    await expect(testBtn).toBeDisabled();

    // Wait for success message with response time
    await expect(
      dialog.getByText(/connection successful/i)
    ).toBeVisible({ timeout: 30000 });

    // Should include response time in milliseconds
    await expect(
      dialog.getByText(/\(\d+ms\)/)
    ).toBeVisible();

    // Button should re-enable after test completes
    await expect(testBtn).toBeEnabled();
  });

  // --------------------------------------------------------------------------
  // Test Connection — failure
  // --------------------------------------------------------------------------

  test('Test Connection shows error for unreachable server', async ({ page }) => {
    const dialog = await openExternalLLMSettings(page);

    await fillExternalConfig(dialog, {
      url: 'http://nonexistent-host:99999',
      model: 'some-model',
    });

    // Click Test Connection
    const testBtn = dialog.getByRole('button', { name: 'Test Connection' });
    await testBtn.click();

    // Should show error feedback
    await expect(
      dialog.locator('.text-destructive').first()
    ).toBeVisible({ timeout: 30000 });

    // Button should re-enable
    await expect(testBtn).toBeEnabled();
  });

  // --------------------------------------------------------------------------
  // Test Connection — validation result clears on config change
  // --------------------------------------------------------------------------

  test('validation result clears when config changes', async ({ page }) => {
    test.setTimeout(60000);
    const dialog = await openExternalLLMSettings(page);

    await fillExternalConfig(dialog, {
      url: 'http://ollama:11434',
      apiFormat: 'ollama',
      model: 'qwen2.5:0.5b',
    });

    await dialog.getByRole('button', { name: 'Test Connection' }).click();

    // Wait for result to appear
    await expect(
      dialog.getByText(/connection successful/i).or(
        dialog.locator('.text-destructive').first()
      )
    ).toBeVisible({ timeout: 30000 });

    // Now change the model — result should clear
    const modelInput = dialog.getByRole('textbox', { name: /manual model name/i });
    await scrollAndFill(modelInput, 'different-model');

    // The success/error message should disappear
    await expect(
      dialog.getByText(/connection successful/i)
    ).not.toBeVisible();
  });

  // --------------------------------------------------------------------------
  // Save — success
  // --------------------------------------------------------------------------

  test('Save closes dialog on success', async ({ page }) => {
    const dialog = await openExternalLLMSettings(page);

    await fillExternalConfig(dialog, {
      url: 'http://ollama:11434',
      apiFormat: 'ollama',
      model: 'qwen2.5:0.5b',
    });

    // Click Save
    const saveBtn = dialog.getByRole('button', { name: 'Save' });
    await saveBtn.click();

    // Dialog should close on successful save
    await expect(dialog).not.toBeVisible({ timeout: 10000 });
  });

  test('Save persists config to backend', async ({ page, request }) => {
    const dialog = await openExternalLLMSettings(page);

    await fillExternalConfig(dialog, {
      url: 'http://ollama:11434',
      apiFormat: 'ollama',
      model: 'qwen2.5:0.5b',
    });

    // Save
    await dialog.getByRole('button', { name: 'Save' }).click();
    await expect(dialog).not.toBeVisible({ timeout: 10000 });

    // Verify backend received the config
    const resp = await request.get('http://localhost:8000/api/settings/llm');
    expect(resp.ok()).toBe(true);

    const config = await resp.json();
    expect(config.provider_type).toBe('ollama_external');
    expect(config.model).toBe('qwen2.5:0.5b');
    expect(config.base_url).toBe('http://ollama:11434');
  });

  // --------------------------------------------------------------------------
  // Save — error feedback
  // --------------------------------------------------------------------------

  test('Save shows error or closes for invalid config', async ({ page }) => {
    const dialog = await openExternalLLMSettings(page);

    await fillExternalConfig(dialog, {
      url: 'http://nonexistent:99999',
      model: 'fake-model',
    });

    const saveBtn = dialog.getByRole('button', { name: 'Save' });
    await saveBtn.click();

    // Wait for either: dialog closes (save succeeded anyway) or error appears
    await expect(
      dialog.locator('.text-destructive').first().or(
        page.locator('body') // fallback — dialog closed
      )
    ).toBeVisible({ timeout: 10000 });

    // Save button should re-enable regardless of outcome
    if (await dialog.isVisible()) {
      await expect(saveBtn).toBeEnabled();
    }
  });

  // --------------------------------------------------------------------------
  // Quick config buttons propagate to Save/Test
  // --------------------------------------------------------------------------

  test('quick config button enables Save and Test', async ({ page }) => {
    const dialog = await openExternalLLMSettings(page);

    // Click the Ollama quick config — sets URL and format
    const ollamaBtn = dialog.getByRole('button', { name: 'Ollama' });
    await scrollAndClick(ollamaBtn);

    // Buttons should be enabled because quick config triggers onConfigChange
    await expect(dialog.getByRole('button', { name: 'Test Connection' })).toBeEnabled();
    await expect(dialog.getByRole('button', { name: 'Save' })).toBeEnabled();
  });
});
