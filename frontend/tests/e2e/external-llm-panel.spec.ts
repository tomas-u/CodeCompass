import { test, expect } from '@playwright/test';

/**
 * E2E Tests: External LLM Panel
 *
 * Tests the External LLM configuration panel for connecting to
 * LM Studio, llama.cpp, vLLM, or external Ollama instances.
 *
 * Pre-conditions:
 * - Backend server running on http://localhost:8000
 * - Frontend server running on http://localhost:3000
 *
 * NOTE: These tests are skipped until issue #92 (Header integration) is complete.
 */

test.describe.skip('External LLM Panel', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/CodeCompass/i);

    // Open settings dialog
    const settingsButton = page.locator('header').getByRole('button', { name: /settings/i });
    await settingsButton.click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // Select "External Local LLM" provider
    const externalOption = dialog.getByRole('radio', { name: /external local llm/i });
    await externalOption.click();
  });

  test('displays server URL input with detect button', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    await expect(dialog.getByRole('textbox', { name: /server url/i })).toBeVisible();
    await expect(dialog.getByRole('button', { name: /detect/i })).toBeVisible();
  });

  test('URL input has default value', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    const urlInput = dialog.getByRole('textbox', { name: /server url/i });
    await expect(urlInput).toHaveValue('http://localhost:1234');
  });

  test('displays API format selector with 3 options', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    const formatGroup = dialog.getByRole('radiogroup', { name: /api format/i });
    await expect(formatGroup).toBeVisible();

    await expect(dialog.getByRole('radio', { name: /auto-detect/i })).toBeVisible();
    await expect(dialog.getByRole('radio', { name: /ollama api/i })).toBeVisible();
    await expect(dialog.getByRole('radio', { name: /openai-compatible/i })).toBeVisible();
  });

  test('auto-detect is selected by default', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    const autoOption = dialog.getByRole('radio', { name: /auto-detect/i });
    await expect(autoOption).toBeChecked();
  });

  test('API format selection works', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    // Select Ollama API
    const ollamaOption = dialog.getByRole('radio', { name: /ollama api/i });
    await ollamaOption.click();
    await expect(ollamaOption).toBeChecked();

    // Select OpenAI-compatible
    const openaiOption = dialog.getByRole('radio', { name: /openai-compatible/i });
    await openaiOption.click();
    await expect(openaiOption).toBeChecked();
    await expect(ollamaOption).not.toBeChecked();
  });

  test('displays quick config buttons', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    await expect(dialog.getByText(/common configurations/i)).toBeVisible();
    await expect(dialog.getByRole('button', { name: 'LM Studio' })).toBeVisible();
    await expect(dialog.getByRole('button', { name: 'Ollama' })).toBeVisible();
    await expect(dialog.getByRole('button', { name: 'llama.cpp' })).toBeVisible();
    await expect(dialog.getByRole('button', { name: 'vLLM' })).toBeVisible();
  });

  test('quick config buttons update URL and format', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    // Click Ollama quick config
    await dialog.getByRole('button', { name: 'Ollama' }).click();

    const urlInput = dialog.getByRole('textbox', { name: /server url/i });
    await expect(urlInput).toHaveValue('http://localhost:11434');

    const ollamaFormat = dialog.getByRole('radio', { name: /ollama api/i });
    await expect(ollamaFormat).toBeChecked();
  });

  test('quick config for llama.cpp sets correct values', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    await dialog.getByRole('button', { name: 'llama.cpp' }).click();

    const urlInput = dialog.getByRole('textbox', { name: /server url/i });
    await expect(urlInput).toHaveValue('http://localhost:8080');

    const openaiFormat = dialog.getByRole('radio', { name: /openai-compatible/i });
    await expect(openaiFormat).toBeChecked();
  });

  test('displays model name input', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    await expect(dialog.getByRole('textbox', { name: /manual model name/i })).toBeVisible();
  });

  test('manual model entry works', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    const modelInput = dialog.getByRole('textbox', { name: /manual model name/i });
    await modelInput.fill('mistral:7b');
    await expect(modelInput).toHaveValue('mistral:7b');
  });

  test('detect button is disabled with empty URL', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    // Clear the URL
    const urlInput = dialog.getByRole('textbox', { name: /server url/i });
    await urlInput.fill('');

    const detectButton = dialog.getByRole('button', { name: /detect/i });
    await expect(detectButton).toBeDisabled();
  });

  test('detect button triggers connection test', async ({ page }) => {
    const dialog = page.getByRole('dialog');

    const detectButton = dialog.getByRole('button', { name: /detect/i });
    await detectButton.click();

    // Should show some connection status (success or error)
    await expect(
      dialog.getByText(/connected successfully/i).or(
        dialog.getByText(/connection failed|failed to connect/i)
      )
    ).toBeVisible({ timeout: 10000 });
  });
});
