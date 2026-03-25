'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart3, Star, AlertTriangle, CheckCircle, Shield,
} from 'lucide-react';
import { getSubmission } from '../../lib/broker-api';
import type { Submission, Quote } from '../../lib/broker-types';

interface QuoteComparisonTableProps {
  submissionId: string;
}

type FieldKey =
  | 'annual_premium'
  | 'total_insured_value'
  | 'building_limit'
  | 'contents_limit'
  | 'business_interruption_limit'
  | 'deductible'
  | 'flood_sublimit'
  | 'earthquake_sublimit';

const COVERAGE_ROWS: { key: FieldKey; label: string }[] = [
  { key: 'annual_premium', label: 'Annual Premium' },
  { key: 'total_insured_value', label: 'Total Insured Value' },
  { key: 'building_limit', label: 'Building Limit' },
  { key: 'contents_limit', label: 'Contents Limit' },
  { key: 'business_interruption_limit', label: 'BI Limit' },
  { key: 'deductible', label: 'Deductible' },
  { key: 'flood_sublimit', label: 'Flood Sublimit' },
  { key: 'earthquake_sublimit', label: 'Earthquake Sublimit' },
];

export default function QuoteComparisonTable({ submissionId }: QuoteComparisonTableProps) {
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getSubmission(submissionId);
      setSubmission(data);
    } catch (err) {
      console.error('Failed to load quotes:', err);
      setError(err instanceof Error ? err.message : 'Failed to load quotes');
    } finally {
      setLoading(false);
    }
  }, [submissionId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-red-600">
        <AlertTriangle className="w-12 h-12 mb-4" />
        <p className="text-lg font-medium">{error}</p>
        <button
          onClick={fetchData}
          className="mt-4 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700"
        >
          Retry
        </button>
      </div>
    );
  }

  const quotes = submission?.quotes ?? [];

  if (quotes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-slate-400">
        <BarChart3 className="w-12 h-12 mb-4" />
        <p className="text-lg">No quotes to compare yet.</p>
        <p className="text-sm mt-1">Upload carrier quotes in the Submission tab first.</p>
      </div>
    );
  }

  // Find the recommended quote (rank 1 or highest score)
  const sortedQuotes = [...quotes].sort(
    (a, b) => (a.scoring?.placement_rank ?? 999) - (b.scoring?.placement_rank ?? 999)
  );
  const recommended = sortedQuotes[0];
  const rationale = recommended?.scoring?.recommendation_rationale;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* AI Recommendation */}
      {rationale && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-5">
          <div className="flex items-start gap-3">
            <Star className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
            <div>
              <h3 className="text-sm font-semibold text-amber-800">
                AI Recommendation: {recommended.carrier_name}
              </h3>
              <p className="text-sm text-amber-700 mt-1">{rationale}</p>
            </div>
          </div>
        </div>
      )}

      {/* Placement Scores */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {sortedQuotes.map((q) => {
          const isRecommended = q.id === recommended?.id;
          const scoring = q.scoring;
          return (
            <div
              key={q.id}
              className={`rounded-lg border p-4 ${
                isRecommended
                  ? 'border-amber-400 bg-amber-50'
                  : 'border-slate-200 bg-white'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-semibold text-slate-900">{q.carrier_name}</p>
                {isRecommended && <Star className="w-4 h-4 text-amber-500" />}
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900">
                  {scoring?.placement_score?.toFixed(1) ?? '—'}
                </span>
                <span className="text-xs text-slate-500">
                  / 100 — Rank #{scoring?.placement_rank ?? '—'}
                </span>
              </div>
              <div className="mt-3 space-y-1">
                {scoring?.coverage_adequacy && (
                  <div className="flex items-center gap-1.5 text-xs">
                    <CheckCircle className="w-3 h-3 text-green-500" />
                    <span className="text-slate-600">
                      Coverage: {scoring.coverage_adequacy}
                    </span>
                  </div>
                )}
                {scoring?.premium_percentile && (
                  <div className="flex items-center gap-1.5 text-xs">
                    <Shield className="w-3 h-3 text-slate-400" />
                    <span className="text-slate-600">
                      Premium: {scoring.premium_percentile}
                    </span>
                  </div>
                )}
                {(scoring?.coverage_gaps?.length ?? 0) > 0 && (
                  <div className="flex items-center gap-1.5 text-xs">
                    <AlertTriangle className="w-3 h-3 text-red-500" />
                    <span className="text-slate-600">
                      Gaps: {scoring?.coverage_gaps?.join(', ')}
                    </span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Coverage Comparison Table */}
      <div className="bg-white rounded-lg border border-slate-200 overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50">
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Coverage
              </th>
              {sortedQuotes.map((q) => (
                <th
                  key={q.id}
                  className={`text-right px-4 py-3 text-xs font-semibold uppercase tracking-wider ${
                    q.id === recommended?.id ? 'text-amber-700' : 'text-slate-500'
                  }`}
                >
                  {q.carrier_name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {COVERAGE_ROWS.map((row) => (
              <tr key={row.key}>
                <td className="px-4 py-3 font-medium text-slate-700">{row.label}</td>
                {sortedQuotes.map((q) => (
                  <td
                    key={q.id}
                    className="px-4 py-3 text-right font-mono text-slate-900"
                  >
                    {(q.fields?.[row.key] as string) ?? '—'}
                  </td>
                ))}
              </tr>
            ))}

            {/* AM Best Rating */}
            <tr>
              <td className="px-4 py-3 font-medium text-slate-700">AM Best Rating</td>
              {sortedQuotes.map((q) => (
                <td key={q.id} className="px-4 py-3 text-right text-slate-700">
                  {q.fields?.carrier_am_best_rating ?? '—'}
                </td>
              ))}
            </tr>

            {/* Policy Period */}
            <tr>
              <td className="px-4 py-3 font-medium text-slate-700">Policy Period</td>
              {sortedQuotes.map((q) => (
                <td key={q.id} className="px-4 py-3 text-right text-slate-700">
                  {q.fields?.policy_period ?? '—'}
                </td>
              ))}
            </tr>

            {/* Exclusions */}
            <tr>
              <td className="px-4 py-3 font-medium text-slate-700 align-top">Exclusions</td>
              {sortedQuotes.map((q) => {
                const exclusions = q.fields?.named_perils_exclusions;
                return (
                  <td key={q.id} className="px-4 py-3 text-right text-slate-700 align-top">
                    {(!exclusions || exclusions.length === 0) ? (
                      <span className="text-green-600 text-xs">None</span>
                    ) : (
                      <ul className="space-y-0.5">
                        {exclusions.map((ex, i) => (
                          <li key={i} className="text-xs text-red-600">{ex}</li>
                        ))}
                      </ul>
                    )}
                  </td>
                );
              })}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
