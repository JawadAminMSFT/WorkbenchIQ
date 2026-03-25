'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart3, Star, AlertTriangle, CheckCircle, XCircle, Shield,
} from 'lucide-react';
import { compareQuotes } from '../../lib/broker-api';
import type { ComparisonResult, Quote } from '../../lib/broker-types';

interface QuoteComparisonTableProps {
  submissionId: string;
}

function formatCurrency(v: number): string {
  return `$${v.toLocaleString()}`;
}

type RowKey = keyof Pick<
  Quote,
  | 'annual_premium'
  | 'total_insured_value'
  | 'building_limit'
  | 'contents_limit'
  | 'bi_limit'
  | 'deductible'
  | 'flood_sublimit'
  | 'earthquake_sublimit'
>;

const COVERAGE_ROWS: { key: RowKey; label: string; best: 'low' | 'high' }[] = [
  { key: 'annual_premium', label: 'Annual Premium', best: 'low' },
  { key: 'total_insured_value', label: 'Total Insured Value', best: 'high' },
  { key: 'building_limit', label: 'Building Limit', best: 'high' },
  { key: 'contents_limit', label: 'Contents Limit', best: 'high' },
  { key: 'bi_limit', label: 'BI Limit', best: 'high' },
  { key: 'deductible', label: 'Deductible', best: 'low' },
  { key: 'flood_sublimit', label: 'Flood Sublimit', best: 'high' },
  { key: 'earthquake_sublimit', label: 'Earthquake Sublimit', best: 'high' },
];

function bestValue(quotes: Quote[], key: RowKey, best: 'low' | 'high'): number {
  const vals = quotes.map((q) => q[key]);
  return best === 'low' ? Math.min(...vals) : Math.max(...vals);
}

function cellColor(value: number, bestVal: number, best: 'low' | 'high'): string {
  if (value === bestVal) return 'text-green-700 bg-green-50';
  // Warn if more than 20 % worse
  const pct = best === 'low' ? (value - bestVal) / bestVal : (bestVal - value) / bestVal;
  if (pct > 0.2) return 'text-red-700 bg-red-50';
  return 'text-amber-700 bg-amber-50';
}

export default function QuoteComparisonTable({ submissionId }: QuoteComparisonTableProps) {
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchComparison = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await compareQuotes(submissionId);
      setResult(data);
    } catch (err) {
      console.error('Failed to compare quotes:', err);
      setError(err instanceof Error ? err.message : 'Failed to compare quotes');
    } finally {
      setLoading(false);
    }
  }, [submissionId]);

  useEffect(() => {
    fetchComparison();
  }, [fetchComparison]);

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
          onClick={fetchComparison}
          className="mt-4 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!result || result.carriers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-slate-400">
        <BarChart3 className="w-12 h-12 mb-4" />
        <p className="text-lg">No quotes to compare yet.</p>
        <p className="text-sm mt-1">Upload carrier quotes in the Submission tab first.</p>
      </div>
    );
  }

  const quotes = result.carriers.map((c) => c.quote);
  const rec = result.recommendation;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* AI Recommendation */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-5">
        <div className="flex items-start gap-3">
          <Star className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
          <div>
            <h3 className="text-sm font-semibold text-amber-800">
              AI Recommendation: {rec.carrier_name}
            </h3>
            <p className="text-sm text-amber-700 mt-1">{rec.rationale}</p>
            <p className="text-xs text-amber-500 mt-2">
              Confidence {Math.round(rec.confidence * 100)}%
            </p>
          </div>
        </div>
      </div>

      {/* Placement Scores */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {result.carriers.map((c) => {
          const isRecommended = c.carrier_name === rec.carrier_name;
          return (
            <div
              key={c.carrier_name}
              className={`rounded-lg border p-4 ${
                isRecommended
                  ? 'border-amber-400 bg-amber-50'
                  : 'border-slate-200 bg-white'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-semibold text-slate-900">{c.carrier_name}</p>
                {isRecommended && <Star className="w-4 h-4 text-amber-500" />}
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900">{c.placement.score}</span>
                <span className="text-xs text-slate-500">/ 100 — Rank #{c.placement.rank}</span>
              </div>
              <div className="mt-3 space-y-1">
                {c.placement.factors.map((f, i) => (
                  <div key={i} className="flex items-center gap-1.5 text-xs">
                    {f.impact === 'positive' && <CheckCircle className="w-3 h-3 text-green-500" />}
                    {f.impact === 'negative' && <XCircle className="w-3 h-3 text-red-500" />}
                    {f.impact === 'neutral' && <Shield className="w-3 h-3 text-slate-400" />}
                    <span className="text-slate-600">{f.detail}</span>
                  </div>
                ))}
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
              {result.carriers.map((c) => (
                <th
                  key={c.carrier_name}
                  className={`text-right px-4 py-3 text-xs font-semibold uppercase tracking-wider ${
                    c.carrier_name === rec.carrier_name ? 'text-amber-700' : 'text-slate-500'
                  }`}
                >
                  {c.carrier_name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {COVERAGE_ROWS.map((row) => {
              const bv = bestValue(quotes, row.key, row.best);
              return (
                <tr key={row.key}>
                  <td className="px-4 py-3 font-medium text-slate-700">{row.label}</td>
                  {quotes.map((q) => {
                    const val = q[row.key];
                    return (
                      <td
                        key={q.carrier_name}
                        className={`px-4 py-3 text-right font-mono ${cellColor(val, bv, row.best)}`}
                      >
                        {formatCurrency(val)}
                      </td>
                    );
                  })}
                </tr>
              );
            })}

            {/* AM Best Rating */}
            <tr>
              <td className="px-4 py-3 font-medium text-slate-700">AM Best Rating</td>
              {quotes.map((q) => (
                <td key={q.carrier_name} className="px-4 py-3 text-right text-slate-700">
                  {q.carrier_am_best}
                </td>
              ))}
            </tr>

            {/* Policy Period */}
            <tr>
              <td className="px-4 py-3 font-medium text-slate-700">Policy Period</td>
              {quotes.map((q) => (
                <td key={q.carrier_name} className="px-4 py-3 text-right text-slate-700">
                  {q.policy_period}
                </td>
              ))}
            </tr>

            {/* Exclusions */}
            <tr>
              <td className="px-4 py-3 font-medium text-slate-700 align-top">Exclusions</td>
              {quotes.map((q) => (
                <td key={q.carrier_name} className="px-4 py-3 text-right text-slate-700 align-top">
                  {q.exclusions.length === 0 ? (
                    <span className="text-green-600 text-xs">None</span>
                  ) : (
                    <ul className="space-y-0.5">
                      {q.exclusions.map((ex, i) => (
                        <li key={i} className="text-xs text-red-600">{ex}</li>
                      ))}
                    </ul>
                  )}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
