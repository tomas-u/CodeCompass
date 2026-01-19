'use client';

import { useState, useEffect } from 'react';
import { FileText, Download, Copy, Check, Package, RefreshCw, Loader2, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AnalysisInProgress } from '@/components/ui/loading-skeleton';
import { useAppStore } from '@/lib/store';
import { api } from '@/lib/api';
import { Report, ReportType } from '@/types/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

type TabType = 'summary' | 'architecture' | 'dependencies';

interface ReportState {
  data: Report | null;
  loading: boolean;
  error: string | null;
  generating: boolean;
}

export function ReportsTab() {
  const { currentProjectId, projects } = useAppStore();
  const [activeTab, setActiveTab] = useState<TabType>('architecture');
  const [copied, setCopied] = useState(false);

  // Separate state for each report type
  const [reports, setReports] = useState<Record<TabType, ReportState>>({
    summary: { data: null, loading: false, error: null, generating: false },
    architecture: { data: null, loading: false, error: null, generating: false },
    dependencies: { data: null, loading: false, error: null, generating: false },
  });

  const currentProject = projects.find(p => p.id === currentProjectId);

  // Check if analysis is in progress
  const analysisStates = ['pending', 'cloning', 'scanning', 'analyzing'];
  const isAnalyzing = currentProject && analysisStates.includes(currentProject.status);

  // Fetch report when tab changes or project changes
  useEffect(() => {
    if (!currentProjectId || isAnalyzing) return;

    const fetchReport = async () => {
      const reportType = activeTab as ReportType;

      // Skip if already loaded or loading
      if (reports[activeTab].data || reports[activeTab].loading) return;

      setReports(prev => ({
        ...prev,
        [activeTab]: { ...prev[activeTab], loading: true, error: null }
      }));

      try {
        // Try to get the report (will auto-generate if doesn't exist)
        const report = await api.getReport(currentProjectId, reportType, true);
        setReports(prev => ({
          ...prev,
          [activeTab]: { data: report, loading: false, error: null, generating: false }
        }));
      } catch (err: any) {
        const errorMessage = err?.message || 'Failed to load report';
        setReports(prev => ({
          ...prev,
          [activeTab]: { ...prev[activeTab], loading: false, error: errorMessage, generating: false }
        }));
      }
    };

    fetchReport();
  }, [currentProjectId, activeTab, isAnalyzing]);

  // Reset reports when project changes
  useEffect(() => {
    setReports({
      summary: { data: null, loading: false, error: null, generating: false },
      architecture: { data: null, loading: false, error: null, generating: false },
      dependencies: { data: null, loading: false, error: null, generating: false },
    });
  }, [currentProjectId]);

  const handleRegenerate = async () => {
    if (!currentProjectId) return;

    const reportType = activeTab as ReportType;

    setReports(prev => ({
      ...prev,
      [activeTab]: { ...prev[activeTab], generating: true, error: null }
    }));

    try {
      await api.generateReport(currentProjectId, reportType, true);
      // Fetch the newly generated report
      const report = await api.getReport(currentProjectId, reportType, false);
      setReports(prev => ({
        ...prev,
        [activeTab]: { data: report, loading: false, error: null, generating: false }
      }));
    } catch (err: any) {
      const errorMessage = err?.message || 'Failed to regenerate report';
      setReports(prev => ({
        ...prev,
        [activeTab]: { ...prev[activeTab], generating: false, error: errorMessage }
      }));
    }
  };

  // Show loading state while analyzing
  if (isAnalyzing) {
    return (
      <div className="p-6">
        <AnalysisInProgress status={currentProject?.status || 'pending'} />
      </div>
    );
  }

  const handleCopy = async (content: string) => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const currentReportState = reports[activeTab];
  const currentReport = currentReportState.data;

  const renderReportContent = () => {
    if (currentReportState.loading) {
      return (
        <div className="flex flex-col items-center justify-center h-[400px] gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <p className="text-muted-foreground">Loading report...</p>
        </div>
      );
    }

    if (currentReportState.generating) {
      return (
        <div className="flex flex-col items-center justify-center h-[400px] gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Generating report with AI...</p>
          <p className="text-sm text-muted-foreground">This may take a moment</p>
        </div>
      );
    }

    if (currentReportState.error) {
      return (
        <div className="flex flex-col items-center justify-center h-[400px] gap-4">
          <AlertCircle className="h-8 w-8 text-destructive" />
          <p className="text-destructive font-medium">Failed to load report</p>
          <p className="text-sm text-muted-foreground">{currentReportState.error}</p>
          <Button variant="outline" onClick={handleRegenerate}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </Button>
        </div>
      );
    }

    if (!currentReport) {
      return (
        <div className="flex flex-col items-center justify-center h-[400px] gap-4">
          <FileText className="h-8 w-8 text-muted-foreground" />
          <p className="text-muted-foreground">No report available</p>
          <Button onClick={handleRegenerate}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Generate Report
          </Button>
        </div>
      );
    }

    return (
      <ScrollArea className="h-[600px]">
        <div className="prose prose-sm dark:prose-invert max-w-none px-1">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              // Style tables
              table: ({ children }) => (
                <table className="border-collapse border border-border my-4">{children}</table>
              ),
              th: ({ children }) => (
                <th className="border border-border px-4 py-2 bg-muted font-semibold text-left">{children}</th>
              ),
              td: ({ children }) => (
                <td className="border border-border px-4 py-2">{children}</td>
              ),
              // Style code blocks
              code: ({ className, children, ...props }) => {
                const isInline = !className;
                if (isInline) {
                  return (
                    <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                      {children}
                    </code>
                  );
                }
                return (
                  <code className={className} {...props}>
                    {children}
                  </code>
                );
              },
              pre: ({ children }) => (
                <pre className="bg-muted p-4 rounded-lg overflow-x-auto my-4">{children}</pre>
              ),
            }}
          >
            {currentReport.content.body}
          </ReactMarkdown>
        </div>
      </ScrollArea>
    );
  };

  const getReportTitle = (tab: TabType): string => {
    switch (tab) {
      case 'summary': return 'Project Summary';
      case 'architecture': return 'Architecture Report';
      case 'dependencies': return 'Dependencies Report';
    }
  };

  const getReportDescription = (tab: TabType): string => {
    switch (tab) {
      case 'summary': return 'Quick overview of the project structure and technologies';
      case 'architecture': return 'Comprehensive overview of the codebase structure and patterns';
      case 'dependencies': return 'Analysis of project dependencies and their relationships';
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Reports</h1>
        <p className="text-muted-foreground mt-1">
          AI-generated documentation and analysis reports
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabType)}>
        <TabsList>
          <TabsTrigger value="architecture">
            <FileText className="h-4 w-4 mr-2" />
            Architecture
          </TabsTrigger>
          <TabsTrigger value="summary">
            <FileText className="h-4 w-4 mr-2" />
            Summary
          </TabsTrigger>
          <TabsTrigger value="dependencies">
            <Package className="h-4 w-4 mr-2" />
            Dependencies
          </TabsTrigger>
        </TabsList>

        {(['architecture', 'summary', 'dependencies'] as TabType[]).map((tab) => (
          <TabsContent key={tab} value={tab} className="mt-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>{getReportTitle(tab)}</CardTitle>
                  <CardDescription>{getReportDescription(tab)}</CardDescription>
                  {reports[tab].data && (
                    <p className="text-xs text-muted-foreground mt-1">
                      Generated: {new Date(reports[tab].data!.generated_at).toLocaleString()}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {reports[tab].data && (
                    <>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleCopy(reports[tab].data!.content.body)}
                        disabled={currentReportState.generating}
                      >
                        {copied && activeTab === tab ? (
                          <Check className="h-4 w-4 mr-2" />
                        ) : (
                          <Copy className="h-4 w-4 mr-2" />
                        )}
                        Copy
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDownload(
                          reports[tab].data!.content.body,
                          `${tab}-report.md`
                        )}
                        disabled={currentReportState.generating}
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download
                      </Button>
                    </>
                  )}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleRegenerate}
                    disabled={currentReportState.loading || currentReportState.generating}
                  >
                    {currentReportState.generating ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <RefreshCw className="h-4 w-4 mr-2" />
                    )}
                    Regenerate
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {renderReportContent()}
              </CardContent>
            </Card>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
