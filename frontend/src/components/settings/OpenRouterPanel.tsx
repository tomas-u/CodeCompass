'use client';

import { useState, useMemo } from 'react';
import { Loader2, CheckCircle2, XCircle, Info, ExternalLink } from 'lucide-react';
import { cn } from '@/lib/utils';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import type { OpenRouterModel } from '@/types/api';

export interface OpenRouterPanelProps {
  mode: 'byok' | 'managed';
  /** Callback when configuration changes */
  onConfigChange?: (config: {
    apiKey?: string;
    model: string;
  }) => void;
  /** Callback when form becomes dirty */
  onDirtyChange?: (dirty: boolean) => void;
}

/**
 * OpenRouter configuration panel.
 *
 * Supports two modes:
 * - BYOK (Bring Your Own Key): User enters their OpenRouter API key
 * - Managed: CodeCompass-provided access with limited model selection
 */
export function OpenRouterPanel({
  mode,
  onConfigChange,
  onDirtyChange,
}: OpenRouterPanelProps) {
  if (mode === 'managed') {
    return <ManagedModePanel onDirtyChange={onDirtyChange} onConfigChange={onConfigChange} />;
  }

  return <BYOKModePanel onConfigChange={onConfigChange} onDirtyChange={onDirtyChange} />;
}

// ============================================================================
// BYOK Mode Panel
// ============================================================================

interface BYOKModePanelProps {
  onConfigChange?: OpenRouterPanelProps['onConfigChange'];
  onDirtyChange?: (dirty: boolean) => void;
}

function BYOKModePanel({ onConfigChange, onDirtyChange }: BYOKModePanelProps) {
  const [apiKey, setApiKey] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [keyStatus, setKeyStatus] = useState<'valid' | 'invalid' | null>(null);
  const [keyError, setKeyError] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState('');
  const [models, setModels] = useState<OpenRouterModel[]>([]);
  const [isLoadingModels, setIsLoadingModels] = useState(false);
  const [filter, setFilter] = useState('');

  // Handle API key validation
  const handleValidate = async () => {
    if (!apiKey.trim()) return;

    setIsValidating(true);
    setKeyError(null);
    setKeyStatus(null);

    try {
      const result = await api.validateLLMConfig({
        provider_type: 'openrouter_byok',
        model: 'test',
        api_key: apiKey,
      });

      if (result.valid) {
        setKeyStatus('valid');
        // Fetch available models after validation
        fetchModels();
      } else {
        setKeyStatus('invalid');
        setKeyError(result.error || 'Invalid API key');
      }
    } catch (err) {
      setKeyStatus('invalid');
      setKeyError(err instanceof Error ? err.message : 'Validation failed');
    } finally {
      setIsValidating(false);
    }
  };

  // Fetch OpenRouter models
  const fetchModels = async () => {
    setIsLoadingModels(true);
    try {
      const response = await api.listOpenRouterModels();
      setModels(response.models);
    } catch {
      // Models may not be available without valid key
    } finally {
      setIsLoadingModels(false);
    }
  };

  // Handle API key change
  const handleApiKeyChange = (value: string) => {
    setApiKey(value);
    setKeyStatus(null);
    setKeyError(null);
    onDirtyChange?.(true);
  };

  // Handle model selection
  const handleModelSelect = (modelId: string) => {
    setSelectedModel(modelId);
    onDirtyChange?.(true);
    onConfigChange?.({ apiKey, model: modelId });
  };

  return (
    <div className="space-y-6">
      {/* API Key Input */}
      <ApiKeyInput
        value={apiKey}
        onChange={handleApiKeyChange}
        onValidate={handleValidate}
        isValidating={isValidating}
        status={keyStatus}
        error={keyError}
      />

      {/* Model Browser (shown after valid key) */}
      {keyStatus === 'valid' && (
        <ModelBrowser
          models={models}
          filter={filter}
          onFilterChange={setFilter}
          selectedModel={selectedModel}
          onSelectModel={handleModelSelect}
          isLoading={isLoadingModels}
        />
      )}
    </div>
  );
}

// ============================================================================
// Managed Mode Panel
// ============================================================================

interface ManagedModePanelProps {
  onConfigChange?: OpenRouterPanelProps['onConfigChange'];
  onDirtyChange?: (dirty: boolean) => void;
}

function ManagedModePanel({ onConfigChange, onDirtyChange }: ManagedModePanelProps) {
  const [selectedModel, setSelectedModel] = useState('');

  const handleModelSelect = (model: string) => {
    setSelectedModel(model);
    onDirtyChange?.(true);
    onConfigChange?.({ model });
  };

  return (
    <div className="space-y-4">
      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>Managed Access</AlertTitle>
        <AlertDescription>
          Cloud models are provided by CodeCompass. Usage may be limited
          based on available capacity.
        </AlertDescription>
      </Alert>

      <div className="space-y-3">
        <Label className="text-base font-medium">Select Model</Label>
        <RadioGroup
          value={selectedModel}
          onValueChange={handleModelSelect}
          className="border rounded-lg divide-y"
          aria-label="Select managed model"
        >
          {MANAGED_MODELS.map((model) => (
            <label
              key={model.id}
              className={cn(
                'flex items-center justify-between p-3 cursor-pointer',
                'hover:bg-accent/50 transition-colors',
                selectedModel === model.id && 'bg-accent'
              )}
            >
              <div className="flex items-center gap-3">
                <RadioGroupItem id={`managed-model-${model.id}`} value={model.id} />
                <div>
                  <span className="font-medium text-sm">{model.name}</span>
                  <p className="text-xs text-muted-foreground">{model.description}</p>
                </div>
              </div>
            </label>
          ))}
        </RadioGroup>
      </div>
    </div>
  );
}

const MANAGED_MODELS = [
  {
    id: 'anthropic/claude-3-haiku',
    name: 'Claude 3 Haiku',
    description: 'Fast, cost-effective model for code analysis',
  },
  {
    id: 'google/gemma-2-9b-it',
    name: 'Gemma 2 9B',
    description: 'Open model with good coding capabilities',
  },
  {
    id: 'meta-llama/llama-3.1-8b-instruct',
    name: 'Llama 3.1 8B',
    description: 'Open model for general coding tasks',
  },
];

// ============================================================================
// API Key Input
// ============================================================================

interface ApiKeyInputProps {
  value: string;
  onChange: (value: string) => void;
  onValidate: () => void;
  isValidating: boolean;
  status: 'valid' | 'invalid' | null;
  error: string | null;
}

function ApiKeyInput({
  value,
  onChange,
  onValidate,
  isValidating,
  status,
  error,
}: ApiKeyInputProps) {
  return (
    <div className="space-y-2">
      <Label className="text-base font-medium">API Key</Label>
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Input
            type="password"
            placeholder="sk-or-v1-..."
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && value.trim()) onValidate();
            }}
            aria-label="OpenRouter API key"
            className={cn(
              status === 'valid' && 'border-green-500 pr-8',
              status === 'invalid' && 'border-destructive pr-8'
            )}
          />
          {status === 'valid' && (
            <CheckCircle2 className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-green-500" />
          )}
          {status === 'invalid' && (
            <XCircle className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-destructive" />
          )}
        </div>
        <Button
          variant="outline"
          onClick={onValidate}
          disabled={isValidating || !value.trim()}
        >
          {isValidating ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : null}
          Validate
        </Button>
      </div>
      {status === 'valid' && (
        <p className="text-sm text-green-600 dark:text-green-400 flex items-center gap-1">
          <CheckCircle2 className="h-3.5 w-3.5" /> Valid API key
        </p>
      )}
      {status === 'invalid' && (
        <p className="text-sm text-destructive flex items-center gap-1">
          <XCircle className="h-3.5 w-3.5" /> {error || 'Invalid API key'}
        </p>
      )}
      <p className="text-xs text-muted-foreground">
        Get your API key at{' '}
        <a
          href="https://openrouter.ai/keys"
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary hover:underline inline-flex items-center gap-1"
        >
          openrouter.ai/keys
          <ExternalLink className="h-3 w-3" />
        </a>
      </p>
    </div>
  );
}

// ============================================================================
// Model Browser
// ============================================================================

interface ModelBrowserProps {
  models: OpenRouterModel[];
  filter: string;
  onFilterChange: (filter: string) => void;
  selectedModel: string;
  onSelectModel: (modelId: string) => void;
  isLoading: boolean;
}

function ModelBrowser({
  models,
  filter,
  onFilterChange,
  selectedModel,
  onSelectModel,
  isLoading,
}: ModelBrowserProps) {
  const filteredModels = useMemo(() => {
    if (!filter.trim()) return models;
    const lower = filter.toLowerCase();
    return models.filter(
      (m) =>
        m.name.toLowerCase().includes(lower) ||
        m.id.toLowerCase().includes(lower) ||
        m.provider.toLowerCase().includes(lower)
    );
  }, [models, filter]);

  if (isLoading) {
    return (
      <div className="space-y-3">
        <Label className="text-base font-medium">Select Model</Label>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading models...
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <Label className="text-base font-medium">Select Model</Label>

      {/* Search filter */}
      <Input
        placeholder="Search models..."
        value={filter}
        onChange={(e) => onFilterChange(e.target.value)}
        aria-label="Search models"
      />

      {/* Model table */}
      {filteredModels.length === 0 ? (
        <div className="border rounded-lg p-4 text-center text-sm text-muted-foreground">
          {models.length === 0
            ? 'No models available.'
            : 'No models match your search.'}
        </div>
      ) : (
        <div className="border rounded-lg max-h-[300px] overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 sticky top-0">
              <tr>
                <th className="p-2 text-left font-medium">Model</th>
                <th className="p-2 text-right font-medium">Input</th>
                <th className="p-2 text-right font-medium">Output</th>
                <th className="p-2 text-right font-medium">Context</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filteredModels.map((model) => (
                <tr
                  key={model.id}
                  className={cn(
                    'cursor-pointer hover:bg-accent/50 transition-colors',
                    selectedModel === model.id && 'bg-accent'
                  )}
                  onClick={() => onSelectModel(model.id)}
                >
                  <td className="p-2">
                    <div className="flex items-center gap-2">
                      <input
                        type="radio"
                        name="openrouter-model"
                        checked={selectedModel === model.id}
                        onChange={() => onSelectModel(model.id)}
                        aria-label={model.name}
                        className="accent-primary"
                      />
                      <span className="font-medium truncate max-w-[200px]">
                        {model.name}
                      </span>
                    </div>
                  </td>
                  <td className="p-2 text-right text-muted-foreground whitespace-nowrap">
                    ${model.pricing.input_per_million}/M
                  </td>
                  <td className="p-2 text-right text-muted-foreground whitespace-nowrap">
                    ${model.pricing.output_per_million}/M
                  </td>
                  <td className="p-2 text-right text-muted-foreground whitespace-nowrap">
                    {formatContextLength(model.context_length)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Selected model info */}
      {selectedModel && (
        <p className="text-sm text-muted-foreground">
          Selected: <span className="font-medium">{selectedModel}</span>
        </p>
      )}
    </div>
  );
}

// ============================================================================
// Helpers
// ============================================================================

/**
 * Format context length for display (e.g., 200000 -> "200K", 1000000 -> "1M")
 */
function formatContextLength(tokens: number): string {
  if (tokens >= 1_000_000) {
    const m = tokens / 1_000_000;
    return m % 1 === 0 ? `${m}M` : `${m.toFixed(1)}M`;
  }
  if (tokens >= 1_000) {
    const k = tokens / 1_000;
    return k % 1 === 0 ? `${k}K` : `${k.toFixed(1)}K`;
  }
  return tokens.toString();
}
