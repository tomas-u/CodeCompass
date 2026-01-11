/**
 * Health Check Component
 *
 * Debug component to test API connectivity
 * Shows backend health status and version
 */

'use client';

import { useEffect, useState } from 'react';
import { Activity, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api';
import { getErrorMessage } from '@/lib/api-error';
import type { HealthResponse } from '@/types/api';

export function HealthCheck() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const response = await api.healthCheck();
        setHealth(response);
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setIsLoading(false);
      }
    };

    checkHealth();
  }, []);

  const formatUptime = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          Backend Health
        </CardTitle>
        <CardDescription>
          API connectivity and status check
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <div className="animate-spin rounded-full border-2 border-muted border-t-primary h-4 w-4" />
            Checking connection...
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span>{error}</span>
          </div>
        )}

        {health && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-500" />
              <span className="font-medium">Connected</span>
              <Badge variant="outline" className="ml-auto">
                v{health.version}
              </Badge>
            </div>

            <div className="grid grid-cols-2 gap-4 pt-2">
              <div>
                <p className="text-xs text-muted-foreground">Status</p>
                <p className="font-medium capitalize">{health.status}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Uptime</p>
                <p className="font-medium">{formatUptime(health.uptime_seconds)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">LLM Provider</p>
                <p className="font-medium capitalize">{health.llm_provider}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">LLM Status</p>
                <p className="font-medium capitalize">{health.llm_status}</p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
