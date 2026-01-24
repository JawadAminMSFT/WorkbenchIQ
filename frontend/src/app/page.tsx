'use client';

import { useState, useEffect } from 'react';
import { Sparkles, FileText } from 'lucide-react';
import TopNav from '@/components/TopNav';
import PatientHeader from '@/components/PatientHeader';
import PatientSummary from '@/components/PatientSummary';
import LabResultsPanel from '@/components/LabResultsPanel';
import SubstanceUsePanel from '@/components/SubstanceUsePanel';
import FamilyHistoryPanel from '@/components/FamilyHistoryPanel';
import AllergiesPanel from '@/components/AllergiesPanel';
import OccupationPanel from '@/components/OccupationPanel';
import ChronologicalOverview from '@/components/ChronologicalOverview';
import DocumentsPanel from '@/components/DocumentsPanel';
import SourcePagesPanel from '@/components/SourcePagesPanel';
import LoadingSpinner from '@/components/LoadingSpinner';
import PolicySummaryPanel from '@/components/PolicySummaryPanel';
import PolicyReportModal from '@/components/PolicyReportModal';
import ChatDrawer from '@/components/ChatDrawer';
import { ClaimsSummary, MedicalRecordsPanel, EligibilityPanel } from '@/components/claims';
import LifeHealthClaimsOverview from '@/components/claims/LifeHealthClaimsOverview';
import PropertyCasualtyClaimsOverview from '@/components/claims/PropertyCasualtyClaimsOverview';
import AutomotiveClaimsOverview from '@/components/claims/AutomotiveClaimsOverview';
import { usePersona } from '@/lib/PersonaContext';
import type { ApplicationMetadata, ApplicationListItem } from '@/lib/types';

type ViewType = 'overview' | 'timeline' | 'documents' | 'source';

export default function Home() {
  const [applications, setApplications] = useState<ApplicationListItem[]>([]);
  const [selectedApp, setSelectedApp] = useState<ApplicationMetadata | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<ViewType>('overview');
  const [isPolicyReportOpen, setIsPolicyReportOpen] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const { currentPersona, personaConfig } = usePersona();

  // Load applications list - reload when persona changes
  useEffect(() => {
    async function fetchApplications() {
      try {
        setLoading(true);
        setError(null);
        setSelectedApp(null); // Clear selection when switching personas
        setApplications([]); // Clear applications immediately to prevent stale data
        console.log('Loading applications for persona:', currentPersona);
        const response = await fetch(`/api/applications?persona=${currentPersona}`, {
          cache: 'no-store',
          headers: {
            'Cache-Control': 'no-cache',
          },
        });
        if (response.ok) {
          const apps = await response.json();
          console.log('Loaded applications:', apps.length, 'for persona:', currentPersona, apps.map((a: any) => ({ id: a.id, persona: a.persona })));
          setApplications(apps);
          // Select the first completed app if available
          if (apps.length > 0) {
            const completedApp = apps.find((a: ApplicationListItem) => a.status === 'completed') || apps[0];
            loadApplication(completedApp.id);
          } else {
            setLoading(false);
          }
        } else {
          setError('Failed to load applications');
          setApplications([]);
          setLoading(false);
        }
      } catch (err) {
        console.error('Failed to load applications:', err);
        setError('Failed to connect to API server');
        setApplications([]);
        setLoading(false);
      }
    }
    
    fetchApplications();
  }, [currentPersona]);

  async function loadApplications() {
    // This function is now just for manual refresh
    try {
      setLoading(true);
      setError(null);
      setSelectedApp(null);
      setApplications([]);
      console.log('Loading applications for persona:', currentPersona);
      const response = await fetch(`/api/applications?persona=${currentPersona}`, {
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache',
        },
      });
      if (response.ok) {
        const apps = await response.json();
        console.log('Loaded applications:', apps.length, 'for persona:', currentPersona, apps.map((a: any) => ({ id: a.id, persona: a.persona })));
        setApplications(apps);
        if (apps.length > 0) {
          const completedApp = apps.find((a: ApplicationListItem) => a.status === 'completed') || apps[0];
          loadApplication(completedApp.id);
        } else {
          setLoading(false);
        }
      } else {
        setError('Failed to load applications');
        setApplications([]);
        setLoading(false);
      }
    } catch (err) {
      console.error('Failed to load applications:', err);
      setError('Failed to connect to API server');
      setApplications([]);
      setLoading(false);
    }
  }

  async function loadApplication(appId: string) {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`/api/applications/${appId}`);
      if (response.ok) {
        const app = await response.json();
        setSelectedApp(app);
        // Reset to overview when selecting a new application
        setActiveView('overview');
      } else {
        setError('Failed to load application details');
        setSelectedApp(null);
      }
    } catch (err) {
      console.error('Failed to load application:', err);
      setError('Failed to load application details');
      setSelectedApp(null);
    } finally {
      setLoading(false);
    }
  }

  const renderMainContent = () => {
    if (!selectedApp) return null;

    switch (activeView) {
      case 'timeline':
        return (
          <div className="flex-1 overflow-auto p-6">
            <ChronologicalOverview application={selectedApp} fullWidth />
          </div>
        );
      case 'documents':
        return (
          <div className="flex-1 overflow-auto p-6">
            <DocumentsPanel files={selectedApp.files || []} />
          </div>
        );
      case 'source':
        return (
          <div className="flex-1 overflow-auto p-6 h-full">
            <SourcePagesPanel pages={selectedApp.markdown_pages || []} />
          </div>
        );
      case 'overview':
      default:
        // Render persona-specific overview
        if (currentPersona === 'automotive_claims') {
          return renderAutomotiveClaimsOverview();
        }
        if (currentPersona === 'life_health_claims') {
          return renderLifeHealthClaimsOverview();
        }
        if (currentPersona === 'property_casualty_claims') {
          return renderPropertyCasualtyClaimsOverview();
        }
        if (currentPersona === 'mortgage') {
          return renderMortgageOverview();
        }
        // Default: Underwriting overview
        return renderUnderwritingOverview();
    }
  };

  const renderUnderwritingOverview = () => {
    if (!selectedApp) return null;
    
    const handleRerunAnalysis = async () => {
      if (!selectedApp) return;
      try {
        // Re-run risk analysis (separate from extraction)
        const response = await fetch(`/api/applications/${selectedApp.id}/risk-analysis`, {
          method: 'POST',
        });
        if (response.ok) {
          // Reload application to get updated analysis
          loadApplication(selectedApp.id);
        }
      } catch (err) {
        console.error('Failed to re-run risk analysis:', err);
      }
    };
    
    return (
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Top Section: AI Analysis + Chronological Overview side by side */}
          <div className="flex gap-6 items-stretch">
            {/* Left Column - AI Analysis */}
            <div className="flex-1 flex flex-col gap-6">
              {/* Patient Summary */}
              <PatientSummary 
                application={selectedApp} 
                onPolicyClick={(policyId) => {
                  setIsPolicyReportOpen(true);
                }}
              />
              
              {/* Policy Summary Panel (risk analysis) */}
              <PolicySummaryPanel
                application={selectedApp}
                onViewFullReport={() => setIsPolicyReportOpen(true)}
                onRiskAnalysisComplete={() => loadApplication(selectedApp.id)}
              />
            </div>

            {/* Right Column - Chronological Overview (matches height of left column) */}
            <div className="w-80 flex-shrink-0 flex flex-col">
              <div className="flex-1 overflow-y-auto">
                <ChronologicalOverview application={selectedApp} />
              </div>
            </div>
          </div>

          {/* Section Divider */}
          <div className="flex items-center gap-4 py-2">
            <div className="flex-1 border-t border-slate-200" />
            <div className="flex items-center gap-2 text-xs font-medium text-slate-400 uppercase tracking-wider">
              <FileText className="w-4 h-4" />
              <span>Evidence from Documents</span>
            </div>
            <div className="flex-1 border-t border-slate-200" />
          </div>

          {/* Evidence Section - Full Width */}
          <div className="grid grid-cols-3 gap-6">
            <LabResultsPanel application={selectedApp} />
            <SubstanceUsePanel application={selectedApp} />
            <FamilyHistoryPanel application={selectedApp} />
          </div>

          <div className="grid grid-cols-2 gap-6">
            <AllergiesPanel application={selectedApp} />
            <OccupationPanel application={selectedApp} />
          </div>
        </div>
        
        {/* Policy Report Modal */}
        <PolicyReportModal
          isOpen={isPolicyReportOpen}
          onClose={() => setIsPolicyReportOpen(false)}
          application={selectedApp}
          onRerunAnalysis={handleRerunAnalysis}
        />
      </div>
    );
  };

  const renderLifeHealthClaimsOverview = () => {
    if (!selectedApp) {
      return (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center text-slate-500">
            <p className="text-lg font-medium">No claims application selected</p>
            <p className="text-sm mt-2">Select a claim from the dropdown to view details</p>
          </div>
        </div>
      );
    }
    return (
      <LifeHealthClaimsOverview application={selectedApp} />
    );
  };

  const renderPropertyCasualtyClaimsOverview = () => {
    if (!selectedApp) {
      return (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center text-slate-500">
            <p className="text-lg font-medium">No claims application selected</p>
            <p className="text-sm mt-2">Select a claim from the dropdown to view details</p>
          </div>
        </div>
      );
    }
    return (
      <PropertyCasualtyClaimsOverview application={selectedApp} />
    );
  };

  const renderAutomotiveClaimsOverview = () => {
    if (!selectedApp) {
      return (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center text-slate-500">
            <p className="text-lg font-medium">No automotive claim selected</p>
            <p className="text-sm mt-2">Select a claim from the dropdown to view details</p>
          </div>
        </div>
      );
    }
    return (
      <AutomotiveClaimsOverview 
        applicationId={selectedApp.id}
      />
    );
  };

  const renderMortgageOverview = () => {
    return (
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-3xl mx-auto">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8 text-center">
            <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-3xl">🏠</span>
            </div>
            <h2 className="text-2xl font-semibold text-slate-900 mb-2">
              Mortgage Workbench
            </h2>
            <p className="text-slate-600 mb-6">
              The Mortgage underwriting workbench is coming soon. This workspace will help you 
              process loan applications, property documents, and borrower verification.
            </p>
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-100 text-indigo-700 rounded-lg">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-indigo-500"></span>
              </span>
              Coming Soon
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Top Navigation */}
      <TopNav
        applications={applications}
        selectedAppId={selectedApp?.id}
        selectedApp={selectedApp || undefined}
        activeView={activeView}
        onSelectApp={loadApplication}
        onChangeView={setActiveView}
      />

      {/* Main Content */}
      <main className="flex flex-col" style={{ minHeight: 'calc(100vh - 120px)' }}>
        {loading ? (
          <div className="flex-1 flex items-center justify-center">
            <LoadingSpinner />
          </div>
        ) : error ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <p className="text-rose-500 mb-2">{error}</p>
              <p className="text-slate-500 text-sm">
                Make sure the API server is running on port 8000
              </p>
              <button
                onClick={() => loadApplications()}
                className="mt-4 px-4 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition-colors"
              >
                Retry
              </button>
            </div>
          </div>
        ) : selectedApp ? (
          <>
            {/* Patient Header - only for underwriting */}
            {currentPersona === 'underwriting' && <PatientHeader application={selectedApp} />}

            {/* Main Content Area based on active view */}
            {renderMainContent()}
          </>
        ) : currentPersona === 'mortgage' ? (
          // Mortgage "Coming Soon" view
          renderMortgageOverview()
        ) : applications.length === 0 ? (
          <div className="flex-1 flex items-center justify-center text-slate-500">
            <div className="text-center">
              <div 
                className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4"
                style={{ backgroundColor: `${personaConfig.color}15` }}
              >
                <personaConfig.icon className="w-8 h-8" style={{ color: personaConfig.color }} />
              </div>
              <p className="text-lg mb-2 text-slate-700">No {personaConfig.name.toLowerCase()} applications found</p>
              <p className="text-sm text-slate-500">Go to the Admin page to upload and process documents</p>
              <a
                href="/admin"
                className="mt-4 inline-block px-4 py-2 text-white rounded-lg transition-colors"
                style={{ backgroundColor: personaConfig.color }}
              >
                Go to Admin
              </a>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-500">
            <p>Select an application from the dropdown to view details</p>
          </div>
        )}
      </main>

      {/* Chat Drawer - Always mounted at root for smooth animations */}
      {selectedApp && (
        <ChatDrawer
          isOpen={isChatOpen}
          onClose={() => setIsChatOpen(false)}
          onOpen={() => setIsChatOpen(true)}
          applicationId={selectedApp.id}
          persona={currentPersona}
        />
      )}
    </div>
  );
}
