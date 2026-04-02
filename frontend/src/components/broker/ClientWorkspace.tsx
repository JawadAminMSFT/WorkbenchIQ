'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  ArrowLeft, Building2, Search, FileText, BarChart3, Loader2,
  AlertTriangle, MapPin, Users, DollarSign, Calendar, User,
} from 'lucide-react';
import { getClient } from '../../lib/broker-api';
import type { Client } from '../../lib/broker-types';
import ProfileTab from './ProfileTab';
import ResearchTab from './ResearchTab';
import SubmissionsTab from './SubmissionsTab';
import QuotesTab from './QuotesTab';

type ClientTab = 'profile' | 'research' | 'submissions' | 'quotes';

interface RenewalDraft {
  line_of_business: string;
  effective_date: string;
  expiration_date: string;
}

interface ClientWorkspaceProps {
  clientId: string;
  onBack: () => void;
}

const TABS: { id: ClientTab; label: string; icon: typeof Search }[] = [
  { id: 'profile', label: 'Profile', icon: User },
  { id: 'research', label: 'Research', icon: Search },
  { id: 'submissions', label: 'Submissions', icon: FileText },
  { id: 'quotes', label: 'Quote Comparison', icon: BarChart3 },
];

export default function ClientWorkspace({ clientId, onBack }: ClientWorkspaceProps) {
  const [client, setClient] = useState<Client | null>(null);
  const [activeTab, setActiveTab] = useState<ClientTab>('profile');
  const [selectedSubmissionId, setSelectedSubmissionId] = useState<string | null>(null);
  const [renewalDraft, setRenewalDraft] = useState<RenewalDraft | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchClient = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getClient(clientId);
      setClient(data);
    } catch (err) {
      console.error('Failed to fetch client:', err);
      setError(err instanceof Error ? err.message : 'Failed to load client');
    } finally {
      setLoading(false);
    }
  }, [clientId]);

  useEffect(() => {
    fetchClient();
  }, [fetchClient]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-12 h-12 animate-spin text-amber-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-red-600">
        <AlertTriangle className="w-12 h-12 mb-4" />
        <p className="text-lg font-medium">{error}</p>
        <button
          onClick={fetchClient}
          className="mt-4 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Client Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Dashboard
            </button>
            <div className="h-6 w-px bg-slate-200" />
            <div className="w-9 h-9 rounded-lg bg-amber-100 flex items-center justify-center">
              <Building2 className="w-4 h-4 text-amber-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-900">
                {client?.name ?? 'Loading...'}
              </h2>
              <p className="text-sm text-slate-500">
                {client?.industry_code} • {client?.business_type}
              </p>
            </div>
          </div>
        </div>
        {/* AC-1.4: Rich client profile summary */}
        {client && (
          <div className="mt-3 ml-[4.25rem] grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-2">
            {client.headquarters_address && (
              <div className="flex items-center gap-1.5 text-sm text-slate-600">
                <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <span className="truncate">{client.headquarters_address}</span>
              </div>
            )}
            {client.annual_revenue && (
              <div className="flex items-center gap-1.5 text-sm text-slate-600">
                <DollarSign className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <span>Revenue: {client.annual_revenue}</span>
              </div>
            )}
            {client.employee_count != null && (
              <div className="flex items-center gap-1.5 text-sm text-slate-600">
                <Users className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <span>{client.employee_count.toLocaleString()} employees</span>
              </div>
            )}
            {client.renewal_date && (
              <div className="flex items-center gap-1.5 text-sm text-slate-600">
                <Calendar className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <span>Renews {new Date(client.renewal_date).toLocaleDateString()}</span>
              </div>
            )}
            {client.years_in_business != null && (
              <div className="flex items-center gap-1.5 text-sm text-slate-600">
                <Building2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <span>{client.years_in_business} years in business</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Tab Bar */}
      <div className="bg-white border-b border-slate-200 px-4">
        <div className="flex gap-1">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-amber-600 text-amber-600'
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
        {activeTab === 'profile' && (
          <ProfileTab
            clientId={clientId}
            client={client}
            onStartRenewal={(lob, effDate, expDate) => {
              setRenewalDraft({ line_of_business: lob, effective_date: effDate, expiration_date: expDate });
              setActiveTab('submissions');
            }}
          />
        )}
        {activeTab === 'research' && (
          <ResearchTab clientId={clientId} client={client} />
        )}
        {activeTab === 'submissions' && (
          <SubmissionsTab
            clientId={clientId}
            clientName={client?.name}
            onViewSubmission={(subId) => setSelectedSubmissionId(subId)}
            selectedSubmissionId={selectedSubmissionId}
            renewalDraft={renewalDraft}
            onRenewalDraftConsumed={() => setRenewalDraft(null)}
          />
        )}
        {activeTab === 'quotes' && (
          <QuotesTab
            clientId={clientId}
            clientName={client?.name}
            preselectedSubmissionId={selectedSubmissionId}
          />
        )}
      </div>
    </div>
  );
}
