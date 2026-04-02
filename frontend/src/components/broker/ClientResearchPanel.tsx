'use client';

import React, { useState, useCallback, useEffect } from 'react';
import {
  Search, FileText, AlertTriangle, ExternalLink,
  Loader2, Building2, Plus,
} from 'lucide-react';
import { runClientResearch, getClientSubmissions, getClient } from '../../lib/broker-api';
import type { ResearchBrief, Client, Submission } from '../../lib/broker-types';

interface ClientResearchPanelProps {
  clientId?: string;
  onSelectSubmission?: (submissionId: string) => void;
}

export default function ClientResearchPanel({ clientId, onSelectSubmission }: ClientResearchPanelProps) {
  const [brief, setBrief] = useState<ResearchBrief | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeClientId, setActiveClientId] = useState(clientId ?? '');
  const [client, setClient] = useState<Client | null>(null);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [submissionsLoading, setSubmissionsLoading] = useState(false);

  const loadClientData = useCallback(async (id: string) => {
    setSubmissionsLoading(true);
    try {
      const [clientData, submissionsData] = await Promise.all([
        getClient(id),
        getClientSubmissions(id),
      ]);
      setClient(clientData);
      setSubmissions(submissionsData);
    } catch (err) {
      console.error('Failed to load client data:', err);
    } finally {
      setSubmissionsLoading(false);
    }
  }, []);

  const runResearch = useCallback(async () => {
    const id = activeClientId.trim();
    if (!id) return;
    setLoading(true);
    setError(null);
    setBrief(null);
    try {
      const companyName = client?.name ?? id;
      const data = await runClientResearch(id, companyName);
      setBrief(data);
    } catch (err) {
      console.error('Research failed:', err);
      setError(err instanceof Error ? err.message : 'Research request failed');
    } finally {
      setLoading(false);
    }
  }, [activeClientId, client]);

  useEffect(() => {
    if (clientId) {
      setActiveClientId(clientId);
      loadClientData(clientId);
    }
  }, [clientId, loadClientData]);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Client Info & Submissions */}
      {client && (
        <div className="bg-white rounded-lg border border-slate-200 p-5">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                <Building2 className="w-5 h-5 text-slate-500" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-900">{client.name}</h2>
                <p className="text-sm text-slate-500">
                  {client.industry_code} • {client.business_type}
                </p>
              </div>
            </div>
          </div>
          
          <div className="border-t border-slate-100 pt-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-slate-900">Submissions</h3>
              <button className="flex items-center gap-1.5 px-2 py-1 text-xs font-medium text-amber-600 hover:text-amber-700">
                <Plus className="w-3 h-3" />
                New Submission
              </button>
            </div>
            
            {submissionsLoading ? (
              <div className="py-8 text-center">
                <Loader2 className="w-6 h-6 animate-spin text-amber-600 mx-auto" />
              </div>
            ) : submissions.length === 0 ? (
              <p className="text-sm text-slate-400 py-4 text-center">No submissions yet</p>
            ) : (
              <div className="space-y-2">
                {submissions.map((sub) => (
                  <button
                    key={sub.id}
                    onClick={() => onSelectSubmission?.(sub.id)}
                    className="w-full text-left px-3 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-slate-900">
                          {sub.line_of_business || 'Property'}
                        </p>
                        <p className="text-xs text-slate-500">
                          Status: {sub.status} • {sub.quotes?.length || 0} quotes
                        </p>
                      </div>
                      <span className="text-xs text-slate-400">
                        {new Date(sub.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Search / Trigger */}
      <div className="bg-white rounded-lg border border-slate-200 p-5">
        <h3 className="text-sm font-semibold text-slate-900 mb-3">Client Research</h3>
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Enter client ID"
              value={activeClientId}
              onChange={(e) => setActiveClientId(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
          </div>
          <button
            onClick={runResearch}
            disabled={loading || !activeClientId.trim()}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 disabled:opacity-50 rounded-lg transition-colors"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            Run Research
          </button>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-20 text-amber-600">
          <Loader2 className="w-10 h-10 animate-spin mb-4" />
          <p className="text-sm font-medium">Generating research brief…</p>
          <p className="text-xs text-slate-400 mt-1">This may take a minute.</p>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="flex flex-col items-center justify-center py-16 text-red-600">
          <AlertTriangle className="w-12 h-12 mb-4" />
          <p className="text-lg font-medium">{error}</p>
          <button
            onClick={runResearch}
            className="mt-4 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700"
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty – no research run yet */}
      {!brief && !loading && !error && (
        <div className="flex flex-col items-center justify-center py-20 text-slate-400">
          <FileText className="w-12 h-12 mb-4" />
          <p className="text-lg">No research brief yet</p>
          <p className="text-sm mt-1">Enter a client ID and click Run Research to generate an AI brief.</p>
        </div>
      )}

      {/* Research Results — render brief summary */}
      {brief && !loading && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-slate-900">{brief.company_name}</h2>

          <div className="bg-white rounded-lg border border-slate-200 p-5">
            <div className="prose prose-sm prose-slate max-w-none whitespace-pre-line leading-relaxed text-sm text-slate-700">
              {brief.brief || brief.business_description || 'Research complete. View the Research tab for full details.'}
            </div>
          </div>

          {((brief.sources?.length ?? 0) > 0 || (brief.data_sources?.length ?? 0) > 0) && (
            <div className="bg-white rounded-lg border border-slate-200 p-5 space-y-2">
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Sources</p>
              {(brief.sources ?? brief.data_sources ?? []).map((src, i) => (
                <div key={i} className="flex items-center gap-1.5 text-xs text-amber-600">
                  <ExternalLink className="w-3 h-3" />
                  <span>{src}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
