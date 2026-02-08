'use client';

import { useState, useEffect } from 'react';
import { Loader2, CheckCircle2, XCircle } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { LLMSettingsPanel } from './LLMSettingsPanel';
import { useAppStore } from '@/lib/store';
import type { LLMConfigUpdate, LLMValidationResponse } from '@/types/settings';

export type SettingsTab = 'llm' | 'embedding' | 'analysis';

export interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  defaultTab?: SettingsTab;
}

/**
 * Main Settings Dialog with tabbed interface for LLM, Embedding, and Analysis settings.
 *
 * Usage:
 * ```tsx
 * <SettingsDialog
 *   open={isOpen}
 *   onOpenChange={setIsOpen}
 *   defaultTab="llm"
 * />
 * ```
 */
export function SettingsDialog({
  open,
  onOpenChange,
  defaultTab = 'llm',
}: SettingsDialogProps) {
  const [activeTab, setActiveTab] = useState<SettingsTab>(defaultTab);
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [pendingConfig, setPendingConfig] = useState<LLMConfigUpdate | null>(null);
  const [validationResult, setValidationResult] = useState<LLMValidationResponse | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Sync activeTab with defaultTab when dialog opens or defaultTab changes
  useEffect(() => {
    if (open) {
      setActiveTab(defaultTab);
      // Reset transient state when dialog opens
      setPendingConfig(null);
      setValidationResult(null);
      setSaveError(null);
    }
  }, [open, defaultTab]);

  // Handle tab change
  const handleTabChange = (value: string) => {
    setActiveTab(value as SettingsTab);
  };

  // Capture config changes from LLMSettingsPanel
  const handleConfigChange = (config: LLMConfigUpdate) => {
    setPendingConfig(config);
    // Clear previous validation/error when config changes
    setValidationResult(null);
    setSaveError(null);
  };

  // Handle cancel - discard changes and close
  const handleCancel = () => {
    onOpenChange(false);
  };

  // Handle test connection
  const handleTestConnection = async () => {
    if (!pendingConfig) return;
    setIsTesting(true);
    setValidationResult(null);
    try {
      const result = await useAppStore.getState().validateLLMConfig(pendingConfig);
      setValidationResult(result);
    } finally {
      setIsTesting(false);
    }
  };

  // Handle save
  const handleSave = async () => {
    if (!pendingConfig) return;
    setIsSaving(true);
    setSaveError(null);
    try {
      const success = await useAppStore.getState().updateLLMConfig(pendingConfig);
      if (success) {
        onOpenChange(false);
      } else {
        setSaveError(useAppStore.getState().llmError || 'Failed to save configuration');
      }
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
          <DialogDescription>
            Configure LLM providers, embedding models, and analysis options.
          </DialogDescription>
        </DialogHeader>

        <Tabs
          value={activeTab}
          onValueChange={handleTabChange}
          className="flex-1 flex flex-col min-h-0"
        >
          <TabsList className="w-full justify-start shrink-0">
            <TabsTrigger value="llm">LLM</TabsTrigger>
            <TabsTrigger value="embedding">Embedding</TabsTrigger>
            <TabsTrigger value="analysis">Analysis</TabsTrigger>
          </TabsList>

          <div className="flex-1 min-h-0 overflow-y-auto mt-4">
            <TabsContent value="llm" className="mt-0">
              <LLMSettingsPanel onConfigChange={handleConfigChange} />
            </TabsContent>

            <TabsContent value="embedding" className="mt-0">
              <EmbeddingSettingsPanel />
            </TabsContent>

            <TabsContent value="analysis" className="mt-0">
              <AnalysisSettingsPanel />
            </TabsContent>
          </div>
        </Tabs>

        {/* Validation / Save feedback */}
        {validationResult && (
          <div className={`flex items-center gap-2 text-sm px-1 ${validationResult.valid ? 'text-green-600 dark:text-green-400' : 'text-destructive'}`}>
            {validationResult.valid ? (
              <>
                <CheckCircle2 className="h-4 w-4 shrink-0" />
                <span>
                  Connection successful
                  {validationResult.test_response_ms != null && ` (${validationResult.test_response_ms}ms)`}
                </span>
              </>
            ) : (
              <>
                <XCircle className="h-4 w-4 shrink-0" />
                <span>{validationResult.error || 'Validation failed'}</span>
              </>
            )}
          </div>
        )}
        {saveError && (
          <div className="flex items-center gap-2 text-sm text-destructive px-1">
            <XCircle className="h-4 w-4 shrink-0" />
            <span>{saveError}</span>
          </div>
        )}

        <DialogFooter className="mt-4 gap-2 sm:gap-0 shrink-0">
          <Button variant="outline" onClick={handleCancel} disabled={isSaving}>
            Cancel
          </Button>
          <Button
            variant="outline"
            onClick={handleTestConnection}
            disabled={isSaving || isTesting || !pendingConfig}
          >
            {isTesting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Test Connection
          </Button>
          <Button onClick={handleSave} disabled={isSaving || isTesting || !pendingConfig}>
            {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Save
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ============================================================================
// Placeholder Panels (to be replaced with full implementations)
// ============================================================================

/**
 * Embedding Settings Panel - placeholder for future implementation
 */
function EmbeddingSettingsPanel() {
  return (
    <div className="space-y-4 p-4 border rounded-lg bg-muted/30">
      <div className="text-center text-muted-foreground py-8">
        <p className="text-lg font-medium">Embedding Settings</p>
        <p className="text-sm mt-2">
          Configure embedding model and vector store settings.
        </p>
        <p className="text-xs mt-4 text-muted-foreground/70">
          Coming soon
        </p>
      </div>
    </div>
  );
}

/**
 * Analysis Settings Panel - placeholder for future implementation
 */
function AnalysisSettingsPanel() {
  return (
    <div className="space-y-4 p-4 border rounded-lg bg-muted/30">
      <div className="text-center text-muted-foreground py-8">
        <p className="text-lg font-medium">Analysis Settings</p>
        <p className="text-sm mt-2">
          Configure code analysis options and language support.
        </p>
        <p className="text-xs mt-4 text-muted-foreground/70">
          Coming soon
        </p>
      </div>
    </div>
  );
}
