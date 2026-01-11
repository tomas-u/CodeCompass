'use client';

import { Header } from './Header';
import { ChatPanel } from './ChatPanel';
import { useAppStore } from '@/lib/store';

interface MainLayoutProps {
  children: React.ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  const { isChatPanelOpen } = useAppStore();

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <div className="flex pt-14 h-screen">
        {/* Main Content */}
        <main className={`flex-1 overflow-auto ${isChatPanelOpen ? 'mr-0' : ''}`}>
          {children}
        </main>

        {/* Chat Panel */}
        <ChatPanel />
      </div>
    </div>
  );
}
