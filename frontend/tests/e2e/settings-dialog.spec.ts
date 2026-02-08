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
 * The tests require the Settings button in the header to have an onClick handler
 * and accessible name (added in #92).
 */

test.describe('Settings Dialog', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/CodeCompass/i);
  });

  test('opens settings dialog from header', async ({ page }) => {
    // Click the settings button in the header
    const settingsButton = page.locator('header').getByRole('button', { name: 'Settings', exact: true });
    await settingsButton.click();

    // Dialog should be visible
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // Should have "Settings" title
    await expect(dialog.getByRole('heading', { name: 'Settings' })).toBeVisible();
  });

  test('has three tabs: LLM, Embedding, Analysis', async ({ page }) => {
    // Open settings dialog
    const settingsButton = page.locator('header').getByRole('button', { name: 'Settings', exact: true });
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
    const settingsButton = page.locator('header').getByRole('button', { name: 'Settings', exact: true });
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
    const settingsButton = page.locator('header').getByRole('button', { name: 'Settings', exact: true });
    await settingsButton.click();

    const dialog = page.getByRole('dialog');

    // Check footer buttons
    await expect(dialog.getByRole('button', { name: 'Cancel' })).toBeVisible();
    await expect(dialog.getByRole('button', { name: 'Test Connection' })).toBeVisible();
    await expect(dialog.getByRole('button', { name: 'Save' })).toBeVisible();
  });

  test('Cancel button closes dialog', async ({ page }) => {
    // Open settings dialog
    const settingsButton = page.locator('header').getByRole('button', { name: 'Settings', exact: true });
    await settingsButton.click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // Use native Playwright click — NOT JS dispatch.
    // If this fails due to overlap, it means content is spilling over the footer (layout bug).
    await dialog.getByRole('button', { name: 'Cancel' }).click();

    // Dialog should be closed
    await expect(dialog).not.toBeVisible();
  });

  test('X button closes dialog', async ({ page }) => {
    // Open settings dialog
    const settingsButton = page.locator('header').getByRole('button', { name: 'Settings', exact: true });
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
    const settingsButton = page.locator('header').getByRole('button', { name: 'Settings', exact: true });
    await settingsButton.click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // Press ESC
    await page.keyboard.press('Escape');

    // Dialog should be closed
    await expect(dialog).not.toBeVisible();
  });

  test('Save and Test Connection buttons are disabled without config', async ({ page }) => {
    // Open settings dialog
    const settingsButton = page.locator('header').getByRole('button', { name: 'Settings', exact: true });
    await settingsButton.click();

    const dialog = page.getByRole('dialog');

    // Save and Test Connection should be disabled when no config has been selected
    const testButton = dialog.getByRole('button', { name: 'Test Connection' });
    const saveButton = dialog.getByRole('button', { name: 'Save' });
    await expect(testButton).toBeDisabled();
    await expect(saveButton).toBeDisabled();
  });

  test('Save and Test Connection enable after selecting a config', async ({ page }) => {
    // Open settings dialog
    const settingsButton = page.locator('header').getByRole('button', { name: 'Settings', exact: true });
    await settingsButton.click();

    const dialog = page.getByRole('dialog');

    // Select "External Local LLM" provider
    await dialog.getByRole('radio', { name: /external local llm/i }).click();

    // Enter a model name to trigger onConfigChange (scroll into view for overflow container)
    const modelInput = dialog.getByRole('textbox', { name: /manual model name/i });
    await modelInput.evaluate((el) => el.scrollIntoView({ block: 'center' }));
    await modelInput.focus();
    await modelInput.fill('test-model');

    // Both buttons should now be enabled
    const testButton = dialog.getByRole('button', { name: 'Test Connection' });
    const saveButton = dialog.getByRole('button', { name: 'Save' });
    await expect(testButton).toBeEnabled();
    await expect(saveButton).toBeEnabled();
  });

  test('dialog is accessible', async ({ page }) => {
    // Open settings dialog
    const settingsButton = page.locator('header').getByRole('button', { name: 'Settings', exact: true });
    await settingsButton.click();

    const dialog = page.getByRole('dialog');

    // Dialog should have proper ARIA attributes
    await expect(dialog).toHaveAttribute('role', 'dialog');

    // Should be able to navigate with Tab key
    await page.keyboard.press('Tab');
    const focused = page.locator(':focus');
    await expect(focused).toBeVisible();
  });

  test('footer buttons are not overlapped by content', async ({ page }) => {
    // Open settings dialog
    const settingsButton = page.locator('header').getByRole('button', { name: 'Settings', exact: true });
    await settingsButton.click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // Check that footer buttons sit within the dialog bounds and are not
    // covered by scrollable content. This catches layout overflow regressions.
    const layout = await dialog.evaluate((el) => {
      const dialogRect = el.getBoundingClientRect();
      const footer = el.querySelector('[data-slot="dialog-footer"]');
      const scrollArea = el.querySelector('.overflow-y-auto');
      if (!footer || !scrollArea) return null;
      const footerRect = footer.getBoundingClientRect();
      const scrollRect = scrollArea.getBoundingClientRect();
      return {
        footerInsideDialog: footerRect.bottom <= dialogRect.bottom + 1,
        contentDoesNotOverlapFooter: scrollRect.bottom <= footerRect.top + 1,
      };
    });

    expect(layout).not.toBeNull();
    expect(layout!.footerInsideDialog).toBe(true);
    expect(layout!.contentDoesNotOverlapFooter).toBe(true);
  });

  test('footer buttons are not overlapped after selecting External LLM', async ({ page }) => {
    // The External LLM panel has more content than Container Ollama,
    // so this specifically guards against overflow with longer forms.
    const settingsButton = page.locator('header').getByRole('button', { name: 'Settings', exact: true });
    await settingsButton.click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // Switch to External LLM (more content)
    await dialog.getByRole('radio', { name: /external local llm/i }).click();

    const layout = await dialog.evaluate((el) => {
      const dialogRect = el.getBoundingClientRect();
      const footer = el.querySelector('[data-slot="dialog-footer"]');
      const scrollArea = el.querySelector('.overflow-y-auto');
      if (!footer || !scrollArea) return null;
      const footerRect = footer.getBoundingClientRect();
      const scrollRect = scrollArea.getBoundingClientRect();
      return {
        footerInsideDialog: footerRect.bottom <= dialogRect.bottom + 1,
        contentDoesNotOverlapFooter: scrollRect.bottom <= footerRect.top + 1,
      };
    });

    expect(layout).not.toBeNull();
    expect(layout!.footerInsideDialog).toBe(true);
    expect(layout!.contentDoesNotOverlapFooter).toBe(true);

    // Also verify footer buttons are natively clickable (not obscured)
    await dialog.getByRole('button', { name: 'Cancel' }).click();
    await expect(dialog).not.toBeVisible();
  });
});
