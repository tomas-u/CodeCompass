'use client';

import { useState } from 'react';
import { cn } from '@/lib/utils';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';

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
}: LLMSettingsPanelProps) {
  const [providerType, setProviderType] = useState<ProviderType>(initialProvider);

  const handleProviderChange = (value: string) => {
    const newProvider = value as ProviderType;
    setProviderType(newProvider);
    onProviderChange?.(newProvider);
    onDirtyChange?.(true);
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
          <OllamaContainerPanel onDirtyChange={onDirtyChange} />
        )}
        {providerType === 'ollama_external' && (
          <ExternalLLMPanel onDirtyChange={onDirtyChange} />
        )}
        {providerType === 'openrouter_byok' && (
          <OpenRouterPanel mode="byok" onDirtyChange={onDirtyChange} />
        )}
        {providerType === 'openrouter_managed' && (
          <OpenRouterPanel mode="managed" onDirtyChange={onDirtyChange} />
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

// ============================================================================
// Placeholder Panels (to be implemented in issues #88, #89, #90)
// ============================================================================

interface PanelProps {
  onDirtyChange?: (dirty: boolean) => void;
}

/**
 * Ollama Container Panel - placeholder for issue #88
 */
function OllamaContainerPanel({ onDirtyChange: _onDirtyChange }: PanelProps) {
  return (
    <div className="p-4 border rounded-lg bg-muted/30">
      <div className="text-center text-muted-foreground py-6">
        <p className="font-medium">Container Ollama Configuration</p>
        <p className="text-sm mt-2">
          Configure Ollama running in the compose stack.
        </p>
        <p className="text-xs mt-4 text-muted-foreground/70">
          Full implementation in issue #88
        </p>
      </div>
    </div>
  );
}

/**
 * External LLM Panel - placeholder for issue #89
 */
function ExternalLLMPanel({ onDirtyChange: _onDirtyChange }: PanelProps) {
  return (
    <div className="p-4 border rounded-lg bg-muted/30">
      <div className="text-center text-muted-foreground py-6">
        <p className="font-medium">External LLM Configuration</p>
        <p className="text-sm mt-2">
          Connect to LM Studio, llama.cpp, or external Ollama instance.
        </p>
        <p className="text-xs mt-4 text-muted-foreground/70">
          Full implementation in issue #89
        </p>
      </div>
    </div>
  );
}

interface OpenRouterPanelProps extends PanelProps {
  mode: 'byok' | 'managed';
}

/**
 * OpenRouter Panel - placeholder for issue #90
 */
function OpenRouterPanel({ mode, onDirtyChange: _onDirtyChange }: OpenRouterPanelProps) {
  return (
    <div className="p-4 border rounded-lg bg-muted/30">
      <div className="text-center text-muted-foreground py-6">
        <p className="font-medium">
          OpenRouter Configuration ({mode === 'byok' ? 'Your API Key' : 'Managed'})
        </p>
        <p className="text-sm mt-2">
          {mode === 'byok'
            ? 'Use your own OpenRouter API key for cloud models.'
            : 'Use CodeCompass-provided access to cloud models.'}
        </p>
        <p className="text-xs mt-4 text-muted-foreground/70">
          Full implementation in issue #90
        </p>
      </div>
    </div>
  );
}
