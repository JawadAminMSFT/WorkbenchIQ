'use client';

import { User } from 'lucide-react';
import type { ApplicationMetadata, PolicyCitation } from '@/lib/types';
import RiskRatingPopover from './RiskRatingPopover';

interface PatientSummaryProps {
  application: ApplicationMetadata;
  onPolicyClick?: (policyId: string) => void;
}

export default function PatientSummary({ application, onPolicyClick }: PatientSummaryProps) {
  // Get summary from LLM outputs
  const customerProfile = application.llm_outputs?.application_summary?.customer_profile?.parsed as any;
  const summary = customerProfile?.summary || customerProfile?.medical_summary || null;
  const riskAssessment = customerProfile?.risk_assessment || null;
  const policyCitations: PolicyCitation[] = customerProfile?.policy_citations || [];
  const underwritingAction = customerProfile?.underwriting_action || null;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center">
            <User className="w-5 h-5 text-indigo-600" />
          </div>
          <h2 className="text-lg font-semibold text-slate-900">Patient Summary</h2>
        </div>

        {/* Risk Badge with Popover */}
        {riskAssessment && (
          <RiskRatingPopover
            rating={riskAssessment}
            rationale={summary}
            citations={policyCitations}
            onPolicyClick={onPolicyClick}
          />
        )}
      </div>

      {/* Summary Text */}
      {summary ? (
        <div className="space-y-4">
          <p className="text-sm text-slate-700 leading-relaxed">
            {summary}
          </p>
          
          {underwritingAction && (
            <div className="pt-3 border-t border-slate-100">
              <h4 className="text-xs font-medium text-slate-500 uppercase mb-1">
                Recommended Action
              </h4>
              <p className="text-sm text-slate-700">{underwritingAction}</p>
            </div>
          )}
        </div>
      ) : (
        <p className="text-sm text-slate-500 italic">
          No summary available. Run analysis to generate patient summary.
        </p>
      )}
    </div>
  );
}
