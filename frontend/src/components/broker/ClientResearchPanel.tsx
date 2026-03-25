'use client';

import React, { useState, useCallback } from 'react';
import {
  Search, FileText, AlertTriangle, ExternalLink, Shield,
  Loader2,
} from 'lucide-react';
import { runClientResearch } from '../../lib/broker-api';
import type { ResearchBrief, ResearchSection } from '../../lib/broker-types';

interface ClientResearchPanelProps {
  clientId?: string;
}

function confidenceBar(confidence: number) {
  const pct = Math.round(confidence * 100);
  const color =
    pct >= 80 ? 'bg-green-500' : pct >= 60 ? 'bg-amber-500' : 'bg-red-500';
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-1.5 bg-slate-200 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-500">{pct}%</span>
    </div>
  );
}

export default function ClientResearchPanel({ clientId }: ClientResearchPanelProps) {
  const [brief, setBrief] = useState<ResearchBrief | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeClientId, setActiveClientId] = useState(clientId ?? '');

  const runResearch = useCallback(async () => {
    const id = activeClientId.trim();
    if (!id) return;
    setLoading(true);
    setError(null);
    setBrief(null);
    try {
      const data = await runClientResearch(id);
      setBrief(data);
    } catch (err) {
      console.error('Research failed:', err);
      setError(err instanceof Error ? err.message : 'Research request failed');
    } finally {
      setLoading(false);
    }
  }, [activeClientId]);

  // Auto-run if clientId is provided and changed
  React.useEffect(() => {
    if (clientId) {
      setActiveClientId(clientId);
    }
  }, [clientId]);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
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

      {/* Research Results */}
      {brief && !loading && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">{brief.company_name}</h2>
            <span className="text-xs text-slate-400">
              Generated {new Date(brief.generated_at).toLocaleString()}
            </span>
          </div>

          {brief.sections.map((section, idx) => (
            <ResearchSectionCard key={idx} section={section} />
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-component: Research Section Card
// ---------------------------------------------------------------------------

function ResearchSectionCard({ section }: { section: ResearchSection }) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-5 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-900">{section.title}</h3>
        {confidenceBar(section.confidence)}
      </div>
      <p className="text-sm text-slate-700 whitespace-pre-line leading-relaxed">
        {section.content}
      </p>
      {section.citations.length > 0 && (
        <div className="pt-2 border-t border-slate-100 space-y-1">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Sources</p>
          {section.citations.map((cite, i) => (
            <a
              key={i}
              href={cite.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-xs text-amber-600 hover:text-amber-700"
            >
              <ExternalLink className="w-3 h-3" />
              {cite.text}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
