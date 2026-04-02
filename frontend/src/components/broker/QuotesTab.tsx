'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  BarChart3, Upload, Loader2, AlertTriangle, Star,
  CheckCircle, Shield, FileText, Mail, Copy, X, Info,
  Download, ChevronDown, ChevronUp, Layers, SlidersHorizontal,
} from 'lucide-react';
import {
  getClientSubmissions, getSubmission, uploadQuote, runQuoteComparison,
} from '../../lib/broker-api';
import type { CompareWeights } from '../../lib/broker-api';
import type { Submission, Quote } from '../../lib/broker-types';

interface QuotesTabProps {
  clientId: string;
  clientName?: string;
  preselectedSubmissionId?: string | null;
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

/* ---------- weight defaults ---------- */

const DEFAULT_WEIGHTS: CompareWeights = {
  premium_weight: 35,
  coverage_weight: 30,
  financial_weight: 20,
  completeness_weight: 15,
};

type WeightKey = keyof CompareWeights;
const WEIGHT_LABELS: { key: WeightKey; label: string }[] = [
  { key: 'premium_weight', label: 'Premium' },
  { key: 'coverage_weight', label: 'Coverage' },
  { key: 'financial_weight', label: 'Financial Strength' },
  { key: 'completeness_weight', label: 'Completeness' },
];

function weightsSum(w: CompareWeights): number {
  return w.premium_weight + w.coverage_weight + w.financial_weight + w.completeness_weight;
}

/* ---------- export helpers (AC-5.4) ---------- */

function generateExportHtml(
  clientName: string,
  submission: Submission,
  sortedQuotes: Quote[],
  recommendation: string | undefined,
): string {
  const now = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });

  const allRows: { label: string; values: string[] }[] = [
    ...COVERAGE_ROWS.map((r) => ({
      label: r.label,
      values: sortedQuotes.map((q) => (q.fields?.[r.key] as string) ?? '—'),
    })),
    {
      label: 'Named Perils Exclusions',
      values: sortedQuotes.map((q) => {
        const ex = q.fields?.named_perils_exclusions;
        return (!ex || ex.length === 0) ? 'None' : ex.join(', ');
      }),
    },
    {
      label: 'AM Best Rating',
      values: sortedQuotes.map((q) => q.fields?.carrier_am_best_rating ?? '—'),
    },
    {
      label: 'Terms / Special Conditions',
      values: sortedQuotes.map((q) => {
        const sc = q.fields?.special_conditions;
        return (!sc || sc.length === 0) ? 'None' : sc.join(', ');
      }),
    },
  ];

  const th = (t: string) => `<th style="text-align:right;padding:8px;border:1px solid #ddd;background:#f5f5f5;">${t}</th>`;
  const tableHeader = `<tr><th style="text-align:left;padding:8px;border:1px solid #ddd;background:#f5f5f5;">Coverage</th>${sortedQuotes.map((q) => th(q.carrier_name)).join('')}</tr>`;
  const tableRows = allRows.map((r) =>
    `<tr><td style="padding:8px;border:1px solid #ddd;font-weight:600;">${r.label}</td>${r.values.map((v) => `<td style="text-align:right;padding:8px;border:1px solid #ddd;">${v}</td>`).join('')}</tr>`
  ).join('');

  return `<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>Quote Comparison – ${clientName}</title>
<style>body{font-family:system-ui,sans-serif;padding:40px;max-width:1000px;margin:auto}table{border-collapse:collapse;width:100%}h1{font-size:1.5rem}h2{font-size:1.1rem;color:#555}.meta{color:#888;font-size:0.85rem}.rec{background:#fffbeb;border:1px solid #fbbf24;border-radius:8px;padding:16px;margin:16px 0}</style>
</head><body>
<h1>Quote Comparison Summary</h1>
<p class="meta">Client: <strong>${clientName}</strong> | ${submission.line_of_business} | TIV: ${submission.total_insured_value} | Generated: ${now}</p>
${recommendation ? `<div class="rec"><strong>AI Recommendation:</strong> ${recommendation}</div>` : ''}
<h2>Coverage Comparison</h2>
<table>${tableHeader}${tableRows}</table>
<h2>Placement Scores</h2>
<table>
<tr><th style="text-align:left;padding:8px;border:1px solid #ddd;background:#f5f5f5;">Carrier</th><th style="text-align:right;padding:8px;border:1px solid #ddd;background:#f5f5f5;">Score</th><th style="text-align:right;padding:8px;border:1px solid #ddd;background:#f5f5f5;">Rank</th><th style="text-align:right;padding:8px;border:1px solid #ddd;background:#f5f5f5;">Coverage</th><th style="text-align:right;padding:8px;border:1px solid #ddd;background:#f5f5f5;">Premium</th></tr>
${sortedQuotes.map((q) => `<tr><td style="padding:8px;border:1px solid #ddd;">${q.carrier_name}</td><td style="text-align:right;padding:8px;border:1px solid #ddd;">${q.scoring?.placement_score?.toFixed(1) ?? '—'}</td><td style="text-align:right;padding:8px;border:1px solid #ddd;">#${q.scoring?.placement_rank ?? '—'}</td><td style="text-align:right;padding:8px;border:1px solid #ddd;">${q.scoring?.coverage_adequacy ?? '—'}</td><td style="text-align:right;padding:8px;border:1px solid #ddd;">${q.scoring?.premium_percentile ?? '—'}</td></tr>`).join('')}
</table>
</body></html>`;
}

function downloadHtml(html: string, filename: string) {
  const blob = new Blob([html], { type: 'text/html' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/* ---------- combined view helpers (AC-5.3) ---------- */

function parseCurrency(value?: string): number {
  if (!value) return 0;
  const cleaned = value.replace(/[$,\s]/g, '');
  const num = parseFloat(cleaned);
  return isNaN(num) ? 0 : num;
}

interface CombinedLine {
  submissionId: string;
  lineOfBusiness: string;
  bestQuote: Quote;
  premium: number;
}

function buildCombinedLines(subs: Submission[]): CombinedLine[] {
  const lines: CombinedLine[] = [];
  for (const sub of subs) {
    if (!sub.quotes || sub.quotes.length === 0) continue;
    const sorted = [...sub.quotes].sort(
      (a, b) => (b.scoring?.placement_score ?? 0) - (a.scoring?.placement_score ?? 0)
    );
    const best = sorted[0];
    lines.push({
      submissionId: sub.id,
      lineOfBusiness: sub.line_of_business,
      bestQuote: best,
      premium: parseCurrency(best.fields?.annual_premium),
    });
  }
  return lines;
}

/* ---------- helpers ---------- */

function confidenceBadge(score: number | undefined) {
  if (score === undefined || score === null) return null;
  const pct = Math.round(score * 100);
  if (score >= 0.8) {
    return (
      <span className="inline-flex items-center gap-0.5 ml-1 px-1.5 py-0.5 text-[10px] font-medium rounded-full bg-green-100 text-green-700" title={`${pct}% confidence`}>
        <CheckCircle className="w-3 h-3" />{pct}%
      </span>
    );
  }
  if (score >= 0.6) {
    return (
      <span className="inline-flex items-center gap-0.5 ml-1 px-1.5 py-0.5 text-[10px] font-medium rounded-full bg-yellow-100 text-yellow-700" title={`${pct}% confidence`}>
        <Info className="w-3 h-3" />{pct}%
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-0.5 ml-1 px-1.5 py-0.5 text-[10px] font-medium rounded-full bg-red-100 text-red-700" title={`${pct}% confidence`}>
      <AlertTriangle className="w-3 h-3" />{pct}%
    </span>
  );
}

function needsReviewBadge(score: number | undefined) {
  if (score !== undefined && score !== null && score < 0.6) {
    return (
      <span className="inline-flex items-center gap-0.5 ml-1 px-1.5 py-0.5 text-[10px] font-semibold rounded bg-amber-100 text-amber-800 border border-amber-300">
        Needs Review
      </span>
    );
  }
  return null;
}

function fieldWithConfidence(value: string | undefined, score: number | undefined) {
  return (
    <span className="inline-flex items-center flex-wrap justify-end">
      <span>{value || '—'}</span>
      {confidenceBadge(score)}
      {needsReviewBadge(score)}
    </span>
  );
}

/* ---------- Clarification Modal ---------- */

function ClarificationModal({
  carrierName,
  quoteRef,
  fieldName,
  onClose,
}: {
  carrierName: string;
  quoteRef: string;
  fieldName: string;
  onClose: () => void;
}) {
  const [copied, setCopied] = useState(false);
  const template = `Dear ${carrierName},

Regarding quote ${quoteRef || '[Ref #]'}, we noticed "${fieldName}" is missing from your submission. Could you please provide this information at your earliest convenience?

Thank you for your prompt attention to this matter.

Best regards`;

  const handleCopy = () => {
    navigator.clipboard.writeText(template).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-xl max-w-lg w-full mx-4 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
            <Mail className="w-4 h-4 text-amber-600" /> Request Clarification
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X className="w-5 h-5" />
          </button>
        </div>
        <textarea
          readOnly
          value={template}
          className="w-full h-40 text-sm border border-slate-200 rounded-lg p-3 text-slate-700 bg-slate-50 resize-none focus:outline-none"
        />
        <div className="flex justify-end gap-2">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors"
          >
            <Copy className="w-4 h-4" />
            {copied ? 'Copied!' : 'Copy to Clipboard'}
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

/* ---------- Main component ---------- */

export default function QuotesTab({ clientId, clientName, preselectedSubmissionId }: QuotesTabProps) {
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [selectedSubmissionId, setSelectedSubmissionId] = useState<string | null>(
    preselectedSubmissionId ?? null
  );
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [loading, setLoading] = useState(true);
  const [submissionLoading, setSubmissionLoading] = useState(false);
  const [comparing, setComparing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [carrierName, setCarrierName] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const quoteInputRef = useRef<HTMLInputElement>(null);

  // Clarification modal state
  const [clarification, setClarification] = useState<{
    carrier: string; ref: string; field: string;
  } | null>(null);

  // AC-5.5: adjustable weights
  const [weights, setWeights] = useState<CompareWeights>({ ...DEFAULT_WEIGHTS });
  const [showWeights, setShowWeights] = useState(false);

  // AC-5.3: combined view
  const [showCombinedView, setShowCombinedView] = useState(false);

  const fetchSubmissions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getClientSubmissions(clientId);
      setSubmissions(data);
      // Auto-select first if none preselected
      if (!selectedSubmissionId && data.length > 0) {
        setSelectedSubmissionId(data[0]?.id ?? null);
      }
    } catch (err) {
      console.error('Failed to fetch submissions:', err);
      setError(err instanceof Error ? err.message : 'Failed to load submissions');
    } finally {
      setLoading(false);
    }
  }, [clientId, selectedSubmissionId]);

  const fetchSubmission = useCallback(async (subId: string) => {
    setSubmissionLoading(true);
    try {
      const data = await getSubmission(subId);
      setSubmission(data);
    } catch (err) {
      console.error('Failed to fetch submission:', err);
    } finally {
      setSubmissionLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSubmissions();
  }, [fetchSubmissions]);

  useEffect(() => {
    if (selectedSubmissionId) {
      fetchSubmission(selectedSubmissionId);
    } else {
      setSubmission(null);
    }
  }, [selectedSubmissionId, fetchSubmission]);

  // Sync preselectedSubmissionId changes
  useEffect(() => {
    if (preselectedSubmissionId) {
      setSelectedSubmissionId(preselectedSubmissionId);
    }
  }, [preselectedSubmissionId]);

  const handleQuoteUpload = async (file: File) => {
    if (!selectedSubmissionId || !carrierName.trim()) return;
    setUploading(true);
    try {
      await uploadQuote(selectedSubmissionId, file, carrierName.trim());
      setCarrierName('');
      await fetchSubmission(selectedSubmissionId);
    } catch (err) {
      console.error('Failed to upload quote:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleQuoteUpload(file);
  };

  const handleRunComparison = async () => {
    if (!selectedSubmissionId) return;
    setComparing(true);
    try {
      const isCustom =
        weights.premium_weight !== DEFAULT_WEIGHTS.premium_weight ||
        weights.coverage_weight !== DEFAULT_WEIGHTS.coverage_weight ||
        weights.financial_weight !== DEFAULT_WEIGHTS.financial_weight ||
        weights.completeness_weight !== DEFAULT_WEIGHTS.completeness_weight;
      await runQuoteComparison(selectedSubmissionId, isCustom ? weights : undefined);
      // Refresh submission to get updated scoring
      await fetchSubmission(selectedSubmissionId);
    } catch (err) {
      console.error('Comparison failed:', err);
    } finally {
      setComparing(false);
    }
  };

  // AC-5.5: weight slider handler — redistributes remaining weight proportionally
  const handleWeightChange = (key: WeightKey, newValue: number) => {
    setWeights((prev) => {
      const otherKeys = WEIGHT_LABELS.map((l) => l.key).filter((k) => k !== key);
      const otherSum = otherKeys.reduce((s, k) => s + prev[k], 0);
      const remaining = 100 - newValue;
      const updated = { ...prev, [key]: newValue };
      if (otherSum > 0) {
        for (const k of otherKeys) {
          updated[k] = Math.round((prev[k] / otherSum) * remaining);
        }
        const diff = 100 - (updated.premium_weight + updated.coverage_weight + updated.financial_weight + updated.completeness_weight);
        if (diff !== 0) updated[otherKeys[0]] += diff;
      } else {
        const each = Math.floor(remaining / otherKeys.length);
        for (const k of otherKeys) updated[k] = each;
        const diff2 = 100 - (updated.premium_weight + updated.coverage_weight + updated.financial_weight + updated.completeness_weight);
        if (diff2 !== 0) updated[otherKeys[0]] += diff2;
      }
      return updated;
    });
  };

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
          onClick={fetchSubmissions}
          className="mt-4 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (submissions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-slate-400">
        <FileText className="w-12 h-12 mb-4" />
        <p className="text-lg">No submissions yet</p>
        <p className="text-sm mt-1">Create a submission first to compare quotes.</p>
      </div>
    );
  }

  const quotes: Quote[] = submission?.quotes ?? [];
  const sortedQuotes = [...quotes].sort(
    (a, b) => (a.scoring?.placement_rank ?? 999) - (b.scoring?.placement_rank ?? 999)
  );
  const recommended = sortedQuotes[0];
  const rationale = recommended?.scoring?.recommendation_rationale;

  // AC-5.3: combined view data
  const submissionsWithQuotes = submissions.filter((s) => (s.quotes?.length ?? 0) > 0);
  const showCombinedToggle = submissionsWithQuotes.length > 1;
  const combinedLines = showCombinedView ? buildCombinedLines(submissionsWithQuotes) : [];
  const combinedTotal = combinedLines.reduce((sum, l) => sum + l.premium, 0);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Clarification Modal */}
      {clarification && (
        <ClarificationModal
          carrierName={clarification.carrier}
          quoteRef={clarification.ref}
          fieldName={clarification.field}
          onClose={() => setClarification(null)}
        />
      )}

      {/* Submission Selector */}
      <div className="bg-white rounded-lg border border-slate-200 p-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <BarChart3 className="w-5 h-5 text-amber-600" />
            <h3 className="text-base font-semibold text-slate-900">Quote Comparison</h3>
          </div>
          <div className="flex items-center gap-3">
            {/* AC-5.3: Combined View toggle */}
            {showCombinedToggle && (
              <button
                onClick={() => setShowCombinedView((v) => !v)}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
                  showCombinedView
                    ? 'bg-amber-100 border-amber-300 text-amber-800'
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                Combined View
              </button>
            )}
            <label className="text-sm text-slate-500">Submission:</label>
            <select
              value={selectedSubmissionId ?? ''}
              onChange={(e) => setSelectedSubmissionId(e.target.value || null)}
              className="px-3 py-1.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
            >
              {submissions.map((sub) => (
                <option key={sub.id} value={sub.id}>
                  {sub.line_of_business} — {sub.status} — TIV {sub.total_insured_value}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* AC-5.3: Combined View Panel */}
      {showCombinedView && combinedLines.length > 0 && (
        <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-5">
          <div className="flex items-center gap-2 mb-3">
            <Layers className="w-5 h-5 text-indigo-600" />
            <h3 className="text-sm font-semibold text-indigo-800">
              Multi-Line Combined Summary
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-indigo-200 bg-indigo-100/50">
                  <th className="text-left px-4 py-2 text-xs font-semibold text-indigo-600 uppercase">Line of Business</th>
                  <th className="text-left px-4 py-2 text-xs font-semibold text-indigo-600 uppercase">Best Carrier</th>
                  <th className="text-right px-4 py-2 text-xs font-semibold text-indigo-600 uppercase">Score</th>
                  <th className="text-right px-4 py-2 text-xs font-semibold text-indigo-600 uppercase">Premium</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-indigo-100">
                {combinedLines.map((line) => (
                  <tr key={line.submissionId}>
                    <td className="px-4 py-2 font-medium text-slate-700">{line.lineOfBusiness}</td>
                    <td className="px-4 py-2 text-slate-700">{line.bestQuote.carrier_name}</td>
                    <td className="px-4 py-2 text-right font-mono text-slate-900">
                      {line.bestQuote.scoring?.placement_score?.toFixed(1) ?? '—'}
                    </td>
                    <td className="px-4 py-2 text-right font-mono text-slate-900">
                      {line.bestQuote.fields?.annual_premium ?? '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t-2 border-indigo-300">
                  <td className="px-4 py-2 font-semibold text-indigo-800" colSpan={3}>
                    Total Blended Premium
                  </td>
                  <td className="px-4 py-2 text-right font-mono font-bold text-indigo-800">
                    ${combinedTotal.toLocaleString('en-US', { minimumFractionDigits: 0 })}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}

      {/* Upload Carrier Quote */}
      {selectedSubmissionId && (
        <div className="bg-white rounded-lg border border-slate-200 p-5 space-y-4">
          <h3 className="text-sm font-semibold text-slate-900">Upload Carrier Quote</h3>
          <div className="flex gap-3">
            <input
              type="text"
              placeholder="Carrier name"
              value={carrierName}
              onChange={(e) => setCarrierName(e.target.value)}
              className="flex-1 px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
          </div>
          <div
            onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive ? 'border-amber-400 bg-amber-50' : 'border-slate-200 hover:border-slate-300'
            }`}
          >
            <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
            <p className="text-sm text-slate-500">
              Drag &amp; drop a PDF or Excel file, or{' '}
              <button
                type="button"
                onClick={() => quoteInputRef.current?.click()}
                className="text-amber-600 hover:text-amber-700 font-medium"
                disabled={uploading || !carrierName.trim()}
              >
                browse
              </button>
            </p>
            <input
              ref={quoteInputRef}
              type="file"
              accept=".pdf,.xlsx,.xls"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleQuoteUpload(file);
              }}
            />
            {uploading && (
              <p className="text-xs text-amber-600 mt-2">Uploading…</p>
            )}
          </div>
        </div>
      )}

      {/* AC-5.5: Adjust Weights Panel */}
      {selectedSubmissionId && quotes.length > 0 && (
        <div className="bg-white rounded-lg border border-slate-200">
          <button
            onClick={() => setShowWeights((v) => !v)}
            className="w-full flex items-center justify-between px-5 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <SlidersHorizontal className="w-4 h-4 text-slate-500" />
              Adjust Ranking Weights
              {weightsSum(weights) !== 100 && (
                <span className="text-xs text-red-500 font-normal">
                  (sum: {weightsSum(weights)}%, must be 100%)
                </span>
              )}
            </div>
            {showWeights ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
          {showWeights && (
            <div className="px-5 pb-5 space-y-4 border-t border-slate-100">
              <p className="text-xs text-slate-500 pt-3">
                Adjust the relative importance of each factor. Values will be redistributed to total 100%.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {WEIGHT_LABELS.map(({ key, label }) => (
                  <div key={key} className="space-y-1">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-medium text-slate-600">{label}</label>
                      <span className="text-xs font-mono text-slate-500">{weights[key]}%</span>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={100}
                      value={weights[key]}
                      onChange={(e) => handleWeightChange(key, parseInt(e.target.value, 10))}
                      className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-amber-600"
                    />
                  </div>
                ))}
              </div>
              <div className="flex items-center justify-between pt-2">
                <button
                  onClick={() => setWeights({ ...DEFAULT_WEIGHTS })}
                  className="text-xs text-slate-500 hover:text-slate-700 underline"
                >
                  Reset to defaults
                </button>
                <button
                  onClick={handleRunComparison}
                  disabled={comparing || weightsSum(weights) !== 100}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-amber-600 hover:bg-amber-700 disabled:opacity-50 rounded-lg transition-colors"
                >
                  {comparing ? <Loader2 className="w-3 h-3 animate-spin" /> : <BarChart3 className="w-3 h-3" />}
                  Re-score with Weights
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Run Comparison */}
      {selectedSubmissionId && quotes.length > 0 && (
        <div className="flex justify-end gap-3">
          {/* AC-5.4: Download Summary */}
          {sortedQuotes.length > 0 && sortedQuotes[0]?.scoring?.placement_score > 0 && (
            <button
              onClick={() => {
                if (!submission) return;
                const html = generateExportHtml(
                  clientName ?? 'Client',
                  submission,
                  sortedQuotes,
                  rationale,
                );
                const safeName = (clientName ?? 'client').replace(/[^a-zA-Z0-9]/g, '_');
                downloadHtml(html, `quote_comparison_${safeName}.html`);
              }}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg transition-colors"
            >
              <Download className="w-4 h-4" />
              Download Summary
            </button>
          )}
          <button
            onClick={handleRunComparison}
            disabled={comparing}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 disabled:opacity-50 rounded-lg transition-colors"
          >
            {comparing ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <BarChart3 className="w-4 h-4" />
            )}
            {comparing ? 'Comparing…' : 'Run Comparison'}
          </button>
        </div>
      )}

      {/* Loading submission */}
      {submissionLoading && (
        <div className="flex items-center justify-center h-48">
          <Loader2 className="w-8 h-8 animate-spin text-amber-600" />
        </div>
      )}

      {/* No quotes */}
      {!submissionLoading && quotes.length === 0 && selectedSubmissionId && (
        <div className="flex flex-col items-center justify-center py-16 text-slate-400">
          <BarChart3 className="w-12 h-12 mb-4" />
          <p className="text-lg">No quotes to compare yet.</p>
          <p className="text-sm mt-1">Upload carrier quotes above first.</p>
        </div>
      )}

      {/* Quote Comparison Content */}
      {!submissionLoading && quotes.length > 0 && (
        <>
          {/* AI Recommendation */}
          {rationale && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-5">
              <div className="flex items-start gap-3">
                <Star className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
                <div>
                  <h3 className="text-sm font-semibold text-amber-800">
                    AI Recommendation: {recommended?.carrier_name}
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
                      <div className="text-xs">
                        <div className="flex items-center gap-1.5">
                          <AlertTriangle className="w-3 h-3 text-red-500" />
                          <span className="text-slate-600">Coverage Gaps:</span>
                        </div>
                        <ul className="mt-1 ml-4 space-y-0.5">
                          {scoring?.coverage_gaps?.map((gap, i) => (
                            <li key={i} className="flex items-center gap-1.5">
                              <span className="text-red-600">{gap}</span>
                              <button
                                onClick={() =>
                                  setClarification({
                                    carrier: q.carrier_name,
                                    ref: q.fields?.quote_reference_number || '',
                                    field: gap,
                                  })
                                }
                                className="text-[10px] text-amber-600 hover:text-amber-800 underline whitespace-nowrap"
                              >
                                Request Clarification
                              </button>
                            </li>
                          ))}
                        </ul>
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
                        {fieldWithConfidence(
                          q.fields?.[row.key] as string,
                          q.confidence_scores?.[row.key],
                        )}
                      </td>
                    ))}
                  </tr>
                ))}

                {/* Effective Date */}
                <tr>
                  <td className="px-4 py-3 font-medium text-slate-700">Effective Date</td>
                  {sortedQuotes.map((q) => (
                    <td key={q.id} className="px-4 py-3 text-right text-slate-700">
                      {fieldWithConfidence(
                        q.fields?.effective_date ?? undefined,
                        q.confidence_scores?.effective_date,
                      )}
                    </td>
                  ))}
                </tr>

                {/* AM Best Rating */}
                <tr>
                  <td className="px-4 py-3 font-medium text-slate-700">AM Best Rating</td>
                  {sortedQuotes.map((q) => (
                    <td key={q.id} className="px-4 py-3 text-right text-slate-700">
                      {fieldWithConfidence(
                        q.fields?.carrier_am_best_rating,
                        q.confidence_scores?.carrier_am_best_rating,
                      )}
                    </td>
                  ))}
                </tr>

                {/* Policy Period */}
                <tr>
                  <td className="px-4 py-3 font-medium text-slate-700">Policy Period</td>
                  {sortedQuotes.map((q) => (
                    <td key={q.id} className="px-4 py-3 text-right text-slate-700">
                      {fieldWithConfidence(
                        q.fields?.policy_period,
                        q.confidence_scores?.policy_period,
                      )}
                    </td>
                  ))}
                </tr>

                {/* Expiry Date */}
                <tr>
                  <td className="px-4 py-3 font-medium text-slate-700">Quote Expiry</td>
                  {sortedQuotes.map((q) => (
                    <td key={q.id} className="px-4 py-3 text-right text-slate-700">
                      {fieldWithConfidence(
                        q.fields?.expiry_date ?? undefined,
                        q.confidence_scores?.expiry_date,
                      )}
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
                        {confidenceBadge(q.confidence_scores?.named_perils_exclusions)}
                      </td>
                    );
                  })}
                </tr>

                {/* AC-5.1: Terms / Special Conditions */}
                <tr>
                  <td className="px-4 py-3 font-medium text-slate-700 align-top">
                    Terms / Special Conditions
                  </td>
                  {sortedQuotes.map((q) => {
                    const conditions = q.fields?.special_conditions;
                    return (
                      <td key={q.id} className="px-4 py-3 text-right text-slate-700 align-top">
                        {(!conditions || conditions.length === 0) ? (
                          <span className="text-slate-400 text-xs">None</span>
                        ) : (
                          <ul className="space-y-0.5">
                            {conditions.map((sc, i) => (
                              <li key={i} className="text-xs">{sc}</li>
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
        </>
      )}
    </div>
  );
}
