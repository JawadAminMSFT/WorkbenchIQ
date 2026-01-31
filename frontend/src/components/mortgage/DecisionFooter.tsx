/**
 * Decision Footer Component
 * 
 * Bottom bar with:
 * - Decision notes input
 * - Action buttons (Approve, Refer, Decline)
 * - Conditions summary
 */

'use client';

import React from 'react';
import {
  CheckCircle, XCircle, AlertTriangle, Send, MessageSquare,
  Lock, Unlock
} from 'lucide-react';
import type { MortgageFinding } from './MortgageWorkbench';

interface DecisionFooterProps {
  decision: 'APPROVE' | 'DECLINE' | 'REFER';
  decisionNotes: string;
  onNotesChange: (notes: string) => void;
  onApprove: () => void;
  onDecline: () => void;
  onRefer: () => void;
  findings: MortgageFinding[];
}

export default function DecisionFooter({
  decision,
  decisionNotes,
  onNotesChange,
  onApprove,
  onDecline,
  onRefer,
  findings,
}: DecisionFooterProps) {
  const hasBlockingIssues = findings.some(f => f.severity === 'fail');
  const hasWarnings = findings.some(f => f.severity === 'warning');
  const conditionsCount = findings.filter(f => f.severity === 'fail' || f.severity === 'warning').length;

  return (
    <div className="bg-white border-t border-slate-200 px-6 py-4">
      <div className="flex items-center gap-6">
        {/* Decision Notes */}
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <MessageSquare className="w-4 h-4 text-slate-400" />
            <span className="text-sm font-medium text-slate-700">Decision Notes</span>
          </div>
          <textarea
            value={decisionNotes}
            onChange={(e) => onNotesChange(e.target.value)}
            placeholder="Add notes for the decision audit trail..."
            className="w-full h-16 px-3 py-2 text-sm border border-slate-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
        </div>

        {/* Conditions Summary */}
        {conditionsCount > 0 && (
          <div className="w-48">
            <div className="text-sm text-slate-500 mb-1">Conditions</div>
            <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
              hasBlockingIssues ? 'bg-red-50 text-red-700' : 'bg-amber-50 text-amber-700'
            }`}>
              {hasBlockingIssues ? (
                <Lock className="w-4 h-4" />
              ) : (
                <Unlock className="w-4 h-4" />
              )}
              <span className="text-sm font-medium">
                {conditionsCount} {conditionsCount === 1 ? 'condition' : 'conditions'} required
              </span>
            </div>
          </div>
        )}

        {/* Decision Buttons */}
        <div className="flex items-center gap-3">
          <button
            onClick={onDecline}
            className="flex items-center gap-2 px-5 py-2.5 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 transition-colors font-medium"
          >
            <XCircle className="w-5 h-5" />
            Decline
          </button>

          <button
            onClick={onRefer}
            className="flex items-center gap-2 px-5 py-2.5 bg-amber-50 text-amber-700 rounded-lg hover:bg-amber-100 transition-colors font-medium"
          >
            <AlertTriangle className="w-5 h-5" />
            Refer
          </button>

          <button
            onClick={onApprove}
            disabled={hasBlockingIssues}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-lg font-medium transition-colors ${
              hasBlockingIssues
                ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                : 'bg-emerald-600 text-white hover:bg-emerald-700'
            }`}
            title={hasBlockingIssues ? 'Cannot approve: blocking issues exist' : 'Approve application'}
          >
            <CheckCircle className="w-5 h-5" />
            Approve
          </button>
        </div>
      </div>

      {/* Blocking Issues Warning */}
      {hasBlockingIssues && (
        <div className="mt-3 flex items-center gap-2 text-sm text-red-600">
          <AlertTriangle className="w-4 h-4" />
          <span>
            Application has {findings.filter(f => f.severity === 'fail').length} blocking issue(s) 
            that must be resolved before approval
          </span>
        </div>
      )}
    </div>
  );
}
