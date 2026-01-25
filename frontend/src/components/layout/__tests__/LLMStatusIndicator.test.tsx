/**
 * Unit tests for LLMStatusIndicator component.
 *
 * NOTE: These tests require Jest and React Testing Library to be configured.
 * To run these tests, you'll need to:
 * 1. Install: npm install -D jest @testing-library/react @testing-library/jest-dom jest-environment-jsdom
 * 2. Configure jest.config.js
 * 3. Run: npm test
 *
 * Test cases cover all visual states and interactions as specified in issue #85.
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LLMStatusIndicator, LLMStatus, LLMConfig } from '../LLMStatusIndicator';

// Mock the api module
jest.mock('@/lib/api', () => ({
  api: {
    getSettings: jest.fn(),
  },
}));

describe('LLMStatusIndicator', () => {
  const mockOnClick = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Visual States', () => {
    it('renders ready state with green dot', () => {
      const config: LLMConfig = {
        providerType: 'ollama_container',
        model: 'qwen2.5-coder:7b',
        status: 'ready',
      };

      render(<LLMStatusIndicator config={config} onClick={mockOnClick} />);

      const dot = screen.getByRole('button').querySelector('span');
      expect(dot).toHaveClass('bg-green-500');
      expect(screen.getByText('qwen2.5-coder:7b')).toBeInTheDocument();
    });

    it('renders connecting state with pulsing yellow dot', () => {
      const config: LLMConfig = {
        providerType: 'ollama_container',
        model: 'qwen2.5-coder:7b',
        status: 'connecting',
      };

      render(<LLMStatusIndicator config={config} onClick={mockOnClick} />);

      const dot = screen.getByRole('button').querySelector('span');
      expect(dot).toHaveClass('bg-yellow-500');
      expect(dot).toHaveClass('animate-pulse');
      expect(screen.getByText('Connecting...')).toBeInTheDocument();
    });

    it('renders error state with red dot', () => {
      const config: LLMConfig = {
        providerType: 'ollama_container',
        model: '',
        status: 'error',
      };

      render(
        <LLMStatusIndicator
          config={config}
          error="Connection failed"
          onClick={mockOnClick}
        />
      );

      const dot = screen.getByRole('button').querySelector('span');
      expect(dot).toHaveClass('bg-red-500');
      expect(screen.getByText('LLM Unavailable')).toBeInTheDocument();
    });

    it('renders unknown state with gray outline dot', () => {
      const config: LLMConfig = {
        providerType: 'unknown',
        model: '',
        status: 'unknown',
      };

      render(<LLMStatusIndicator config={config} onClick={mockOnClick} />);

      const dot = screen.getByRole('button').querySelector('span');
      expect(dot).toHaveClass('ring-1');
      expect(dot).toHaveClass('bg-transparent');
      expect(screen.getByText('Not configured')).toBeInTheDocument();
    });
  });

  describe('Tooltip', () => {
    it('shows correct information on hover', async () => {
      const config: LLMConfig = {
        providerType: 'ollama_container',
        model: 'qwen2.5-coder:7b',
        status: 'ready',
        baseUrl: 'http://localhost:11434',
      };

      render(<LLMStatusIndicator config={config} onClick={mockOnClick} />);

      const button = screen.getByRole('button');
      await userEvent.hover(button);

      await waitFor(() => {
        expect(screen.getByText('Container Ollama')).toBeInTheDocument();
        expect(screen.getByText('qwen2.5-coder:7b')).toBeInTheDocument();
        expect(screen.getByText('Ready')).toBeInTheDocument();
      });
    });

    it('shows error message in tooltip when present', async () => {
      const config: LLMConfig = {
        providerType: 'ollama_container',
        model: '',
        status: 'error',
      };

      render(
        <LLMStatusIndicator
          config={config}
          error="Connection refused"
          onClick={mockOnClick}
        />
      );

      const button = screen.getByRole('button');
      await userEvent.hover(button);

      await waitFor(() => {
        expect(screen.getByText(/Connection refused/)).toBeInTheDocument();
      });
    });
  });

  describe('Interactions', () => {
    it('calls onClick when clicked', async () => {
      const config: LLMConfig = {
        providerType: 'ollama_container',
        model: 'qwen2.5-coder:7b',
        status: 'ready',
      };

      render(<LLMStatusIndicator config={config} onClick={mockOnClick} />);

      const button = screen.getByRole('button');
      await userEvent.click(button);

      expect(mockOnClick).toHaveBeenCalledTimes(1);
    });

    it('supports keyboard navigation with Enter', async () => {
      const config: LLMConfig = {
        providerType: 'ollama_container',
        model: 'qwen2.5-coder:7b',
        status: 'ready',
      };

      render(<LLMStatusIndicator config={config} onClick={mockOnClick} />);

      const button = screen.getByRole('button');
      button.focus();
      fireEvent.keyDown(button, { key: 'Enter', code: 'Enter' });

      expect(mockOnClick).toHaveBeenCalled();
    });

    it('supports keyboard navigation with Space', async () => {
      const config: LLMConfig = {
        providerType: 'ollama_container',
        model: 'qwen2.5-coder:7b',
        status: 'ready',
      };

      render(<LLMStatusIndicator config={config} onClick={mockOnClick} />);

      const button = screen.getByRole('button');
      button.focus();
      fireEvent.keyDown(button, { key: ' ', code: 'Space' });

      expect(mockOnClick).toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('has correct aria-label', () => {
      const config: LLMConfig = {
        providerType: 'ollama_container',
        model: 'qwen2.5-coder:7b',
        status: 'ready',
      };

      render(<LLMStatusIndicator config={config} onClick={mockOnClick} />);

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute(
        'aria-label',
        expect.stringContaining('LLM Status: Ready')
      );
      expect(button).toHaveAttribute(
        'aria-label',
        expect.stringContaining('qwen2.5-coder:7b')
      );
    });

    it('is focusable', () => {
      const config: LLMConfig = {
        providerType: 'ollama_container',
        model: 'qwen2.5-coder:7b',
        status: 'ready',
      };

      render(<LLMStatusIndicator config={config} onClick={mockOnClick} />);

      const button = screen.getByRole('button');
      button.focus();
      expect(document.activeElement).toBe(button);
    });
  });

  describe('Model Name Truncation', () => {
    it('truncates long model names', () => {
      const config: LLMConfig = {
        providerType: 'openrouter_byok',
        model: 'anthropic/claude-3-opus-20240229',
        status: 'ready',
      };

      render(<LLMStatusIndicator config={config} onClick={mockOnClick} />);

      // The model name should be truncated to fit within 20 chars
      const text = screen.getByRole('button').textContent;
      expect(text?.length).toBeLessThanOrEqual(25); // Allow some margin for "..."
    });
  });

  describe('Provider Type Display Names', () => {
    it.each([
      ['ollama_container', 'Container Ollama'],
      ['ollama_external', 'External Ollama'],
      ['openrouter_byok', 'OpenRouter (BYOK)'],
      ['openrouter_managed', 'OpenRouter'],
    ])('maps %s to %s in tooltip', async (providerType, expectedName) => {
      const config: LLMConfig = {
        providerType,
        model: 'test-model',
        status: 'ready',
      };

      render(<LLMStatusIndicator config={config} onClick={mockOnClick} />);

      const button = screen.getByRole('button');
      await userEvent.hover(button);

      await waitFor(() => {
        expect(screen.getByText(expectedName)).toBeInTheDocument();
      });
    });
  });

  describe('API Fetching', () => {
    it('fetches config from API when not provided', async () => {
      const { api } = require('@/lib/api');
      api.getSettings.mockResolvedValue({
        llm: {
          provider: 'ollama_container',
          model: 'qwen2.5-coder:7b',
          status: 'ready',
          base_url: 'http://localhost:11434',
        },
        embedding: {
          model: 'all-MiniLM-L6-v2',
          dimensions: 384,
          status: 'ready',
        },
        analysis: {
          supported_languages: ['python'],
          max_file_size_mb: 10,
          max_repo_size_mb: 500,
        },
      });

      render(<LLMStatusIndicator onClick={mockOnClick} />);

      // Should show connecting state initially
      expect(screen.getByText('Connecting...')).toBeInTheDocument();

      // Should update after API response
      await waitFor(() => {
        expect(screen.getByText('qwen2.5-coder:7b')).toBeInTheDocument();
      });

      expect(api.getSettings).toHaveBeenCalled();
    });

    it('shows error state when API fails', async () => {
      const { api } = require('@/lib/api');
      api.getSettings.mockRejectedValue(new Error('Network error'));

      render(<LLMStatusIndicator onClick={mockOnClick} />);

      await waitFor(() => {
        expect(screen.getByText('LLM Unavailable')).toBeInTheDocument();
      });
    });
  });
});
