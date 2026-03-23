'use client';

import { Suspense, useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import LandingPage from '@/components/LandingPage';
import WorkbenchView from '@/components/WorkbenchView';
import TopNav from '@/components/TopNav';
import { usePersona } from '@/lib/PersonaContext';
import { ApplicationListItem } from '@/lib/types';
import { PersonaId, PERSONAS } from '@/lib/personas';

type ViewType = 'landing' | 'workbench';

export default function Home() {
  return (
    <Suspense>
      <HomeContent />
    </Suspense>
  );
}

function HomeContent() {
  const [applications, setApplications] = useState<ApplicationListItem[]>([]);
  const [selectedAppId, setSelectedAppId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<ViewType>('landing');
  const { currentPersona, setPersona } = usePersona();
  const searchParams = useSearchParams();
  const [deepLinkHandled, setDeepLinkHandled] = useState(false);

  const fetchApplications = async (persona?: string) => {
    const p = persona || currentPersona;
    try {
      setLoading(true);
      console.log('Loading applications for persona:', p);
      const response = await fetch(`/api/applications?persona=${p}`, {
        cache: 'no-store',
        headers: { 'Cache-Control': 'no-cache' },
      });
      if (response.ok) {
        const apps = await response.json();
        setApplications(apps);
        return apps;
      } else {
        setApplications([]);
        return [];
      }
    } catch (err) {
      console.error('Failed to load applications:', err);
      setApplications([]);
      return [];
    } finally {
      setLoading(false);
    }
  };

  // Handle deep-link query params: ?app=xxx&persona=yyy
  useEffect(() => {
    if (deepLinkHandled) return;
    const appParam = searchParams.get('app');
    const personaParam = searchParams.get('persona');

    if (appParam) {
      setDeepLinkHandled(true);
      
      if (personaParam && personaParam in PERSONAS) {
        setPersona(personaParam as PersonaId);
        // Fetch apps for the target persona, then select the app
        fetchApplications(personaParam).then(() => {
          setSelectedAppId(appParam);
          setView('workbench');
        });
      } else {
        // No persona specified, use current
        fetchApplications().then(() => {
          setSelectedAppId(appParam);
          setView('workbench');
        });
      }

      // Clean the URL without triggering navigation
      if (typeof window !== 'undefined') {
        window.history.replaceState({}, '', '/');
      }
    } else {
      fetchApplications();
    }
  }, [searchParams]);

  useEffect(() => {
    if (deepLinkHandled) return;
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
