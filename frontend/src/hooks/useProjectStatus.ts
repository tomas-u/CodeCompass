/**
 * useProjectStatus Hook
 *
 * Polls project analysis status and updates project state in real-time.
 * Automatically stops polling when analysis completes or fails.
 */

import { useEffect, useRef, useCallback } from 'react';
import { api } from '@/lib/api';
import { getErrorMessage } from '@/lib/api-error';
import type { Project, Analysis } from '@/types/api';

const POLLING_INTERVAL = 2000; // 2 seconds

interface UseProjectStatusOptions {
  projectId: string;
  onStatusUpdate?: (project: Partial<Project>) => void;
  onAnalysisUpdate?: (analysis: Analysis) => void;
  onError?: (error: string) => void;
  enabled?: boolean; // Allow disabling polling
}

interface UseProjectStatusReturn {
  isPolling: boolean;
  lastUpdate: Date | null;
  error: string | null;
}

export function useProjectStatus({
  projectId,
  onStatusUpdate,
  onAnalysisUpdate,
  onError,
  enabled = true,
}: UseProjectStatusOptions): UseProjectStatusReturn {
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const lastUpdateRef = useRef<Date | null>(null);
  const errorRef = useRef<string | null>(null);
  const isPollingRef = useRef<boolean>(false);

  // Fetch project and analysis status
  const fetchStatus = useCallback(async () => {
    try {
      // Fetch project data to get current status
      const project = await api.getProject(projectId);

      // Update last poll time
      lastUpdateRef.current = new Date();
      errorRef.current = null;

      // Notify status update
      if (onStatusUpdate) {
        onStatusUpdate(project);
      }

      // Check if we should stop polling
      const terminalStates = ['ready', 'failed'];
      if (terminalStates.includes(project.status)) {
        stopPolling();
        return;
      }

      // If status indicates analysis in progress, fetch analysis details
      const activeStates = ['analyzing', 'scanning', 'cloning'];
      if (activeStates.includes(project.status)) {
        try {
          const analysis = await api.getAnalysisStatus(projectId);
          if (onAnalysisUpdate) {
            onAnalysisUpdate(analysis);
          }
        } catch (analysisError) {
          // Analysis endpoint might not be available yet, continue polling
          console.debug('Analysis not available yet:', getErrorMessage(analysisError));
        }
      }
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      errorRef.current = errorMessage;

      if (onError) {
        onError(errorMessage);
      }

      // Don't stop polling on error - might be temporary
      console.error('Status polling error:', errorMessage);
    }
  }, [projectId, onStatusUpdate, onAnalysisUpdate, onError]);

  // Start polling
  const startPolling = useCallback(() => {
    if (isPollingRef.current || !enabled) return;

    isPollingRef.current = true;

    // Fetch immediately
    fetchStatus();

    // Set up interval
    intervalRef.current = setInterval(fetchStatus, POLLING_INTERVAL);
  }, [fetchStatus, enabled]);

  // Stop polling
  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    isPollingRef.current = false;
  }, []);

  // Start polling when enabled changes
  useEffect(() => {
    if (enabled) {
      startPolling();
    } else {
      stopPolling();
    }

    // Cleanup on unmount
    return () => {
      stopPolling();
    };
  }, [enabled, startPolling, stopPolling]);

  return {
    isPolling: isPollingRef.current,
    lastUpdate: lastUpdateRef.current,
    error: errorRef.current,
  };
}
