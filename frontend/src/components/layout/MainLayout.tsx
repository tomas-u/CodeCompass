'use client';

import { useState, useRef, useEffect } from 'react';
import { Header } from './Header';
import { ChatPanel } from './ChatPanel';
import { useAppStore } from '@/lib/store';

interface MainLayoutProps {
  children: React.ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  const { isChatPanelOpen } = useAppStore();
  const [chatWidth, setChatWidth] = useState(480); // Default width for lg breakpoint
  const [isResizing, setIsResizing] = useState(false);
  const resizeRef = useRef<number>(chatWidth);

  // Handle resize start
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsResizing(true);
    e.preventDefault();
  };

  // Handle resizing
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;

      const newWidth = window.innerWidth - e.clientX;
      const minWidth = 300;
      const maxWidth = 800;

      if (newWidth >= minWidth && newWidth <= maxWidth) {
        setChatWidth(newWidth);
        resizeRef.current = newWidth;
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <div className="flex pt-14 h-screen overflow-hidden">
        {/* Main Content */}
        <main className="flex-1 overflow-auto transition-all duration-300 ease-in-out">
          {children}
        </main>

        {/* Chat Panel - always rendered for smooth transitions */}
        {isChatPanelOpen && (
          <>
            {/* Resize Handle */}
            <div
              className={`w-1 hover:w-2 bg-border hover:bg-primary transition-all cursor-col-resize ${
                isResizing ? 'bg-primary w-2' : ''
              }`}
              onMouseDown={handleMouseDown}
            />

            <div
              style={{ width: `${chatWidth}px` }}
              className="transition-all duration-300 ease-in-out overflow-hidden min-w-[300px] max-w-[800px]"
            >
              <ChatPanel />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
