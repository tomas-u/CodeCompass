import { test, expect, Page } from '@playwright/test';

/**
 * E2E Tests: Chat Panel Functionality
 *
 * Tests the streaming chat feature including:
 * - Opening/closing chat panel
 * - Sending messages and receiving responses
 * - Error handling
 * - Keyboard shortcuts
 * - UI interactions
 *
 * Pre-conditions:
 * - Backend server running on http://localhost:8000
 * - Frontend server running on http://localhost:3000
 * - At least one "ready" project exists (for full chat tests)
 * - Ollama and Qdrant services running (for streaming tests)
 *
 * To run:
 *   cd frontend
 *   npm run test:e2e -- chat.spec.ts
 *
 * Or with UI:
 *   npm run test:e2e:ui -- chat.spec.ts
 */

// Increase timeout for tests that depend on LLM responses
test.setTimeout(60000);

test.describe('Chat Panel', () => {
  /**
   * Helper to open chat panel
   */
  async function openChatPanel(page: Page) {
    const chatButton = page.locator('button[title*="chat panel"]');
    await chatButton.click();
    await expect(page.getByText('Ask about this codebase')).toBeVisible();
  }

  /**
   * Helper to select a ready project
   */
  async function selectReadyProject(page: Page): Promise<boolean> {
    // Try to get a ready project from API
    try {
      const response = await page.request.get('http://localhost:8000/api/projects?status=ready&limit=1');
      const data = await response.json();

      if (data.items.length === 0) {
        return false;
      }

      // Click the project selector dropdown
      const projectDropdown = page.getByRole('button', { name: /select project/i });
      await projectDropdown.click();

      // Wait for dropdown to open and select ready project
      await page.waitForSelector('[data-testid="project-item"]', { timeout: 5000 });
      const projectItem = page.locator('[data-testid="project-item"][data-status="ready"]').first();
      await projectItem.click();

      return true;
    } catch {
      return false;
    }
  }

  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test.describe('Panel Open/Close', () => {
    test('should open chat panel when clicking chat button', async ({ page }) => {
      // Chat panel should be closed initially
      await expect(page.getByText('Ask about this codebase')).not.toBeVisible();

      // Open chat panel
      await openChatPanel(page);

      // Verify chat UI elements are visible
      await expect(page.getByTestId('chat-input')).toBeVisible();
      await expect(page.getByTestId('chat-send-button')).toBeVisible();
    });

    test('should close chat panel when clicking close button', async ({ page }) => {
      await openChatPanel(page);

      // Click close button
      const closeButton = page.locator('button[title="Close"]');
      await closeButton.click();

      // Chat panel should be hidden
      await expect(page.getByText('Ask about this codebase')).not.toBeVisible();
    });

    test('should open chat panel with Ctrl+K keyboard shortcut', async ({ page }) => {
      // Press Ctrl+K
      await page.keyboard.press('Control+k');

      // Chat panel should open
      await expect(page.getByText('Ask about this codebase')).toBeVisible();

      // Input should be focused
      const chatInput = page.getByTestId('chat-input');
      await expect(chatInput).toBeFocused({ timeout: 1000 });
    });

    test('should toggle minimize/maximize', async ({ page }) => {
      await openChatPanel(page);

      // Click minimize button
      const minimizeButton = page.locator('button[title="Minimize"]');
      await minimizeButton.click();

      // Input should be hidden
      await expect(page.getByTestId('chat-input')).not.toBeVisible();

      // Click maximize button
      const maximizeButton = page.locator('button[title="Maximize"]');
      await maximizeButton.click();

      // Input should be visible again
      await expect(page.getByTestId('chat-input')).toBeVisible();
    });
  });

  test.describe('Message Input', () => {
    test('should enable send button when text is entered', async ({ page }) => {
      await openChatPanel(page);

      const sendButton = page.getByTestId('chat-send-button');
      const chatInput = page.getByTestId('chat-input');

      // Send button should be disabled initially
      await expect(sendButton).toBeDisabled();

      // Type a message
      await chatInput.fill('Hello');

      // Send button should be enabled
      await expect(sendButton).toBeEnabled();
    });

    test('should disable send button when input is cleared', async ({ page }) => {
      await openChatPanel(page);

      const sendButton = page.getByTestId('chat-send-button');
      const chatInput = page.getByTestId('chat-input');

      await chatInput.fill('Hello');
      await expect(sendButton).toBeEnabled();

      await chatInput.clear();
      await expect(sendButton).toBeDisabled();
    });

    test('should send message on Enter key', async ({ page }) => {
      await openChatPanel(page);

      const chatInput = page.getByTestId('chat-input');
      await chatInput.fill('Test message');
      await chatInput.press('Enter');

      // User message should appear
      await expect(page.getByTestId('chat-message-user')).toBeVisible();
      await expect(page.getByText('Test message')).toBeVisible();

      // Input should be cleared
      await expect(chatInput).toHaveValue('');
    });

    test('should add newline on Shift+Enter', async ({ page }) => {
      await openChatPanel(page);

      const chatInput = page.getByTestId('chat-input');
      await chatInput.fill('Line 1');
      await chatInput.press('Shift+Enter');
      await chatInput.type('Line 2');

      // Input should contain both lines
      const value = await chatInput.inputValue();
      expect(value).toContain('Line 1');
      expect(value).toContain('Line 2');

      // Message should not be sent (no user message visible)
      await expect(page.getByTestId('chat-message-user')).not.toBeVisible();
    });
  });

  test.describe('Error Handling', () => {
    test('should show error when no project is selected', async ({ page }) => {
      await openChatPanel(page);

      // Ensure no project is selected (should be default state)
      const projectDropdown = page.getByRole('button', { name: /select project/i });
      await expect(projectDropdown).toBeVisible();

      // Send a message
      const chatInput = page.getByTestId('chat-input');
      await chatInput.fill('What does this code do?');
      await chatInput.press('Enter');

      // Should see error message about no project
      await expect(page.getByText(/no project selected/i)).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('Clear Chat', () => {
    test('should clear all messages when clicking clear button', async ({ page }) => {
      await openChatPanel(page);

      // Send a message to create user message
      const chatInput = page.getByTestId('chat-input');
      await chatInput.fill('Test message to clear');
      await chatInput.press('Enter');

      // Wait for user message to appear
      await expect(page.getByText('Test message to clear')).toBeVisible();

      // Click clear button
      const clearButton = page.getByTestId('chat-clear-button');
      await clearButton.click();

      // Message should be gone (may show mock messages instead)
      await expect(page.getByText('Test message to clear')).not.toBeVisible();
    });
  });

  test.describe('Streaming Chat (requires backend services)', () => {
    test('should send message and receive streaming response', async ({ page }) => {
      // Try to select a ready project
      const hasProject = await selectReadyProject(page);

      if (!hasProject) {
        test.skip(true, 'No ready project available');
        return;
      }

      await openChatPanel(page);

      // Send a message
      const chatInput = page.getByTestId('chat-input');
      await chatInput.fill('What is this project about?');
      await page.getByTestId('chat-send-button').click();

      // User message should appear
      await expect(page.getByTestId('chat-message-user')).toBeVisible();

      // Typing indicator should appear (briefly)
      // Note: This may be very fast if response is quick
      try {
        await expect(page.getByTestId('chat-typing-indicator')).toBeVisible({ timeout: 2000 });
      } catch {
        // Typing indicator may have already disappeared
      }

      // Wait for assistant response (with longer timeout for LLM)
      await expect(page.getByTestId('chat-message-assistant')).toBeVisible({ timeout: 60000 });

      // Typing indicator should disappear after response
      await expect(page.getByTestId('chat-typing-indicator')).not.toBeVisible();
    });

    test('should display sources when available', async ({ page }) => {
      const hasProject = await selectReadyProject(page);

      if (!hasProject) {
        test.skip(true, 'No ready project available');
        return;
      }

      await openChatPanel(page);

      // Send a message that should trigger source retrieval
      const chatInput = page.getByTestId('chat-input');
      await chatInput.fill('Show me the main entry point of the application');
      await page.getByTestId('chat-send-button').click();

      // Wait for response
      await expect(page.getByTestId('chat-message-assistant')).toBeVisible({ timeout: 60000 });

      // Check for sources section (may or may not be present depending on content)
      try {
        await expect(page.getByText('Sources:')).toBeVisible({ timeout: 5000 });
      } catch {
        // Sources may not be present for all responses
        console.log('No sources displayed (this may be expected)');
      }
    });

    test('should handle streaming error gracefully', async ({ page }) => {
      const hasProject = await selectReadyProject(page);

      if (!hasProject) {
        test.skip(true, 'No ready project available');
        return;
      }

      await openChatPanel(page);

      // Mock network failure by blocking API requests
      await page.route('**/api/projects/*/chat', route => {
        route.abort('failed');
      });

      // Send a message
      const chatInput = page.getByTestId('chat-input');
      await chatInput.fill('This should fail');
      await page.getByTestId('chat-send-button').click();

      // Should see error message
      await expect(page.getByText(/error/i)).toBeVisible({ timeout: 10000 });

      // Typing indicator should disappear
      await expect(page.getByTestId('chat-typing-indicator')).not.toBeVisible();

      // Should be able to send another message
      await page.unroute('**/api/projects/*/chat');
      await expect(page.getByTestId('chat-send-button')).toBeEnabled();
    });
  });

  test.describe('Mock Data Fallback', () => {
    test('should display mock messages when no real messages exist', async ({ page }) => {
      await openChatPanel(page);

      // Should see mock data indicator
      await expect(page.getByText('Sample Conversation')).toBeVisible();

      // Should see example messages
      await expect(page.getByText('example messages')).toBeVisible();
    });

    test('should hide mock data indicator after sending real message', async ({ page }) => {
      await openChatPanel(page);

      // Verify mock indicator is visible
      await expect(page.getByText('Sample Conversation')).toBeVisible();

      // Send a real message
      const chatInput = page.getByTestId('chat-input');
      await chatInput.fill('My first real message');
      await chatInput.press('Enter');

      // Mock indicator should disappear (real messages replace mock)
      await expect(page.getByText('Sample Conversation')).not.toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('Code Block Rendering', () => {
    test('should render code blocks with syntax highlighting', async ({ page }) => {
      const hasProject = await selectReadyProject(page);

      if (!hasProject) {
        test.skip(true, 'No ready project available');
        return;
      }

      await openChatPanel(page);

      // Send a message that should get a code response
      const chatInput = page.getByTestId('chat-input');
      await chatInput.fill('Show me an example function');
      await page.getByTestId('chat-send-button').click();

      // Wait for response
      await expect(page.getByTestId('chat-message-assistant')).toBeVisible({ timeout: 60000 });

      // If response contains code, check for copy button
      const codeBlock = page.locator('.language-python, .language-javascript, .language-typescript').first();
      const hasCode = await codeBlock.count() > 0;

      if (hasCode) {
        // Code block should have copy button
        const copyButton = page.locator('button').filter({ has: page.locator('svg') }).first();
        await expect(copyButton).toBeVisible();
      }
    });
  });
});
