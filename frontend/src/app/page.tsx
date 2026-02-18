'use client';

import { useState, useEffect } from 'react';
import LandingPage from '@/components/LandingPage';
import WorkbenchView from '@/components/WorkbenchView';
import TopNav from '@/components/TopNav';
import { usePersona } from '@/lib/PersonaContext';
import { ApplicationListItem } from '@/lib/types';

type ViewType = 'landing' | 'workbench';

export default function Home() {
  const [applications, setApplications] = useState<ApplicationListItem[]>([]);
  const [selectedAppId, setSelectedAppId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<ViewType>('landing');
  const { currentPersona } = usePersona();

  const fetchApplications = async () => {
    try {
      setLoading(true);
      console.log('Loading applications for persona:', currentPersona);
      const response = await fetch(`/api/applications?persona=${currentPersona}`, {
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache',
        },
      });
      if (response.ok) {
        const apps = await response.json();
        setApplications(apps);
      } else {
        setApplications([]);
      }
    } catch (err) {
      console.error('Failed to load applications:', err);
      setApplications([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Reset view to landing when persona changes
    setView('landing');
    setSelectedAppId(null);
    fetchApplications();
  }, [currentPersona]);

  const handleSelectApp = (appId: string) => {
    setSelectedAppId(appId);
    setView('workbench');
  };

  const handleBackToLanding = () => {
    setView('landing');
    setSelectedAppId(null);
    fetchApplications();
  };

  if (view === 'workbench' && selectedAppId) {
    return (
      <WorkbenchView 
        applicationId={selectedAppId}
        applications={applications}
        onBack={handleBackToLanding}
        onSelectApp={handleSelectApp}
      />
    );
  }

  // Landing Page View
  return (
    <>
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <TopNav 
             applications={applications}
             selectedAppId={undefined}
             activeView="overview"
             onSelectApp={handleSelectApp}
             onChangeView={() => {}}
             showWorkbenchControls={false}
        />
      </header>
      <LandingPage 
        applications={applications}
        onSelectApp={handleSelectApp}
        onRefreshApps={fetchApplications}
        loading={loading}
      />
    </>
  );
}
