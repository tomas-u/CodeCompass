'use client';

import { useState, useEffect, useCallback } from 'react';
import { Loader2, RefreshCw, Trash2, Download } from 'lucide-react';
import { cn } from '@/lib/utils';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import type { HardwareInfo, OllamaModel } from '@/types/api';

export interface OllamaContainerPanelProps {
  /** Currently selected model */
  selectedModel?: string;
  /** Callback when model selection changes */
  onModelChange?: (model: string) => void;
  /** Callback when form becomes dirty */
  onDirtyChange?: (dirty: boolean) => void;
}

/**
 * Container Ollama configuration panel.
 *
 * Displays hardware info, available models list with recommendations,
 * and model pull functionality.
 */
export function OllamaContainerPanel({
  selectedModel: initialModel = '',
  onModelChange,
  onDirtyChange,
}: OllamaContainerPanelProps) {
  const [selectedModel, setSelectedModel] = useState(initialModel);
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [hardwareInfo, setHardwareInfo] = useState<HardwareInfo | null>(null);
  const [isLoadingModels, setIsLoadingModels] = useState(true);
  const [isLoadingHardware, setIsLoadingHardware] = useState(true);
  const [modelsError, setModelsError] = useState<string | null>(null);
  const [hardwareError, setHardwareError] = useState<string | null>(null);

  // Fetch hardware info
  const fetchHardware = useCallback(async () => {
    setIsLoadingHardware(true);
    setHardwareError(null);
    try {
      const info = await api.getHardwareInfo();
      setHardwareInfo(info);
    } catch (err) {
      setHardwareError(err instanceof Error ? err.message : 'Failed to detect hardware');
    } finally {
      setIsLoadingHardware(false);
    }
  }, []);

  // Fetch available models
  const fetchModels = useCallback(async () => {
    setIsLoadingModels(true);
    setModelsError(null);
    try {
      const response = await api.listModels();
      setModels(response.models);
    } catch (err) {
      setModelsError(err instanceof Error ? err.message : 'Failed to load models');
    } finally {
      setIsLoadingModels(false);
    }
  }, []);

  // Fetch data on mount
  useEffect(() => {
    fetchHardware();
    fetchModels();
  }, [fetchHardware, fetchModels]);

  // Handle model selection
  const handleModelSelect = (model: string) => {
    setSelectedModel(model);
    onModelChange?.(model);
    onDirtyChange?.(true);
  };

  // Handle model delete
  const handleDeleteModel = async (modelName: string) => {
    try {
      await api.deleteModel(modelName);
      // Refresh model list after deletion
      await fetchModels();
      // Clear selection if deleted model was selected
      if (selectedModel === modelName) {
        setSelectedModel('');
        onModelChange?.('');
      }
    } catch (err) {
      setModelsError(err instanceof Error ? err.message : 'Failed to delete model');
    }
  };

  // Check if a model is recommended
  const isRecommended = (modelName: string): boolean => {
    if (!hardwareInfo?.recommendations.recommended_models) return false;
    return hardwareInfo.recommendations.recommended_models.some(
      (r) => modelName.includes(r.name) || r.name.includes(modelName.split(':')[0])
    );
  };

  return (
    <div className="space-y-6">
      {/* Hardware Info */}
      <HardwareInfoCard
        info={hardwareInfo}
        isLoading={isLoadingHardware}
        error={hardwareError}
      />

      {/* Model Selector */}
      <ModelSelector
        models={models}
        selectedModel={selectedModel}
        onSelect={handleModelSelect}
        onDelete={handleDeleteModel}
        onRefresh={fetchModels}
        isLoading={isLoadingModels}
        error={modelsError}
        isRecommended={isRecommended}
      />

      {/* Model Puller */}
      <ModelPuller onPullComplete={fetchModels} />
    </div>
  );
}

// ============================================================================
// Hardware Info Card
// ============================================================================

interface HardwareInfoCardProps {
  info: HardwareInfo | null;
  isLoading: boolean;
  error: string | null;
}

function HardwareInfoCard({ info, isLoading, error }: HardwareInfoCardProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Hardware Detected</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-4 w-36" />
          <Skeleton className="h-4 w-52" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Hardware Detected</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">{error}</p>
        </CardContent>
      </Card>
    );
  }

  if (!info) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Hardware Detected</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-muted-foreground">GPU:</span>
          <span>{info.gpu.detected ? info.gpu.name : 'Not detected'}</span>
        </div>
        {info.gpu.detected && info.gpu.vram_available_gb != null && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">VRAM:</span>
            <span>{info.gpu.vram_available_gb.toFixed(1)} GB available</span>
          </div>
        )}
        <div className="flex justify-between">
          <span className="text-muted-foreground">RAM:</span>
          <span>{info.cpu.ram_available_gb.toFixed(1)} GB available</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Recommended:</span>
          <span>{info.recommendations.max_model_params} models</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Inference:</span>
          <Badge variant="secondary">{info.recommendations.inference_mode}</Badge>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Model Selector
// ============================================================================

interface ModelSelectorProps {
  models: OllamaModel[];
  selectedModel: string;
  onSelect: (model: string) => void;
  onDelete: (model: string) => void;
  onRefresh: () => void;
  isLoading: boolean;
  error: string | null;
  isRecommended: (model: string) => boolean;
}

function ModelSelector({
  models,
  selectedModel,
  onSelect,
  onDelete,
  onRefresh,
  isLoading,
  error,
  isRecommended,
}: ModelSelectorProps) {
  const [deletingModel, setDeletingModel] = useState<string | null>(null);

  const handleDelete = async (modelName: string) => {
    setDeletingModel(modelName);
    try {
      await onDelete(modelName);
    } finally {
      setDeletingModel(null);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <Label className="text-base font-medium">Available Models</Label>
        <Button
          variant="ghost"
          size="sm"
          onClick={onRefresh}
          disabled={isLoading}
          aria-label="Refresh models"
        >
          <RefreshCw className={cn('h-4 w-4', isLoading && 'animate-spin')} />
        </Button>
      </div>

      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}

      {isLoading ? (
        <div className="border rounded-lg p-4 space-y-3">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      ) : models.length === 0 ? (
        <div className="border rounded-lg p-6 text-center text-muted-foreground">
          <p>No models installed.</p>
          <p className="text-sm mt-1">Pull a model below to get started.</p>
        </div>
      ) : (
        <RadioGroup
          value={selectedModel}
          onValueChange={onSelect}
          className="border rounded-lg divide-y"
          aria-label="Select a model"
        >
          {models.map((model) => (
            <label
              key={model.name}
              className={cn(
                'flex items-center justify-between p-3 cursor-pointer',
                'hover:bg-accent/50 transition-colors',
                selectedModel === model.name && 'bg-accent'
              )}
            >
              <div className="flex items-center gap-3">
                <RadioGroupItem value={model.name} id={`model-${model.name}`} />
                <span className="font-medium text-sm">{model.name}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">{model.size}</span>
                {isRecommended(model.name) && (
                  <Badge variant="secondary">Recommended</Badge>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    handleDelete(model.name);
                  }}
                  disabled={deletingModel === model.name}
                  aria-label={`Delete ${model.name}`}
                  className="h-7 w-7 p-0"
                >
                  {deletingModel === model.name ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Trash2 className="h-3.5 w-3.5 text-muted-foreground hover:text-destructive" />
                  )}
                </Button>
              </div>
            </label>
          ))}
        </RadioGroup>
      )}
    </div>
  );
}

// ============================================================================
// Model Puller
// ============================================================================

interface ModelPullerProps {
  onPullComplete: () => void;
}

function ModelPuller({ onPullComplete }: ModelPullerProps) {
  const [modelName, setModelName] = useState('');
  const [isPulling, setIsPulling] = useState(false);
  const [pullMessage, setPullMessage] = useState<string | null>(null);
  const [pullError, setPullError] = useState<string | null>(null);

  const handlePull = async () => {
    if (!modelName.trim()) return;

    setIsPulling(true);
    setPullError(null);
    setPullMessage(null);

    try {
      const response = await api.pullModel(modelName.trim());
      setPullMessage(response.message);
      setModelName('');
      // Refresh model list after pull
      onPullComplete();
    } catch (err) {
      setPullError(err instanceof Error ? err.message : 'Failed to pull model');
    } finally {
      setIsPulling(false);
    }
  };

  return (
    <div className="space-y-3">
      <Label className="text-base font-medium">Pull New Model</Label>
      <div className="flex gap-2">
        <Input
          placeholder="e.g., mistral:7b, phi3:latest"
          value={modelName}
          onChange={(e) => setModelName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && modelName.trim()) {
              handlePull();
            }
          }}
          disabled={isPulling}
          aria-label="Model name to pull"
        />
        <Button
          onClick={handlePull}
          disabled={!modelName.trim() || isPulling}
        >
          {isPulling ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Download className="mr-2 h-4 w-4" />
          )}
          Pull
        </Button>
      </div>
      <p className="text-xs text-muted-foreground">
        Enter a model name from the Ollama library
      </p>
      {pullMessage && (
        <p className="text-sm text-green-600 dark:text-green-400">{pullMessage}</p>
      )}
      {pullError && (
        <p className="text-sm text-destructive">{pullError}</p>
      )}
    </div>
  );
}
