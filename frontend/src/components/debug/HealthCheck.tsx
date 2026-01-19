/**
 * Health Check Component
 *
 * Debug component to test API connectivity
 * Shows backend health status and version
 */

'use client';

import { useEffect, useState } from 'react';
import { Activity, AlertCircle, CheckCircle2, Trash2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { api } from '@/lib/api';
import { getErrorMessage } from '@/lib/api-error';
import type { HealthResponse } from '@/types/api';

export function HealthCheck() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isClearing, setIsClearing] = useState(false);

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

  const handleClearDatabase = async () => {
    if (!confirm('⚠️ Clear all data from database?\n\nThis will delete all projects. This action cannot be undone.')) {
      return;
    }

    setIsClearing(true);
    try {
      const result = await api.clearDatabase();
      alert(`✅ Database cleared!\n\n${result.records_deleted.projects} projects deleted`);
      window.location.reload(); // Refresh to update UI
    } catch (error) {
      alert(`❌ Failed to clear database: ${getErrorMessage(error)}`);
    } finally {
      setIsClearing(false);
    }
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
                <Badge variant={
                  health.llm_status === 'ready' ? 'default' :
                  health.llm_status === 'idle' ? 'secondary' :
                  health.llm_status === 'connected' ? 'secondary' :
                  'destructive'
                }>
                  {health.llm_status}
                </Badge>
              </div>
              <div className="col-span-2">
                <p className="text-xs text-muted-foreground">Model Loaded</p>
                <p className="font-medium">
                  {health.llm_model_loaded || <span className="text-muted-foreground italic">None (will load on first request)</span>}
                </p>
              </div>
              {health.llm_models_available.length > 0 && (
                <div className="col-span-2">
                  <p className="text-xs text-muted-foreground">Available Models</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {health.llm_models_available.map((model) => (
                      <Badge key={model} variant="outline" className="text-xs">
                        {model}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <Separator className="my-3" />

            <Button
              variant="destructive"
              size="sm"
              onClick={handleClearDatabase}
              disabled={isClearing}
              className="w-full"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              {isClearing ? 'Clearing...' : 'Clear Database'}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
