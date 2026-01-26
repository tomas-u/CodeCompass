'use client';

import { useState } from 'react';
import { Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';

export type ApiFormat = 'auto' | 'ollama' | 'openai';

interface QuickConfig {
  label: string;
  url: string;
  format: ApiFormat;
}

const QUICK_CONFIGS: QuickConfig[] = [
  { label: 'LM Studio', url: 'http://localhost:1234', format: 'openai' },
  { label: 'Ollama', url: 'http://localhost:11434', format: 'ollama' },
  { label: 'llama.cpp', url: 'http://localhost:8080', format: 'openai' },
  { label: 'vLLM', url: 'http://localhost:8000', format: 'openai' },
];

export interface ExternalLLMPanelProps {
  /** Initial base URL */
  initialBaseUrl?: string;
  /** Initial API format */
  initialApiFormat?: ApiFormat;
  /** Initial model name */
  initialModel?: string;
  /** Callback when configuration changes */
  onConfigChange?: (config: {
    baseUrl: string;
    apiFormat: ApiFormat;
    model: string;
  }) => void;
  /** Callback when form becomes dirty */
  onDirtyChange?: (dirty: boolean) => void;
}

/**
 * External LLM configuration panel.
 *
 * Supports connecting to LM Studio, llama.cpp, vLLM, or external Ollama
 * instances with URL input, API format detection, and model discovery.
 */
export function ExternalLLMPanel({
  initialBaseUrl = 'http://localhost:1234',
  initialApiFormat = 'auto',
  initialModel = '',
  onConfigChange,
  onDirtyChange,
}: ExternalLLMPanelProps) {
  const [baseUrl, setBaseUrl] = useState(initialBaseUrl);
  const [apiFormat, setApiFormat] = useState<ApiFormat>(initialApiFormat);
  const [selectedModel, setSelectedModel] = useState(initialModel);
  const [manualModel, setManualModel] = useState('');
  const [detectedModels, setDetectedModels] = useState<string[]>([]);
  const [isDetecting, setIsDetecting] = useState(false);
  const [detectStatus, setDetectStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [detectError, setDetectError] = useState<string | null>(null);

  const markDirty = () => onDirtyChange?.(true);

  const emitConfig = (overrides?: {
    baseUrl?: string;
    apiFormat?: ApiFormat;
    model?: string;
  }) => {
    onConfigChange?.({
      baseUrl: overrides?.baseUrl ?? baseUrl,
      apiFormat: overrides?.apiFormat ?? apiFormat,
      model: overrides?.model ?? (selectedModel || manualModel),
    });
  };

  // Handle URL change - reset detection state and model selection
  const handleUrlChange = (url: string) => {
    setBaseUrl(url);
    setDetectStatus('idle');
    setDetectedModels([]);
    setSelectedModel('');
    markDirty();
    emitConfig({ baseUrl: url });
  };

  // Handle API format change
  const handleApiFormatChange = (format: string) => {
    const newFormat = format as ApiFormat;
    setApiFormat(newFormat);
    markDirty();
    emitConfig({ apiFormat: newFormat });
  };

  // Handle quick config selection
  const handleQuickConfig = (config: QuickConfig) => {
    setBaseUrl(config.url);
    setApiFormat(config.format);
    setDetectStatus('idle');
    setDetectedModels([]);
    markDirty();
    emitConfig({ baseUrl: config.url, apiFormat: config.format });
  };

  // Handle detect / test connection
  const handleDetect = async () => {
    if (!baseUrl.trim()) return;

    setIsDetecting(true);
    setDetectError(null);
    setDetectStatus('idle');
    setDetectedModels([]);

    try {
      // Use the test connection endpoint to validate
      // Backend uses api_format field to distinguish Ollama vs OpenAI-compatible
      const result = await api.testConnection({
        provider: 'ollama_external',
        model: selectedModel || manualModel || 'test',
        base_url: baseUrl,
      });

      if (result.success) {
        setDetectStatus('success');

        // Try to list models (only supported for Ollama-style APIs)
        if (apiFormat === 'ollama' || apiFormat === 'auto') {
          try {
            const modelsResponse = await api.listModels();
            setDetectedModels(modelsResponse.models.map((m) => m.name));
          } catch {
            // Model listing may not work for all configurations
          }
        }
      } else {
        setDetectStatus('error');
        setDetectError(result.error || 'Connection failed');
      }
    } catch (err) {
      setDetectStatus('error');
      setDetectError(err instanceof Error ? err.message : 'Failed to connect');
    } finally {
      setIsDetecting(false);
    }
  };

  // Handle model selection from detected list
  const handleModelSelect = (model: string) => {
    setSelectedModel(model);
    setManualModel('');
    markDirty();
    emitConfig({ model });
  };

  // Handle manual model entry
  const handleManualModelChange = (model: string) => {
    setManualModel(model);
    setSelectedModel('');
    markDirty();
    emitConfig({ model });
  };

  return (
    <div className="space-y-6">
      {/* Server URL */}
      <ServerUrlInput
        value={baseUrl}
        onChange={handleUrlChange}
        onDetect={handleDetect}
        isDetecting={isDetecting}
        detectStatus={detectStatus}
      />

      {/* Connection status */}
      {detectStatus !== 'idle' && (
        <ConnectionStatus status={detectStatus} error={detectError} />
      )}

      {/* API Format */}
      <ApiFormatSelector value={apiFormat} onChange={handleApiFormatChange} />

      {/* Quick Config */}
      <QuickConfigButtons onSelect={handleQuickConfig} currentUrl={baseUrl} />

      {/* Model Selection */}
      <ModelSelection
        models={detectedModels}
        selectedModel={selectedModel}
        onSelectModel={handleModelSelect}
        manualModel={manualModel}
        onManualModelChange={handleManualModelChange}
      />
    </div>
  );
}

// ============================================================================
// Server URL Input
// ============================================================================

interface ServerUrlInputProps {
  value: string;
  onChange: (url: string) => void;
  onDetect: () => void;
  isDetecting: boolean;
  detectStatus: 'idle' | 'success' | 'error';
}

function ServerUrlInput({
  value,
  onChange,
  onDetect,
  isDetecting,
  detectStatus,
}: ServerUrlInputProps) {
  return (
    <div className="space-y-2">
      <Label className="text-base font-medium">Server URL</Label>
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Input
            placeholder="http://localhost:1234"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && value.trim()) onDetect();
            }}
            aria-label="Server URL"
            className={cn(
              detectStatus === 'success' && 'border-green-500 pr-8',
              detectStatus === 'error' && 'border-destructive pr-8'
            )}
          />
          {detectStatus === 'success' && (
            <CheckCircle2 className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-green-500" />
          )}
          {detectStatus === 'error' && (
            <XCircle className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-destructive" />
          )}
        </div>
        <Button
          variant="outline"
          onClick={onDetect}
          disabled={isDetecting || !value.trim()}
        >
          {isDetecting ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : null}
          Detect
        </Button>
      </div>
    </div>
  );
}

// ============================================================================
// Connection Status
// ============================================================================

interface ConnectionStatusProps {
  status: 'success' | 'error';
  error: string | null;
}

function ConnectionStatus({ status, error }: ConnectionStatusProps) {
  if (status === 'success') {
    return (
      <p className="text-sm text-green-600 dark:text-green-400">
        Connected successfully
      </p>
    );
  }

  return (
    <p className="text-sm text-destructive">
      {error || 'Connection failed'}
    </p>
  );
}

// ============================================================================
// API Format Selector
// ============================================================================

interface ApiFormatSelectorProps {
  value: ApiFormat;
  onChange: (format: string) => void;
}

function ApiFormatSelector({ value, onChange }: ApiFormatSelectorProps) {
  return (
    <div className="space-y-2">
      <Label className="text-base font-medium">API Format</Label>
      <RadioGroup
        value={value}
        onValueChange={onChange}
        className="flex gap-4"
        aria-label="Select API format"
      >
        <div className="flex items-center gap-2">
          <RadioGroupItem value="auto" id="format-auto" />
          <Label htmlFor="format-auto" className="font-normal cursor-pointer">
            Auto-detect
          </Label>
        </div>
        <div className="flex items-center gap-2">
          <RadioGroupItem value="ollama" id="format-ollama" />
          <Label htmlFor="format-ollama" className="font-normal cursor-pointer">
            Ollama API
          </Label>
        </div>
        <div className="flex items-center gap-2">
          <RadioGroupItem value="openai" id="format-openai" />
          <Label htmlFor="format-openai" className="font-normal cursor-pointer">
            OpenAI-compatible
          </Label>
        </div>
      </RadioGroup>
    </div>
  );
}

// ============================================================================
// Quick Config Buttons
// ============================================================================

interface QuickConfigButtonsProps {
  onSelect: (config: QuickConfig) => void;
  currentUrl: string;
}

function QuickConfigButtons({ onSelect, currentUrl }: QuickConfigButtonsProps) {
  return (
    <div className="space-y-2">
      <Label className="text-muted-foreground">Common Configurations</Label>
      <div className="flex flex-wrap gap-2">
        {QUICK_CONFIGS.map((config) => (
          <Button
            key={config.label}
            variant={currentUrl === config.url ? 'secondary' : 'outline'}
            size="sm"
            onClick={() => onSelect(config)}
          >
            {config.label}
          </Button>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// Model Selection
// ============================================================================

interface ModelSelectionProps {
  models: string[];
  selectedModel: string;
  onSelectModel: (model: string) => void;
  manualModel: string;
  onManualModelChange: (model: string) => void;
}

function ModelSelection({
  models,
  selectedModel,
  onSelectModel,
  manualModel,
  onManualModelChange,
}: ModelSelectionProps) {
  return (
    <div className="space-y-4">
      {/* Detected models list */}
      {models.length > 0 && (
        <div className="space-y-2">
          <Label className="text-base font-medium">Available Models</Label>
          <RadioGroup
            value={selectedModel}
            onValueChange={onSelectModel}
            className="border rounded-lg divide-y max-h-[200px] overflow-y-auto"
            aria-label="Select detected model"
          >
            {models.map((model) => (
              <label
                key={model}
                className={cn(
                  'flex items-center gap-3 p-3 cursor-pointer',
                  'hover:bg-accent/50 transition-colors',
                  selectedModel === model && 'bg-accent'
                )}
              >
                <RadioGroupItem value={model} id={`detected-${model}`} />
                <span className="text-sm font-medium">{model}</span>
              </label>
            ))}
          </RadioGroup>
        </div>
      )}

      {/* Manual model entry */}
      <div className="space-y-2">
        <Label className="text-base font-medium">
          {models.length > 0 ? 'Or enter model name manually' : 'Model Name'}
        </Label>
        <Input
          placeholder="e.g., mistral:7b, TheBloke/Mistral-7B-GGUF"
          value={manualModel}
          onChange={(e) => onManualModelChange(e.target.value)}
          aria-label="Manual model name"
        />
        {models.length === 0 && (
          <p className="text-xs text-muted-foreground">
            Click &quot;Detect&quot; to discover models from the server, or enter a model name manually.
          </p>
        )}
      </div>
    </div>
  );
}
