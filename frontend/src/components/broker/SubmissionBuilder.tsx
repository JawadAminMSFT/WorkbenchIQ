'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  FileText, Upload, AlertTriangle, CheckCircle, Clock,
  Building2, Briefcase, XCircle,
} from 'lucide-react';
import { getSubmission, uploadQuote } from '../../lib/broker-api';
import type { Submission } from '../../lib/broker-types';

interface SubmissionBuilderProps {
  submissionId: string;
}

const STATUS_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  draft: { bg: 'bg-slate-100', text: 'text-slate-600', label: 'Draft' },
  submitted: { bg: 'bg-blue-100', text: 'text-blue-700', label: 'Submitted' },
  quoted: { bg: 'bg-amber-100', text: 'text-amber-700', label: 'Quoted' },
  bound: { bg: 'bg-green-100', text: 'text-green-700', label: 'Bound' },
};

const DOC_STATUS_ICON: Record<string, React.ReactNode> = {
  pending: <Clock className="w-4 h-4 text-slate-400" />,
  processed: <CheckCircle className="w-4 h-4 text-green-500" />,
  error: <XCircle className="w-4 h-4 text-red-500" />,
};

function confidenceBadge(confidence: number) {
  const pct = Math.round(confidence * 100);
  if (pct >= 80) return <span className="text-xs font-medium text-green-700 bg-green-100 px-1.5 py-0.5 rounded">{pct}%</span>;
  if (pct >= 60) return <span className="text-xs font-medium text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded">{pct}%</span>;
  return <span className="text-xs font-medium text-red-700 bg-red-100 px-1.5 py-0.5 rounded">{pct}%</span>;
}

export default function SubmissionBuilder({ submissionId }: SubmissionBuilderProps) {
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [carrierName, setCarrierName] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const quoteInputRef = useRef<HTMLInputElement>(null);

  const fetchSubmission = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getSubmission(submissionId);
      setSubmission(data);
    } catch (err) {
      console.error('Failed to fetch submission:', err);
      setError(err instanceof Error ? err.message : 'Failed to load submission');
    } finally {
      setLoading(false);
    }
  }, [submissionId]);

  useEffect(() => {
    fetchSubmission();
  }, [fetchSubmission]);

  const handleQuoteUpload = async (file: File) => {
    if (!carrierName.trim()) return;
    setUploading(true);
    try {
      await uploadQuote(submissionId, file, carrierName.trim());
      setCarrierName('');
      await fetchSubmission();
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

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-600" />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-red-600">
        <AlertTriangle className="w-12 h-12 mb-4" />
        <p className="text-lg font-medium">{error}</p>
        <button
          onClick={fetchSubmission}
          className="mt-4 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!submission) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-slate-400">
        <FileText className="w-12 h-12 mb-4" />
        <p className="text-lg">Submission not found</p>
      </div>
    );
  }

  const statusStyle = STATUS_STYLES[submission.status] ?? { bg: 'bg-slate-100', text: 'text-slate-600', label: submission.status };
  const acord125Entries = Object.entries(submission.acord_125_fields ?? {});
  const acord140Entries = Object.entries(submission.acord_140_fields ?? {});
  const confidenceMap = submission.acord_field_confidence ?? {};

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Submission Header */}
      <div className="bg-white rounded-lg border border-slate-200 p-5 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
            <Building2 className="w-5 h-5 text-amber-600" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900">
              {submission.line_of_business} Submission
            </h2>
            <p className="text-sm text-slate-500">
              TIV {submission.total_insured_value} • {submission.effective_date} to {submission.expiration_date}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${statusStyle.bg} ${statusStyle.text}`}>
            {statusStyle.label}
          </span>
          <button className="px-4 py-2 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 rounded-lg transition-colors">
            Generate Submission Package
          </button>
        </div>
      </div>

      {/* ACORD 125 Fields */}
      {acord125Entries.length > 0 && (
        <div className="bg-white rounded-lg border border-slate-200">
          <div className="px-5 py-4 border-b border-slate-200 flex items-center gap-2">
            <Briefcase className="w-4 h-4 text-amber-600" />
            <h3 className="text-sm font-semibold text-slate-900">ACORD 125 Fields</h3>
          </div>
          <div className="divide-y divide-slate-100">
            {acord125Entries.map(([key, value]) => (
              <div key={key} className="px-5 py-3 flex items-center justify-between">
                <p className="text-sm font-medium text-slate-700">{key}</p>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-900 font-mono">
                    {value !== null && value !== undefined ? String(value) : '—'}
                  </span>
                  {confidenceMap[key] != null && confidenceBadge(confidenceMap[key])}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ACORD 140 Fields */}
      {acord140Entries.length > 0 && (
        <div className="bg-white rounded-lg border border-slate-200">
          <div className="px-5 py-4 border-b border-slate-200 flex items-center gap-2">
            <Briefcase className="w-4 h-4 text-amber-600" />
            <h3 className="text-sm font-semibold text-slate-900">ACORD 140 Fields</h3>
          </div>
          <div className="divide-y divide-slate-100">
            {acord140Entries.map(([key, value]) => (
              <div key={key} className="px-5 py-3 flex items-center justify-between">
                <p className="text-sm font-medium text-slate-700">{key}</p>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-900 font-mono">
                    {value !== null && value !== undefined ? String(value) : '—'}
                  </span>
                  {confidenceMap[key] != null && confidenceBadge(confidenceMap[key])}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Documents */}
      <div className="bg-white rounded-lg border border-slate-200">
        <div className="px-5 py-4 border-b border-slate-200">
          <h3 className="text-sm font-semibold text-slate-900">Documents</h3>
        </div>
        {(submission.documents?.length ?? 0) === 0 ? (
          <div className="flex flex-col items-center py-10 text-slate-400">
            <FileText className="w-8 h-8 mb-2" />
            <p className="text-sm">No documents uploaded yet.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {submission.documents?.map((doc) => (
              <div key={doc.id} className="px-5 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {DOC_STATUS_ICON[doc.status] ?? <Clock className="w-4 h-4 text-slate-400" />}
                  <div>
                    <p className="text-sm font-medium text-slate-700">{doc.filename}</p>
                    <p className="text-xs text-slate-400">
                      {doc.type} • {new Date(doc.uploaded_at).toLocaleDateString()}
                      {doc.carrier_name && ` • ${doc.carrier_name}`}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quote Upload */}
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
    </div>
  );
}
