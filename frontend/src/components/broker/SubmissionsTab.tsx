'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  FileText, Plus, ArrowLeft, AlertTriangle,
  CheckCircle, Building2,
} from 'lucide-react';
import {
  getClientSubmissions, getSubmission, createSubmission,
  generatePackage, updateAcordFields, updateSubmission,
  extractAcordFields,
} from '../../lib/broker-api';
import type { Submission, CreateSubmissionRequest, GeneratePackageResponse } from '../../lib/broker-types';
import DocumentUploadPanel from './DocumentUploadPanel';
import AcordFormView from './AcordFormView';
import CarrierSelector from './CarrierSelector';
import SubmissionEmailEditor from './SubmissionEmailEditor';

/* ------------------------------------------------------------------ */
/*  Props & constants                                                 */
/* ------------------------------------------------------------------ */

interface SubmissionsTabProps {
  clientId: string;
  clientName?: string;
  onViewSubmission: (submissionId: string) => void;
  selectedSubmissionId: string | null;
  renewalDraft?: { line_of_business: string; effective_date: string; expiration_date: string } | null;
  onRenewalDraftConsumed?: () => void;
}

const STATUS_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  draft: { bg: 'bg-slate-100', text: 'text-slate-600', label: 'Draft' },
  submitted: { bg: 'bg-blue-100', text: 'text-blue-700', label: 'Submitted' },
  quoted: { bg: 'bg-amber-100', text: 'text-amber-700', label: 'Quoted' },
  bound: { bg: 'bg-green-100', text: 'text-green-700', label: 'Bound' },
};

/* ------------------------------------------------------------------ */
/*  Phase indicator for horizontal lifecycle                          */
/* ------------------------------------------------------------------ */

const PHASES = [
  { id: 'documents', label: 'Documents', icon: FileText },
  { id: 'acord', label: 'ACORD Forms', icon: FileText },
  { id: 'package', label: 'Package', icon: Building2 },
  { id: 'review', label: 'Review & Send', icon: CheckCircle },
] as const;

type PhaseId = typeof PHASES[number]['id'];

function PhaseBar({
  activePhase,
  onSelectPhase,
  completionMap,
}: {
  activePhase: PhaseId | null;
  onSelectPhase: (phase: PhaseId) => void;
  completionMap: Record<PhaseId, boolean>;
}) {
  return (
    <div className="flex items-center gap-0 bg-white rounded-lg border border-slate-200 overflow-hidden">
      {PHASES.map((phase, idx) => {
        const Icon = phase.icon;
        const isActive = activePhase === phase.id;
        const isComplete = completionMap[phase.id];
        return (
          <React.Fragment key={phase.id}>
            {idx > 0 && (
              <div className="w-px h-10 bg-slate-200 flex-shrink-0" />
            )}
            <button
              onClick={() => onSelectPhase(phase.id)}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-amber-50 text-amber-700 border-b-2 border-amber-500'
                  : isComplete
                  ? 'text-green-700 hover:bg-green-50'
                  : 'text-slate-500 hover:bg-slate-50'
              }`}
            >
              {isComplete && !isActive ? (
                <CheckCircle className="w-4 h-4 text-green-500" />
              ) : (
                <Icon className="w-4 h-4" />
              )}
              <span>{phase.label}</span>
              {isComplete && !isActive && (
                <span className="text-[10px] font-semibold text-green-600 bg-green-100 px-1.5 py-0.5 rounded-full">✓</span>
              )}
            </button>
          </React.Fragment>
        );
      })}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Helper                                                            */
/* ------------------------------------------------------------------ */

function lobLabel(raw: string): string {
  return (raw ?? '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/* ------------------------------------------------------------------ */
/*  Main component                                                    */
/* ------------------------------------------------------------------ */

export default function SubmissionsTab({
  clientId,
  clientName,
  onViewSubmission,
  selectedSubmissionId,
  renewalDraft,
  onRenewalDraftConsumed,
}: SubmissionsTabProps) {
  /* ---- All hooks up front ---- */
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [expandedId, setExpandedId] = useState<string | null>(selectedSubmissionId);
  const [expandedSubmission, setExpandedSubmission] = useState<Submission | null>(null);
  const [expandedLoading, setExpandedLoading] = useState(false);

  const [showNewModal, setShowNewModal] = useState(false);
  const [creating, setCreating] = useState(false);

  const [extracting, setExtracting] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [selectedCarriers, setSelectedCarriers] = useState<string[]>([]);
  const [packageResult, setPackageResult] = useState<GeneratePackageResponse | null>(null);

  const [activePhase, setActivePhase] = useState<PhaseId | null>('documents');

  const [newForm, setNewForm] = useState({
    line_of_business: 'property',
    effective_date: '',
    expiration_date: '',
    total_insured_value: '',
  });

  /* ---- Handle renewal draft from Profile tab ---- */
  useEffect(() => {
    if (renewalDraft) {
      setNewForm({
        line_of_business: renewalDraft.line_of_business,
        effective_date: renewalDraft.effective_date,
        expiration_date: renewalDraft.expiration_date,
        total_insured_value: '',
      });
      setShowNewModal(true);
      onRenewalDraftConsumed?.();
    }
  }, [renewalDraft, onRenewalDraftConsumed]);

  /* ---- Data fetching ---- */
  const fetchSubmissions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getClientSubmissions(clientId);
      setSubmissions(data);
    } catch (err) {
      console.error('Failed to fetch submissions:', err);
      setError(err instanceof Error ? err.message : 'Failed to load submissions');
    } finally {
      setLoading(false);
    }
  }, [clientId]);

  const fetchExpanded = useCallback(async (subId: string) => {
    setExpandedLoading(true);
    try {
      const data = await getSubmission(subId);
      setExpandedSubmission(data);
      if ((data.submitted_carriers?.length ?? 0) > 0) {
        setSelectedCarriers(data.submitted_carriers ?? []);
      }
    } catch (err) {
      console.error('Failed to fetch submission detail:', err);
    } finally {
      setExpandedLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSubmissions();
  }, [fetchSubmissions]);

  useEffect(() => {
    if (expandedId) {
      fetchExpanded(expandedId);
    } else {
      setExpandedSubmission(null);
      setPackageResult(null);
      setSelectedCarriers([]);
    }
  }, [expandedId, fetchExpanded]);

  /* ---- Handlers ---- */
  const handleCreate = async () => {
    if (!newForm.line_of_business || !newForm.effective_date) return;
    setCreating(true);
    try {
      const req: CreateSubmissionRequest = {
        client_id: clientId,
        line_of_business: newForm.line_of_business,
        effective_date: newForm.effective_date,
        expiration_date: newForm.expiration_date,
        total_insured_value: newForm.total_insured_value,
      };
      const created = await createSubmission(req);
      setShowNewModal(false);
      setNewForm({
        line_of_business: 'property',
        effective_date: '',
        expiration_date: '',
        total_insured_value: '',
      });
      await fetchSubmissions();
      setExpandedId(created.id);
      onViewSubmission(created.id);
    } catch (err) {
      console.error('Failed to create submission:', err);
      alert('Failed to create submission. Please try again.');
    } finally {
      setCreating(false);
    }
  };

  const handleSelectSubmission = (subId: string) => {
    const newId = expandedId === subId ? null : subId;
    setExpandedId(newId);
    if (newId) onViewSubmission(newId);
  };

  const handleExtractAcord = async () => {
    if (!expandedId) return;
    setExtracting(true);
    try {
      // Call the extraction endpoint to run LLM extraction
      await extractAcordFields(expandedId);
      // Refresh submission to pick up the extracted ACORD fields
      await fetchExpanded(expandedId);
      setActivePhase('acord');
    } catch (err) {
      console.error('Failed to extract ACORD fields:', err);
    } finally {
      setExtracting(false);
    }
  };

  const handleFieldUpdate = async (
    form: '125' | '140',
    key: string,
    value: string,
  ) => {
    if (!expandedId || !expandedSubmission) return;
    try {
      const updated125 = { ...(expandedSubmission.acord_125_fields ?? {}) };
      const updated140 = { ...(expandedSubmission.acord_140_fields ?? {}) };
      if (form === '125') {
        updated125[key] = value;
      } else {
        updated140[key] = value;
      }
      await updateAcordFields(expandedId, updated125, updated140);
      setExpandedSubmission((prev) =>
        prev
          ? {
              ...prev,
              acord_125_fields: updated125,
              acord_140_fields: updated140,
            }
          : prev,
      );
    } catch (err) {
      console.error('Failed to update ACORD field:', err);
    }
  };

  const handleGeneratePackage = async () => {
    if (!expandedId || selectedCarriers.length === 0) return;
    setGenerating(true);
    try {
      // Persist selected carriers first
      await updateSubmission(expandedId, {
        submitted_carriers: selectedCarriers,
      } as Partial<Submission>);
      const result = await generatePackage(expandedId, selectedCarriers);
      setPackageResult(result);
      await fetchExpanded(expandedId);
      setActivePhase('review');
    } catch (err) {
      console.error('Failed to generate package:', err);
    } finally {
      setGenerating(false);
    }
  };

  /* ================================================================ */
  /*  Loading / Error states                                          */
  /* ================================================================ */

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

  /* ================================================================ */
  /*  Submission detail view (4 steps)                                */
  /* ================================================================ */

  if (expandedId && expandedSubmission) {
    const sub = expandedSubmission;
    const statusStyle = STATUS_STYLES[sub.status] ?? {
      bg: 'bg-slate-100',
      text: 'text-slate-600',
      label: sub.status,
    };
    const displayName = clientName ?? 'Client';
    const hasDocuments = (sub.documents?.length ?? 0) > 0;
    const hasAcordFields =
      Object.keys(sub.acord_125_fields ?? {}).length > 0 ||
      Object.keys(sub.acord_140_fields ?? {}).length > 0;
    const hasPackage = sub.status !== 'draft' || packageResult !== null;
    const isSubmitted = sub.status === 'bound';

    return (
      <div className="p-6 max-w-7xl mx-auto space-y-5">
        {/* Back to list */}
        <button
          onClick={() => setExpandedId(null)}
          className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Submissions
        </button>

        {/* Submission Header */}
        <div className="bg-white rounded-lg border border-slate-200 p-5 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
              <Building2 className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-900">
                Submission: {lobLabel(sub.line_of_business)}
              </h2>
              <p className="text-sm text-slate-500">
                {displayName} • TIV {sub.total_insured_value} •{' '}
                {sub.effective_date} to {sub.expiration_date}
              </p>
            </div>
          </div>
          <span
            className={`text-xs font-medium px-2.5 py-1 rounded-full ${statusStyle.bg} ${statusStyle.text}`}
          >
            {statusStyle.label}
          </span>
        </div>

        {/* Horizontal phase bar */}
        <PhaseBar
          activePhase={activePhase}
          onSelectPhase={(phase) =>
            setActivePhase(activePhase === phase ? null : phase)
          }
          completionMap={{
            documents: hasDocuments,
            acord: hasAcordFields,
            package: hasPackage,
            review: isSubmitted,
          }}
        />

        {/* Phase detail panel (expands below the phase bar) */}
        {activePhase === 'documents' && (
          <div className="bg-white rounded-lg border border-slate-200 p-5 animate-in fade-in duration-200">
            <DocumentUploadPanel
              submissionId={sub.id}
              documents={sub.documents ?? []}
              onDocumentUploaded={() => fetchExpanded(sub.id)}
              onExtractAcord={handleExtractAcord}
              extracting={extracting}
            />
          </div>
        )}

        {activePhase === 'acord' && (
          <div className="bg-white rounded-lg border border-slate-200 p-5 animate-in fade-in duration-200">
            {!hasAcordFields && hasDocuments && (
              <div className="flex items-center justify-between mb-4 p-3 bg-amber-50 rounded-lg border border-amber-100">
                <p className="text-sm text-amber-700">
                  Documents uploaded but ACORD fields not yet extracted.
                </p>
                <button
                  onClick={handleExtractAcord}
                  disabled={extracting}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 disabled:opacity-50 rounded-lg transition-colors"
                >
                  {extracting ? 'Extracting…' : 'Extract ACORD Fields'}
                </button>
              </div>
            )}
            <AcordFormView
              acord125Fields={sub.acord_125_fields ?? {}}
              acord140Fields={sub.acord_140_fields ?? {}}
              confidenceMap={sub.acord_field_confidence ?? {}}
              sourceMap={sub.acord_field_sources ?? {}}
              onFieldUpdate={handleFieldUpdate}
            />
          </div>
        )}

        {activePhase === 'package' && (
          <div className="bg-white rounded-lg border border-slate-200 p-5 animate-in fade-in duration-200">
            <CarrierSelector
              selectedCarriers={selectedCarriers}
              onCarriersChange={setSelectedCarriers}
              onGeneratePackage={handleGeneratePackage}
              generating={generating}
              disabled={isSubmitted}
            />
          </div>
        )}

        {activePhase === 'review' && (
          <div className="bg-white rounded-lg border border-slate-200 p-5 animate-in fade-in duration-200">
            <SubmissionEmailEditor
              carriers={selectedCarriers}
              clientName={displayName}
              lineOfBusiness={sub.line_of_business ?? ''}
              documents={sub.documents ?? []}
              submissionId={sub.id}
              onMarkSent={() => fetchExpanded(sub.id)}
            />
          </div>
        )}

        {/* Summary cards row — always visible at bottom */}
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-white rounded-lg border border-slate-200 p-4 text-center">
            <p className="text-2xl font-bold text-slate-900">{sub.documents?.length ?? 0}</p>
            <p className="text-xs text-slate-500 mt-1">Documents</p>
          </div>
          <div className="bg-white rounded-lg border border-slate-200 p-4 text-center">
            <p className="text-2xl font-bold text-slate-900">
              {Object.keys(sub.acord_125_fields ?? {}).length + Object.keys(sub.acord_140_fields ?? {}).length}
            </p>
            <p className="text-xs text-slate-500 mt-1">ACORD Fields</p>
          </div>
          <div className="bg-white rounded-lg border border-slate-200 p-4 text-center">
            <p className="text-2xl font-bold text-slate-900">{sub.submitted_carriers?.length ?? 0}</p>
            <p className="text-xs text-slate-500 mt-1">Carriers</p>
          </div>
          <div className="bg-white rounded-lg border border-slate-200 p-4 text-center">
            <p className="text-2xl font-bold text-slate-900">{sub.quotes?.length ?? 0}</p>
            <p className="text-xs text-slate-500 mt-1">Quotes</p>
          </div>
        </div>
      </div>
    );
  }

  /* Loading spinner for expanded submission */
  if (expandedId && expandedLoading) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <button
          onClick={() => setExpandedId(null)}
          className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Submissions
        </button>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-600" />
        </div>
      </div>
    );
  }

  /* ================================================================ */
  /*  Submissions list                                                */
  /* ================================================================ */

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="bg-white rounded-lg border border-slate-200">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200">
          <h2 className="text-base font-semibold text-slate-900">
            {clientName ? `Submissions for ${clientName}` : 'Submissions'}
          </h2>
          <button
            onClick={() => setShowNewModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Submission
          </button>
        </div>

        {submissions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-slate-400">
            <FileText className="w-10 h-10 mb-3" />
            <p className="text-sm">
              No submissions yet. Create your first submission.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {submissions.map((sub) => {
              const style = STATUS_STYLES[sub.status] ?? {
                bg: 'bg-slate-100',
                text: 'text-slate-600',
                label: sub.status,
              };
              return (
                <button
                  key={sub.id}
                  onClick={() => handleSelectSubmission(sub.id)}
                  className="w-full text-left px-5 py-4 hover:bg-slate-50 transition-colors flex items-center justify-between"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center">
                      <FileText className="w-4 h-4 text-slate-500" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-900">
                        {lobLabel(sub.line_of_business)} Submission
                      </p>
                      <p className="text-xs text-slate-500">
                        TIV {sub.total_insured_value} • Created{' '}
                        {new Date(sub.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-slate-500">
                      {sub.documents?.length ?? 0} doc
                      {(sub.documents?.length ?? 0) !== 1 ? 's' : ''} •{' '}
                      {sub.quotes?.length ?? 0} quote
                      {(sub.quotes?.length ?? 0) !== 1 ? 's' : ''}
                    </span>
                    {(() => {
                      const updatedAt = sub.updated_at ? new Date(sub.updated_at) : null;
                      const sevenDaysAgo = new Date();
                      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
                      const isStale = updatedAt && updatedAt < sevenDaysAgo && sub.status !== 'bound';
                      return isStale ? (
                        <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-red-100 text-red-700">
                          Stale
                        </span>
                      ) : null;
                    })()}
                    <span
                      className={`text-xs font-medium px-2.5 py-1 rounded-full ${style.bg} ${style.text}`}
                    >
                      {style.label}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* New Submission Modal */}
      {showNewModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">
              New Submission
            </h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Line of Business *
                </label>
                <select
                  value={newForm.line_of_business}
                  onChange={(e) =>
                    setNewForm({ ...newForm, line_of_business: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
                >
                  <option value="property">Property</option>
                  <option value="general_liability">General Liability</option>
                  <option value="workers_comp">Workers Comp</option>
                  <option value="commercial_auto">Commercial Auto</option>
                  <option value="umbrella">Umbrella</option>
                  <option value="professional_liability">
                    Professional Liability
                  </option>
                  <option value="dno">D&amp;O</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Effective Date *
                </label>
                <input
                  type="date"
                  value={newForm.effective_date}
                  onChange={(e) =>
                    setNewForm({ ...newForm, effective_date: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Expiration Date
                </label>
                <input
                  type="date"
                  value={newForm.expiration_date}
                  onChange={(e) =>
                    setNewForm({ ...newForm, expiration_date: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Total Insured Value
                </label>
                <input
                  type="text"
                  value={newForm.total_insured_value}
                  onChange={(e) =>
                    setNewForm({
                      ...newForm,
                      total_insured_value: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
                  placeholder="$10,000,000"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowNewModal(false)}
                className="flex-1 px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={
                  creating ||
                  !newForm.line_of_business ||
                  !newForm.effective_date
                }
                className="flex-1 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50 transition-colors"
              >
                {creating ? 'Creating…' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
