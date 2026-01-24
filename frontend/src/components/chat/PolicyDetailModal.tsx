'use client';

import React, { useState, useEffect } from 'react';
import { X, FileText, AlertTriangle, Shield, ChevronRight, ExternalLink, Loader2 } from 'lucide-react';

interface PolicyCriteria {
  id: string;
  condition: string;
  risk_level: string;
  action: string;
  rationale: string;
}

interface PolicyDetail {
  id: string;
  category: string;
  subcategory: string;
  name: string;
  description: string;
  criteria: PolicyCriteria[];
  modifying_factors: Array<{ factor: string; impact: string }>;
  references: string[];
}

interface PolicyDetailModalProps {
  policyId: string;
  onClose: () => void;
  persona?: string;
}

const riskLevelColors: Record<string, { bg: string; text: string; border: string }> = {
  low: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200' },
  moderate: { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' },
  high: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
  standard: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200' },
  rated: { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' },
  decline: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
};

/**
 * PolicyDetailModal - Modal component for viewing policy details
 * Opens when clicking on a citation in Ask IQ chat
 */
const PolicyDetailModal: React.FC<PolicyDetailModalProps> = ({ policyId, onClose, persona = 'underwriting' }) => {
  const [policy, setPolicy] = useState<PolicyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchPolicy() {
      try {
        setLoading(true);
        setError(null);
        const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${backendUrl}/api/policies/${policyId}?persona=${persona}`);
        
        if (!response.ok) {
          throw new Error(`Policy not found: ${policyId}`);
        }
        
        const data = await response.json();
        setPolicy(data.policy || data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load policy');
      } finally {
        setLoading(false);
      }
    }

    fetchPolicy();
  }, [policyId, persona]);

  // Close on escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const getRiskColors = (level: string | undefined) => {
    if (!level) return riskLevelColors.moderate;
    const normalizedLevel = level.toLowerCase();
    return riskLevelColors[normalizedLevel] || riskLevelColors.moderate;
  };

  return (
    <div className="fixed inset-0 z-[60] bg-black/60 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[85vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-100 rounded-lg">
              <Shield className="w-5 h-5 text-indigo-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Policy Details</h2>
              <p className="text-sm text-slate-500 font-mono">{policyId}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
            </div>
          )}

          {error && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <AlertTriangle className="w-12 h-12 text-amber-500 mb-4" />
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Unable to Load Policy</h3>
              <p className="text-slate-600">{error}</p>
            </div>
          )}

          {policy && (
            <div className="space-y-6">
              {/* Policy Header */}
              <div>
                <h3 className="text-xl font-semibold text-slate-900 mb-2">{policy.name}</h3>
                <div className="flex flex-wrap gap-2 mb-3">
                  <span className="px-2.5 py-1 bg-indigo-100 text-indigo-700 text-xs font-medium rounded-full">
                    {policy.category}
                  </span>
                  {policy.subcategory && (
                    <span className="px-2.5 py-1 bg-slate-100 text-slate-700 text-xs font-medium rounded-full">
                      {policy.subcategory}
                    </span>
                  )}
                </div>
                <p className="text-slate-600">{policy.description}</p>
              </div>

              {/* Criteria */}
              {policy.criteria && policy.criteria.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
                    <FileText className="w-4 h-4" />
                    Evaluation Criteria ({policy.criteria.length})
                  </h4>
                  <div className="space-y-3">
                    {policy.criteria.map((criterion, idx) => {
                      const colors = getRiskColors(criterion.risk_level);
                      return (
                        <div
                          key={criterion.id || idx}
                          className={`rounded-lg border ${colors.border} ${colors.bg} p-4`}
                        >
                          <div className="flex items-start justify-between gap-4 mb-2">
                            <div className="flex-1">
                              <span className="text-xs font-mono text-slate-500">{criterion.id}</span>
                              <p className="text-sm font-medium text-slate-900 mt-1">{criterion.condition}</p>
                            </div>
                            <span className={`px-2 py-0.5 text-xs font-medium rounded ${colors.text} ${colors.bg} border ${colors.border}`}>
                              {criterion.risk_level}
                            </span>
                          </div>
                          <div className="text-sm text-slate-600 space-y-1">
                            <div className="flex gap-2">
                              <ChevronRight className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
                              <span><strong>Action:</strong> {criterion.action}</span>
                            </div>
                            <div className="flex gap-2">
                              <ChevronRight className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
                              <span><strong>Rationale:</strong> {criterion.rationale}</span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Modifying Factors */}
              {policy.modifying_factors && policy.modifying_factors.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-slate-900 mb-3">Modifying Factors</h4>
                  <div className="grid gap-2">
                    {policy.modifying_factors.map((factor, idx) => (
                      <div key={idx} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                        <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-2 flex-shrink-0" />
                        <div>
                          <span className="font-medium text-slate-900">{factor.factor}</span>
                          <span className="text-slate-500 ml-2">→ {factor.impact}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* References */}
              {policy.references && policy.references.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-slate-900 mb-3">References</h4>
                  <ul className="space-y-1">
                    {policy.references.map((ref, idx) => (
                      <li key={idx} className="flex items-center gap-2 text-sm text-slate-600">
                        <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
                        {ref}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-200 bg-slate-50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default PolicyDetailModal;
