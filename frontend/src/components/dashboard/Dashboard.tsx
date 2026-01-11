'use client';

import { LayoutDashboard, GitFork, FolderTree, FileText, MessageSquare } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { useAppStore } from '@/lib/store';
import { OverviewTab } from './tabs/OverviewTab';
import { DiagramsTab } from './tabs/DiagramsTab';
import { FilesTab } from './tabs/FilesTab';
import { ReportsTab } from './tabs/ReportsTab';

export function Dashboard() {
  const { activeTab, setActiveTab, isChatPanelOpen, toggleChatPanel } = useAppStore();

  return (
    <div className="h-full flex flex-col">
      {/* Tab Navigation */}
      <div className="border-b border-border bg-muted/30 px-4">
        <div className="flex items-center justify-between">
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)} className="w-full">
            <TabsList className="h-12 bg-transparent border-0 gap-1">
              <TabsTrigger
                value="overview"
                className="data-[state=active]:bg-background data-[state=active]:shadow-sm"
              >
                <LayoutDashboard className="h-4 w-4 mr-2" />
                Overview
              </TabsTrigger>
              <TabsTrigger
                value="diagrams"
                className="data-[state=active]:bg-background data-[state=active]:shadow-sm"
              >
                <GitFork className="h-4 w-4 mr-2" />
                Diagrams
              </TabsTrigger>
              <TabsTrigger
                value="files"
                className="data-[state=active]:bg-background data-[state=active]:shadow-sm"
              >
                <FolderTree className="h-4 w-4 mr-2" />
                Files
              </TabsTrigger>
              <TabsTrigger
                value="reports"
                className="data-[state=active]:bg-background data-[state=active]:shadow-sm"
              >
                <FileText className="h-4 w-4 mr-2" />
                Reports
              </TabsTrigger>
            </TabsList>
          </Tabs>

          {/* Chat Toggle (only shows when panel is closed) */}
          {!isChatPanelOpen && (
            <Button variant="outline" size="sm" onClick={toggleChatPanel} className="ml-4">
              <MessageSquare className="h-4 w-4 mr-2" />
              Open Chat
            </Button>
          )}
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-auto">
        {activeTab === 'overview' && <OverviewTab />}
        {activeTab === 'diagrams' && <DiagramsTab />}
        {activeTab === 'files' && <FilesTab />}
        {activeTab === 'reports' && <ReportsTab />}
      </div>
    </div>
  );
}
