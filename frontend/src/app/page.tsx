'use client';

import { useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { WelcomePage } from '@/components/welcome/WelcomePage';
import { AnalysisProgress } from '@/components/analysis/AnalysisProgress';
import { Dashboard } from '@/components/dashboard/Dashboard';
import { useAppStore } from '@/lib/store';

export default function Home() {
  const { currentProjectId, analysisProgress, projects, fetchProjects } = useAppStore();

  // Fetch projects on mount
  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  // Determine which view to show
  const showWelcome = !currentProjectId && !analysisProgress;
  const showAnalysis = analysisProgress !== null;
  const showDashboard = currentProjectId && !analysisProgress;

  return (
    <MainLayout>
      {showWelcome && <WelcomePage />}
      {showAnalysis && <AnalysisProgress />}
      {showDashboard && <Dashboard />}
    </MainLayout>
  );
}
