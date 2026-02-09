'use client';

import { useState, useEffect } from 'react';
import { Sparkles, FileText, ChevronLeft } from 'lucide-react';
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
import BatchSummariesPanel from '@/components/BatchSummariesPanel';
import LoadingSpinner from '@/components/LoadingSpinner';
import PolicySummaryPanel from '@/components/PolicySummaryPanel';
import PolicyReportModal from '@/components/PolicyReportModal';
import ChatDrawer from '@/components/ChatDrawer';
import LifeHealthClaimsOverview from '@/components/claims/LifeHealthClaimsOverview';
import PropertyCasualtyClaimsOverview from '@/components/claims/PropertyCasualtyClaimsOverview';
import AutomotiveClaimsOverview from '@/components/claims/AutomotiveClaimsOverview';
import { MortgageWorkbench } from '@/components/mortgage';
import { usePersona } from '@/lib/PersonaContext';
import { getApplication } from '@/lib/api';
import type { ApplicationMetadata, ApplicationListItem } from '@/lib/types';

type ViewType = 'overview' | 'timeline' | 'documents' | 'source';

interface WorkbenchViewProps {
  applicationId: string;
  applications: ApplicationListItem[];
  onBack: () => void;
  onSelectApp: (appId: string) => void;
}

export default function WorkbenchView({ 
  applicationId, 
  applications, 
  onBack,
  onSelectApp 
}: WorkbenchViewProps) {
  const [selectedApp, setSelectedApp] = useState<ApplicationMetadata | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<ViewType>('overview');
  const [isPolicyReportOpen, setIsPolicyReportOpen] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [sourcePageNumber, setSourcePageNumber] = useState<number | undefined>(undefined);
  const { currentPersona, personaConfig } = usePersona();

  // Load application details
  useEffect(() => {
    async function loadApp() {
      if (!applicationId) return;
      
      try {
        setLoading(true);
        setError(null);
        console.log('Loading application:', applicationId);
        const app = await getApplication(applicationId);
        setSelectedApp(app);
        // Reset view when app changes
        setActiveView('overview');
      } catch (err) {
        console.error('Failed to load application:', err);
        setError('Failed to load application details');
      } finally {
        setLoading(false);
      }
    }
    
    loadApp();
  }, [applicationId]);

  // Poll for status updates if application is processing
  useEffect(() => {
    if (!selectedApp || selectedApp.status === 'completed' || selectedApp.status === 'error') return;
    
    const interval = setInterval(async () => {
      try {
        const updatedApp = await getApplication(selectedApp.id);
        if (updatedApp.status !== selectedApp.status || updatedApp.processing_status !== selectedApp.processing_status) {
            setSelectedApp(updatedApp);
        }
      } catch (err) {
        console.error('Polling failed:', err);
      }
    }, 2000);
    
    return () => clearInterval(interval);
  }, [selectedApp]);

  const renderContent = () => {
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
        // For underwriting persona with batch summaries, show enhanced view
        const hasBatchSummaries = selectedApp.batch_summaries && selectedApp.batch_summaries.length > 0;
        
        if (hasBatchSummaries) {
          return (
            <div className="flex-1 overflow-auto p-6 h-full">
              <div className="grid grid-cols-2 gap-6 h-full">
                <div className="h-full overflow-hidden">
                  <BatchSummariesPanel 
                    batchSummaries={selectedApp.batch_summaries!}
                    onPageClick={(pageNum) => {
                      setSourcePageNumber(pageNum);
                    }}
                  />
                </div>
                <div className="h-full overflow-hidden">
                  <SourcePagesPanel 
                    pages={selectedApp.markdown_pages || []} 
                    selectedPageNumber={sourcePageNumber}
                  />
                </div>
              </div>
            </div>
          );
        }
        return (
          <div className="flex-1 overflow-auto p-6 h-full">
            <SourcePagesPanel pages={selectedApp.markdown_pages || []} />
          </div>
        );
      case 'overview':
      default:
        if (currentPersona === 'automotive_claims') {
          return (
            <AutomotiveClaimsOverview 
                applicationId={selectedApp.id}
            />
          );
        }
        if (currentPersona === 'life_health_claims') {
          return <LifeHealthClaimsOverview application={selectedApp} />;
        }
        if (currentPersona === 'property_casualty_claims') {
          return <PropertyCasualtyClaimsOverview application={selectedApp} />;
        }
        if (currentPersona === 'mortgage') {
          return <MortgageWorkbench applicationId={selectedApp.id} />;
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
        const response = await fetch(`/api/applications/${selectedApp.id}/risk-analysis`, {
          method: 'POST',
        });
        if (response.ok) {
           // Reload to get new analysis
           const app = await getApplication(selectedApp.id);
           setSelectedApp(app);
        }
      } catch (err) {
        console.error('Failed to re-run risk analysis:', err);
      }
    };
    
    return (
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          <div className="relative">
            <div className="pr-[340px]">
              <div className="flex flex-col gap-6">
                <PatientSummary 
                  application={selectedApp} 
                  onPolicyClick={(policyId) => {
                    setIsPolicyReportOpen(true);
                  }}
                />
                <PolicySummaryPanel
                  application={selectedApp}
                  onViewFullReport={() => setIsPolicyReportOpen(true)}
                  onRiskAnalysisComplete={async () => {
                     const app = await getApplication(selectedApp.id);
                     setSelectedApp(app);
                  }}
                />
              </div>
            </div>
            <div className="absolute top-0 right-0 bottom-0 w-80">
              <ChronologicalOverview application={selectedApp} />
            </div>
          </div>

          <div className="flex items-center gap-4 py-2">
            <div className="flex-1 border-t border-slate-200" />
            <div className="flex items-center gap-2 text-xs font-medium text-slate-400 uppercase tracking-wider">
              <FileText className="w-4 h-4" />
              <span>Evidence from Documents</span>
            </div>
            <div className="flex-1 border-t border-slate-200" />
          </div>

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
        
        <PolicyReportModal
          isOpen={isPolicyReportOpen}
          onClose={() => setIsPolicyReportOpen(false)}
          application={selectedApp}
          onRerunAnalysis={handleRerunAnalysis}
        />
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex flex-col">
      {/* Navigation */}
      <div className="sticky top-0 z-50 bg-white">
        <TopNav 
          applications={applications}
          selectedAppId={selectedApp?.id}
          selectedApp={selectedApp || undefined}
          activeView={activeView}
          onSelectApp={onSelectApp}
          onChangeView={setActiveView}
          showWorkbenchControls={true}
        />
        
        {/* Back Button / Breadcrumb */}
        <div className="border-b border-slate-200 px-6 py-2 flex items-center bg-white/95 backdrop-blur-sm">
            <button 
                onClick={onBack}
                className="flex items-center text-sm text-slate-500 hover:text-indigo-600 transition-colors"
            >
                <ChevronLeft className="w-4 h-4 mr-1" />
                Back to Dashboard
            </button>
            <span className="mx-2 text-slate-300">/</span>
            <span className="text-sm font-medium text-slate-700 truncate max-w-md">
                {selectedApp?.external_reference || selectedApp?.id || 'Application Details'}
            </span>
             {loading && <span className="ml-3 text-xs text-slate-400 animate-pulse">Loading...</span>}
        </div>
      </div>

      <main className="flex flex-col flex-1 relative" style={{ minHeight: 'calc(100vh - 120px)' }}>
          {loading ? (
            <div className="flex-1 flex items-center justify-center">
                <LoadingSpinner />
            </div>
          ) : error ? (
            <div className="flex-1 flex items-center justify-center">
                 <div className="text-center text-rose-600 bg-white p-6 rounded-xl shadow-sm border border-rose-100">
                    <p>{error}</p>
                    <button onClick={onBack} className="mt-4 text-sm text-slate-500 hover:text-indigo-600 underline">Return to list</button>
                 </div>
            </div>
          ) : selectedApp ? (
            <>
               {currentPersona === 'underwriting' && <PatientHeader application={selectedApp} />}
               {renderContent()}
            </>
          ) : null}
      </main>

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
