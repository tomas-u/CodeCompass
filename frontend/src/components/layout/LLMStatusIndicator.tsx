'use client';

import { useEffect, useState, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { api } from '@/lib/api';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';

// Status types for the LLM indicator
export type LLMStatus = 'ready' | 'connecting' | 'error' | 'unknown';

export interface LLMConfig {
  providerType: string;
  model: string;
  status: LLMStatus;
  baseUrl?: string;
  lastUsed?: string;
}

export interface LLMStatusIndicatorProps {
  onClick?: () => void;
  // Optional: pass config directly (for when store is implemented)
  config?: LLMConfig;
  // Optional: pass error directly
  error?: string | null;
}

// Map provider types to display names
const providerDisplayNames: Record<string, string> = {
  ollama_container: 'Container Ollama',
  ollama_external: 'External Ollama',
  openrouter_byok: 'OpenRouter (BYOK)',
  openrouter_managed: 'OpenRouter',
};

// Status colors
// Note: 'unknown' status uses ring styling (outline dot) applied in component logic,
// so its 'dot' value is not used directly but kept for fallback consistency.
const statusColors: Record<LLMStatus, { dot: string; text: string }> = {
  ready: {
    dot: 'bg-green-500',
    text: 'text-green-600 dark:text-green-400',
  },
  connecting: {
    dot: 'bg-yellow-500',
    text: 'text-yellow-600 dark:text-yellow-400',
  },
  error: {
    dot: 'bg-red-500',
    text: 'text-red-600 dark:text-red-400',
  },
  unknown: {
    dot: '', // Overridden in component to use ring styling for outline effect
    text: 'text-gray-500 dark:text-gray-400',
  },
};

// Status display text
const statusDisplayText: Record<LLMStatus, string> = {
  ready: 'Ready',
  connecting: 'Connecting...',
  error: 'LLM Unavailable',
  unknown: 'Not configured',
};

export function LLMStatusIndicator({
  onClick,
  config: propConfig,
  error: propError,
}: LLMStatusIndicatorProps) {
  const [config, setConfig] = useState<LLMConfig | null>(propConfig || null);
  const [error, setError] = useState<string | null>(propError || null);
  const [isLoading, setIsLoading] = useState(!propConfig);

  // Fetch LLM config from API if not provided via props
  const fetchConfig = useCallback(async () => {
    if (propConfig) return; // Don't fetch if config is provided via props

    try {
      setIsLoading(true);
      const response = await api.getSettings();

      // Map API response to our config format
      const status = mapApiStatusToLLMStatus(response.llm.status);
      setConfig({
        providerType: response.llm.provider,
        model: response.llm.model,
        status,
        baseUrl: response.llm.base_url,
      });
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch LLM status');
      setConfig({
        providerType: 'unknown',
        model: '',
        status: 'error',
      });
    } finally {
      setIsLoading(false);
    }
  }, [propConfig]);

  // Map API status string to our LLMStatus type
  function mapApiStatusToLLMStatus(apiStatus: string): LLMStatus {
    switch (apiStatus.toLowerCase()) {
      case 'ready':
        return 'ready';
      case 'connecting':
      case 'loading':
      case 'initializing':
        return 'connecting';
      case 'error':
      case 'unavailable':
      case 'failed':
        return 'error';
      default:
        return 'unknown';
    }
  }

  // Update config when prop changes
  useEffect(() => {
    if (propConfig) {
      setConfig(propConfig);
      setIsLoading(false);
    }
  }, [propConfig]);

  // Update error when prop changes
  useEffect(() => {
    if (propError !== undefined) {
      setError(propError);
    }
  }, [propError]);

  // Fetch config on mount and periodically (only if not provided via props)
  useEffect(() => {
    if (propConfig) {
      return; // Skip fetching and polling when config is provided via props
    }

    fetchConfig();

    // Poll for status updates every 30 seconds
    const intervalId = setInterval(fetchConfig, 30000);

    return () => clearInterval(intervalId);
  }, [fetchConfig, propConfig]);

  // Determine effective status
  const effectiveStatus: LLMStatus = isLoading
    ? 'connecting'
    : config?.status || 'unknown';

  // Get display values
  const colors = statusColors[effectiveStatus];
  const displayText = isLoading
    ? 'Connecting...'
    : config?.model
      ? truncateModel(config.model, 20)
      : statusDisplayText[effectiveStatus];

  const providerName = config?.providerType
    ? providerDisplayNames[config.providerType] || config.providerType
    : 'Unknown';

  // Tooltip content
  const tooltipContent = (
    <div className="space-y-1 text-sm">
      <div>
        <span className="text-muted-foreground">Provider:</span>{' '}
        {providerName}
      </div>
      <div>
        <span className="text-muted-foreground">Model:</span>{' '}
        {config?.model || 'Not configured'}
      </div>
      <div>
        <span className="text-muted-foreground">Status:</span>{' '}
        <span className={colors.text}>{statusDisplayText[effectiveStatus]}</span>
      </div>
      {config?.baseUrl && (
        <div>
          <span className="text-muted-foreground">URL:</span>{' '}
          {truncateUrl(config.baseUrl, 30)}
        </div>
      )}
      {error && (
        <div className="text-red-500 text-xs mt-1">
          Error: {error}
        </div>
      )}
    </div>
  );

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          onClick={onClick}
          className={cn(
            'flex items-center gap-2 px-3 py-1.5 rounded-md',
            'hover:bg-accent transition-colors',
            'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
            'max-w-[200px]'
          )}
          aria-label={`LLM Status: ${statusDisplayText[effectiveStatus]}. Model: ${config?.model || 'Not configured'}. Click to open settings.`}
        >
          {/* Status dot */}
          <span
            className={cn(
              'w-2 h-2 rounded-full flex-shrink-0',
              colors.dot,
              effectiveStatus === 'connecting' && 'animate-pulse',
              effectiveStatus === 'unknown' && 'ring-1 ring-gray-400 dark:ring-gray-500 bg-transparent'
            )}
            aria-hidden="true"
          />

          {/* Model name / status text */}
          <span
            className={cn(
              'text-sm truncate',
              effectiveStatus === 'ready'
                ? 'text-foreground'
                : colors.text,
              // Hide text on very small screens
              'hidden sm:inline'
            )}
          >
            {displayText}
          </span>
        </button>
      </TooltipTrigger>
      <TooltipContent side="bottom" className="max-w-[300px]">
        {tooltipContent}
      </TooltipContent>
    </Tooltip>
  );
}

// Helper to truncate model name
function truncateModel(model: string, maxLength: number): string {
  if (model.length <= maxLength) return model;
  return model.slice(0, maxLength - 3) + '...';
}

// Helper to truncate URL - shows as much as possible within maxLength
function truncateUrl(url: string, maxLength: number): string {
  if (url.length <= maxLength) return url;

  try {
    const parsed = new URL(url);
    // Try to show hostname:port first
    const hostWithPort = parsed.host; // includes port if present

    if (hostWithPort.length <= maxLength) {
      // Can fit host:port, try to add path
      const remaining = maxLength - hostWithPort.length;
      if (remaining > 4 && parsed.pathname.length > 1) {
        // Add as much of the path as fits
        const pathPart = parsed.pathname.slice(0, remaining - 3) + '...';
        return hostWithPort + pathPart;
      }
      return hostWithPort;
    }

    // Host alone is too long, truncate it
    return hostWithPort.slice(0, maxLength - 3) + '...';
  } catch {
    // Invalid URL, just truncate the string
    return url.slice(0, maxLength - 3) + '...';
  }
}
