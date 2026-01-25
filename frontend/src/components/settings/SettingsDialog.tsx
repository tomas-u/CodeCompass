'use client';

import { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
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
import { ScrollArea } from '@/components/ui/scroll-area';
import { LLMSettingsPanel } from './LLMSettingsPanel';

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

  // Sync activeTab with defaultTab when dialog opens or defaultTab changes
  useEffect(() => {
    if (open) {
      setActiveTab(defaultTab);
    }
  }, [open, defaultTab]);

  // Handle tab change
  const handleTabChange = (value: string) => {
    setActiveTab(value as SettingsTab);
  };

  // Handle cancel - discard changes and close
  const handleCancel = () => {
    // TODO: Reset form state when store is implemented
    onOpenChange(false);
  };

  // Handle test connection
  const handleTestConnection = async () => {
    setIsTesting(true);
    try {
      // TODO: Implement validation via store when available
      // For now, simulate a test
      await new Promise((resolve) => setTimeout(resolve, 1000));
    } finally {
      setIsTesting(false);
    }
  };

  // Handle save
  const handleSave = async () => {
    setIsSaving(true);
    try {
      // TODO: Implement save via store when available
      // For now, simulate a save
      await new Promise((resolve) => setTimeout(resolve, 500));
      onOpenChange(false);
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
          <TabsList className="w-full justify-start">
            <TabsTrigger value="llm">LLM</TabsTrigger>
            <TabsTrigger value="embedding">Embedding</TabsTrigger>
            <TabsTrigger value="analysis">Analysis</TabsTrigger>
          </TabsList>

          <ScrollArea className="flex-1 mt-4">
            <TabsContent value="llm" className="mt-0 min-h-[300px]">
              <LLMSettingsPanel />
            </TabsContent>

            <TabsContent value="embedding" className="mt-0 min-h-[300px]">
              <EmbeddingSettingsPanel />
            </TabsContent>

            <TabsContent value="analysis" className="mt-0 min-h-[300px]">
              <AnalysisSettingsPanel />
            </TabsContent>
          </ScrollArea>
        </Tabs>

        <DialogFooter className="mt-4 gap-2 sm:gap-0">
          <Button variant="outline" onClick={handleCancel} disabled={isSaving}>
            Cancel
          </Button>
          <Button
            variant="outline"
            onClick={handleTestConnection}
            disabled={isSaving || isTesting}
          >
            {isTesting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Test Connection
          </Button>
          <Button onClick={handleSave} disabled={isSaving || isTesting}>
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
