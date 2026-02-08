'use client';

import { useState } from 'react';
import { cn } from '@/lib/utils';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { OllamaContainerPanel } from './OllamaContainerPanel';
import { ExternalLLMPanel } from './ExternalLLMPanel';
import { OpenRouterPanel } from './OpenRouterPanel';
import type { LLMConfigUpdate } from '@/types/settings';

// Provider types matching backend schema
export type ProviderType =
  | 'ollama_container'
  | 'ollama_external'
  | 'openrouter_byok'
  | 'openrouter_managed';

// Provider option configuration
interface ProviderOption {
  value: ProviderType;
  label: string;
  description: string;
}

const PROVIDER_OPTIONS: ProviderOption[] = [
  {
    value: 'ollama_container',
    label: 'Container Ollama (Default)',
    description: 'Ollama running in Docker/Podman compose stack',
  },
  {
    value: 'ollama_external',
    label: 'External Local LLM',
    description: 'Connect to LM Studio, llama.cpp, or external Ollama',
  },
  {
    value: 'openrouter_byok',
    label: 'OpenRouter (Your API Key)',
    description: 'Cloud models using your OpenRouter API key',
  },
  {
    value: 'openrouter_managed',
    label: 'OpenRouter (Managed)',
    description: 'Cloud models with CodeCompass-provided access',
  },
];

export interface LLMSettingsPanelProps {
  /** Initial provider type (from settings) */
  initialProvider?: ProviderType;
  /** Callback when provider type changes */
  onProviderChange?: (provider: ProviderType) => void;
  /** Callback when any form value changes (for dirty state tracking) */
  onDirtyChange?: (dirty: boolean) => void;
  /** Callback when config changes (unified LLMConfigUpdate for save/test) */
  onConfigChange?: (config: LLMConfigUpdate) => void;
}

/**
 * LLM Settings Panel - allows users to select and configure LLM providers.
 *
 * Displays a radio card selector for provider types and renders the
 * appropriate configuration panel based on selection.
 */
export function LLMSettingsPanel({
  initialProvider = 'ollama_container',
  onProviderChange,
  onDirtyChange,
  onConfigChange,
}: LLMSettingsPanelProps) {
  const [providerType, setProviderType] = useState<ProviderType>(initialProvider);

  const handleProviderChange = (value: string) => {
    const newProvider = value as ProviderType;
    setProviderType(newProvider);
    onProviderChange?.(newProvider);
    onDirtyChange?.(true);
  };

  // Container Ollama: model selection only
  const handleContainerModelChange = (model: string) => {
    onConfigChange?.({ provider_type: 'ollama_container', model });
  };

  // External LLM: base_url, api_format, model
  const handleExternalConfigChange = (config: {
    baseUrl: string;
    apiFormat: 'auto' | 'ollama' | 'openai';
    model: string;
  }) => {
    const apiFormat =
      config.apiFormat === 'auto' ? undefined : config.apiFormat;

    onConfigChange?.({
      provider_type: 'ollama_external',
      model: config.model,
      base_url: config.baseUrl,
      ...(apiFormat ? { api_format: apiFormat } : {}),
    });
  };

  // OpenRouter BYOK: api_key + model
  const handleBYOKConfigChange = (config: { apiKey?: string; model: string }) => {
    onConfigChange?.({
      provider_type: 'openrouter_byok',
      model: config.model,
      api_key: config.apiKey,
    });
  };

  // OpenRouter Managed: model only
  const handleManagedConfigChange = (config: { apiKey?: string; model: string }) => {
    onConfigChange?.({
      provider_type: 'openrouter_managed',
      model: config.model,
    });
  };

  return (
    <div className="space-y-6">
      {/* Provider Type Selector */}
      <div className="space-y-3">
        <Label className="text-base font-medium">Provider Type</Label>
        <ProviderTypeSelector
          value={providerType}
          onChange={handleProviderChange}
        />
      </div>

      {/* Provider-specific Configuration Panel */}
      <div className="pt-2">
        {providerType === 'ollama_container' && (
          <OllamaContainerPanel
            onDirtyChange={onDirtyChange}
            onModelChange={handleContainerModelChange}
          />
        )}
        {providerType === 'ollama_external' && (
          <ExternalLLMPanel
            onDirtyChange={onDirtyChange}
            onConfigChange={handleExternalConfigChange}
          />
        )}
        {providerType === 'openrouter_byok' && (
          <OpenRouterPanel
            mode="byok"
            onDirtyChange={onDirtyChange}
            onConfigChange={handleBYOKConfigChange}
          />
        )}
        {providerType === 'openrouter_managed' && (
          <OpenRouterPanel
            mode="managed"
            onDirtyChange={onDirtyChange}
            onConfigChange={handleManagedConfigChange}
          />
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Provider Type Selector
// ============================================================================

interface ProviderTypeSelectorProps {
  value: ProviderType;
  onChange: (value: string) => void;
}

/**
 * Radio card selector for provider types.
 * Uses styled radio cards with labels and descriptions.
 */
function ProviderTypeSelector({ value, onChange }: ProviderTypeSelectorProps) {
  return (
    <RadioGroup
      value={value}
      onValueChange={onChange}
      className="grid gap-3"
      aria-label="Select LLM provider type"
    >
      {PROVIDER_OPTIONS.map((option) => (
        <label
          key={option.value}
          className={cn(
            'flex flex-col p-4 border rounded-lg cursor-pointer',
            'hover:bg-accent/50 transition-colors',
            'has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-ring',
            value === option.value && 'border-primary bg-accent/30'
          )}
        >
          <div className="flex items-center gap-3">
            <RadioGroupItem value={option.value} id={option.value} />
            <span className="font-medium">{option.label}</span>
          </div>
          <p className="text-sm text-muted-foreground ml-7 mt-1">
            {option.description}
          </p>
        </label>
      ))}
    </RadioGroup>
  );
}

