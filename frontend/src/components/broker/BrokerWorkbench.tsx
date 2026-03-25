'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Briefcase, BarChart3, FileText, Search, TrendingUp,
  AlertTriangle, RefreshCw,
} from 'lucide-react';
import BrokerDashboard from './BrokerDashboard';
import SubmissionBuilder from './SubmissionBuilder';
import QuoteComparisonTable from './QuoteComparisonTable';
import ClientResearchPanel from './ClientResearchPanel';
import { getSubmission } from '../../lib/broker-api';
import type { Submission } from '../../lib/broker-types';

type BrokerTab = 'dashboard' | 'submission' | 'quotes' | 'research';

interface BrokerWorkbenchProps {
  applicationId: string;
}

export default function BrokerWorkbench({ applicationId }: BrokerWorkbenchProps) {
  const [activeTab, setActiveTab] = useState<BrokerTab>('dashboard');
  const [selectedSubmissionId, setSelectedSubmissionId] = useState<string | null>(null);
  const [selectedClientId, setSelectedClientId] = useState<string | null>(null);
  const [submission, setSubmission] = useState<Submission | null>(null);

  // When a submission is selected, pre-fetch it and open the Submission tab
  const handleSelectSubmission = useCallback(async (submissionId: string) => {
    setSelectedSubmissionId(submissionId);
    setActiveTab('submission');
    try {
      const sub = await getSubmission(submissionId);
      setSubmission(sub);
      setSelectedClientId(sub.client_id);
    } catch {
      // SubmissionBuilder will handle its own loading/errors
    }
  }, []);

  const handleSelectClient = useCallback((clientId: string) => {
    setSelectedClientId(clientId);
    setActiveTab('research');
  }, []);

  const tabs: { id: BrokerTab; label: string; icon: typeof Briefcase; disabled?: boolean }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: TrendingUp },
    { id: 'submission', label: 'Submission', icon: FileText, disabled: !selectedSubmissionId },
    { id: 'quotes', label: 'Quotes', icon: BarChart3, disabled: !selectedSubmissionId },
    { id: 'research', label: 'Research', icon: Search },
  ];

  return (
    <div className="flex flex-col h-full bg-slate-50">
      {/* Header Bar */}
      <div className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
              <Briefcase className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-slate-900">
                Commercial Brokerage Workbench
              </h1>
              <p className="text-sm text-slate-500">
                Application {applicationId}
                {selectedSubmissionId && ` • Submission ${selectedSubmissionId}`}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation + Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Tab Bar */}
        <div className="bg-white border-b border-slate-200 px-4">
          <div className="flex gap-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => !tab.disabled && setActiveTab(tab.id)}
                disabled={tab.disabled}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-amber-600 text-amber-600'
                    : tab.disabled
                    ? 'border-transparent text-slate-300 cursor-not-allowed'
                    : 'border-transparent text-slate-600 hover:text-slate-900 hover:border-slate-300'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto">
          {activeTab === 'dashboard' && (
            <BrokerDashboard
              onSelectClient={handleSelectClient}
              onSelectSubmission={handleSelectSubmission}
            />
          )}
          {activeTab === 'submission' && selectedSubmissionId && (
            <SubmissionBuilder submissionId={selectedSubmissionId} />
          )}
          {activeTab === 'quotes' && selectedSubmissionId && (
            <QuoteComparisonTable submissionId={selectedSubmissionId} />
          )}
          {activeTab === 'research' && (
            <ClientResearchPanel clientId={selectedClientId ?? undefined} />
          )}
        </div>
      </div>
    </div>
  );
}
