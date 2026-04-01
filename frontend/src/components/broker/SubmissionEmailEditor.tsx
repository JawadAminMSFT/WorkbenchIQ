'use client';

import React, { useState, useEffect } from 'react';
import { Mail, Copy, Save, CheckCircle, Send } from 'lucide-react';
import type { SubmissionDocument } from '../../lib/broker-types';

interface EmailDraft {
  carrier: string;
  subject: string;
  body: string;
}

interface SubmissionEmailEditorProps {
  carriers: string[];
  clientName: string;
  lineOfBusiness: string;
  documents: SubmissionDocument[];
  submissionId?: string;
  onMarkSent?: () => void;
}

function generateDraftEmail(
  carrier: string,
  clientName: string,
  lob: string,
): EmailDraft {
  const lobLabel = lob
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
  return {
    carrier,
    subject: `Submission - ${clientName} - ${lobLabel}`,
    body: [
      `Dear ${carrier} Underwriting Team,`,
      '',
      `Please find attached a ${lob.replace(/_/g, ' ')} submission for our client ${clientName}.`,
      '',
      'This submission includes completed ACORD applications, schedule of values, and supporting loss run documentation for your review.',
      '',
      'We would appreciate a quote at your earliest convenience. Please do not hesitate to reach out with any questions.',
      '',
      'Best regards',
    ].join('\n'),
  };
}

export default function SubmissionEmailEditor({
  carriers,
  clientName,
  lineOfBusiness,
  documents,
  submissionId,
  onMarkSent,
}: SubmissionEmailEditorProps) {
  const [drafts, setDrafts] = useState<EmailDraft[]>([]);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);
  const [savedIdx, setSavedIdx] = useState<number | null>(null);
  const [markingSent, setMarkingSent] = useState(false);
  const [markedSent, setMarkedSent] = useState(false);

  useEffect(() => {
    setDrafts(
      carriers.map((c) => generateDraftEmail(c, clientName, lineOfBusiness)),
    );
  }, [carriers, clientName, lineOfBusiness]);

  const updateDraft = (
    idx: number,
    field: 'subject' | 'body',
    value: string,
  ) => {
    setDrafts((prev) =>
      prev.map((d, i) => (i === idx ? { ...d, [field]: value } : d)),
    );
  };

  const copyToClipboard = async (idx: number) => {
    const draft = drafts[idx];
    if (!draft) return;
    const text = `Subject: ${draft.subject}\n\n${draft.body}`;
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // Fallback
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
    }
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  const saveDraft = (idx: number) => {
    // Save is visual-only for now (email drafts live in component state)
    setSavedIdx(idx);
    setTimeout(() => setSavedIdx(null), 2000);
  };

  // Build attachment labels from uploaded documents
  const attachmentLabels: string[] = [];
  const typeLabels: Record<string, string> = {
    acord_125: 'ACORD 125',
    acord_140: 'ACORD 140',
    sov: 'SOV',
    loss_runs: 'Loss Runs',
    prior_declaration: 'Prior Declaration',
  };
  const seen = new Set<string>();
  documents?.forEach((d) => {
    const label = typeLabels[d.document_type] ?? d.file_name;
    if (!seen.has(label)) {
      seen.add(label);
      attachmentLabels.push(label);
    }
  });

  if (carriers.length === 0) {
    return (
      <div className="text-center py-8 text-slate-400">
        <p className="text-sm">
          Select carriers in Step 3 and generate a package to create email
          drafts.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {drafts.map((draft, idx) => (
        <div
          key={draft.carrier}
          className="border border-slate-200 rounded-lg overflow-hidden"
        >
          {/* Card header */}
          <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center gap-2">
            <Mail className="w-4 h-4 text-amber-600" />
            <h4 className="text-sm font-semibold text-slate-900">
              Draft Email — {draft.carrier}
            </h4>
          </div>

          <div className="p-4 space-y-3">
            {/* Subject */}
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Subject
              </label>
              <input
                type="text"
                value={draft.subject}
                onChange={(e) => updateDraft(idx, 'subject', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
            </div>

            {/* Body */}
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">
                Body
              </label>
              <textarea
                value={draft.body}
                onChange={(e) => updateDraft(idx, 'body', e.target.value)}
                rows={8}
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 resize-y font-mono"
              />
            </div>

            {/* Attachments */}
            {attachmentLabels.length > 0 && (
              <div>
                <span className="text-xs font-medium text-slate-500">
                  Attachments:{' '}
                </span>
                <span className="text-xs text-slate-700">
                  {attachmentLabels.join(', ')}
                </span>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3">
              <button
                onClick={() => saveDraft(idx)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
              >
                {savedIdx === idx ? (
                  <CheckCircle className="w-3.5 h-3.5 text-green-500" />
                ) : (
                  <Save className="w-3.5 h-3.5" />
                )}
                {savedIdx === idx ? 'Saved!' : 'Save Draft'}
              </button>
              <button
                onClick={() => copyToClipboard(idx)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium border border-slate-200 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
              >
                {copiedIdx === idx ? (
                  <CheckCircle className="w-3.5 h-3.5 text-green-500" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
                {copiedIdx === idx ? 'Copied!' : 'Copy to Clipboard'}
              </button>
            </div>
          </div>
        </div>
      ))}

      {/* Mark All as Sent */}
      {submissionId && (
        <div className="flex justify-end pt-2">
          <button
            onClick={async () => {
              if (markedSent || markingSent) return;
              setMarkingSent(true);
              try {
                const { markSubmissionSent } = await import('../../lib/broker-api');
                await markSubmissionSent(submissionId, carriers);
                setMarkedSent(true);
                onMarkSent?.();
              } catch (err) {
                console.error('Failed to mark as sent:', err);
              } finally {
                setMarkingSent(false);
              }
            }}
            disabled={markingSent || markedSent}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              markedSent
                ? 'bg-green-100 text-green-700 border border-green-200'
                : 'bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50'
            }`}
          >
            {markedSent ? (
              <CheckCircle className="w-4 h-4" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            {markedSent
              ? 'Marked as Sent'
              : markingSent
                ? 'Marking…'
                : 'Mark All as Sent'}
          </button>
        </div>
      )}
    </div>
  );
}
