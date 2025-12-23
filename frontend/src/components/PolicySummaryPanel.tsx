'use client';

import { useState } from 'react';
import { Shield, FileText, AlertTriangle, CheckCircle, Clock, Play, Loader2, Sparkles } from 'lucide-react';
import type { ApplicationMetadata, RiskFinding } from '@/lib/types';

interface PolicySummaryPanelProps {
  application: ApplicationMetadata;
  onViewFullReport: () => void;
  onRiskAnalysisComplete?: () => void;
}

function getRiskLevelInfo(rating: string): { icon: React.ReactNode; bgColor: string; textColor: string; borderColor: string; label: string } {
  const lowerRating = (rating || '').toLowerCase();
  if (lowerRating.includes('high')) {
    return {
      icon: <AlertTriangle className="w-5 h-5" />,
      bgColor: 'bg-rose-50',
      textColor: 'text-rose-700',
      borderColor: 'border-rose-200',
      label: 'High Risk',
    };
  }
  if (lowerRating.includes('moderate')) {
    return {
      icon: <Clock className="w-5 h-5" />,
      bgColor: 'bg-amber-50',
      textColor: 'text-amber-700',
      borderColor: 'border-amber-200',
      label: 'Moderate Risk',
    };
  }
  if (lowerRating.includes('low')) {
    return {
      icon: <CheckCircle className="w-5 h-5" />,
      bgColor: 'bg-emerald-50',
      textColor: 'text-emerald-700',
      borderColor: 'border-emerald-200',
      label: 'Low Risk',
    };
  }
  return {
    icon: <Shield className="w-5 h-5" />,
    bgColor: 'bg-slate-50',
    textColor: 'text-slate-600',
    borderColor: 'border-slate-200',
    label: 'Not Assessed',
  };
}

export default function PolicySummaryPanel({
  application,
  onViewFullReport,
  onRiskAnalysisComplete,
}: PolicySummaryPanelProps) {
  const [isRunningAnalysis, setIsRunningAnalysis] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const riskAnalysis = application.risk_analysis?.parsed;
  const hasRiskAnalysis = !!riskAnalysis;

  const handleRunRiskAnalysis = async () => {
    setIsRunningAnalysis(true);
    setError(null);

    try {
      const response = await fetch(`/api/applications/${application.id}/risk-analysis`, {
        method: 'POST',
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to run risk analysis');
      }

      // Trigger reload of application data
      if (onRiskAnalysisComplete) {
        onRiskAnalysisComplete();
      }
    } catch (err) {
      console.error('Risk analysis error:', err);
      setError(err instanceof Error ? err.message : 'Failed to run risk analysis');
    } finally {
      setIsRunningAnalysis(false);
    }
  };

  // If no risk analysis, show the "Run Risk Analysis" prompt
  if (!hasRiskAnalysis) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center text-indigo-600">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-900">
                Policy Risk Analysis
              </h2>
              <p className="text-sm text-slate-500">
                Run policy-based risk assessment
              </p>
            </div>
          </div>
        </div>

        <div className="px-6 py-6">
          <div className="text-center">
            <div className="w-16 h-16 rounded-full bg-indigo-100 flex items-center justify-center mx-auto mb-4">
              <FileText className="w-8 h-8 text-indigo-600" />
            </div>
            <h3 className="text-lg font-medium text-slate-900 mb-2">
              Risk Analysis Not Run
            </h3>
            <p className="text-sm text-slate-600 mb-6 max-w-sm mx-auto">
              Run a comprehensive policy-based risk analysis to evaluate this application against underwriting guidelines.
            </p>
            
            {error && (
              <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-lg text-sm text-rose-700">
                {error}
              </div>
            )}

            <button
              onClick={handleRunRiskAnalysis}
              disabled={isRunningAnalysis || application.status !== 'completed'}
              className="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isRunningAnalysis ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Running Analysis...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Run Risk Analysis
                </>
              )}
            </button>

            {application.status !== 'completed' && (
              <p className="text-xs text-slate-500 mt-3">
                Standard analysis must be completed first
              </p>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Risk analysis is available - show results
  const riskInfo = getRiskLevelInfo(riskAnalysis.overall_risk_level);
  const topFindings = (riskAnalysis.findings || []).slice(0, 3);
  const premium = riskAnalysis.premium_recommendation;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      {/* Header with Risk Rating */}
      <div className={`px-6 py-4 ${riskInfo.bgColor}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg ${riskInfo.bgColor} flex items-center justify-center ${riskInfo.textColor}`}>
              {riskInfo.icon}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-semibold text-slate-900">
                  Policy Risk Analysis
                </h2>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-600 border border-indigo-100">
                  <Sparkles className="w-3 h-3" />
                  AI Analysis
                </span>
              </div>
              <div className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${riskInfo.bgColor} ${riskInfo.textColor} border ${riskInfo.borderColor}`}>
                {riskAnalysis.overall_risk_level || 'Unknown'}
              </div>
            </div>
          </div>
          
          <div className="text-right">
            <div className="text-2xl font-bold text-slate-900">
              {(riskAnalysis.findings || []).length}
            </div>
            <div className="text-xs text-slate-500">Policy Findings</div>
          </div>
        </div>
      </div>

      {/* Overall Rationale */}
      {riskAnalysis.overall_rationale && (
        <div className="px-6 py-4 border-b border-slate-100">
          <div className="flex items-start gap-3">
            <Shield className="w-5 h-5 text-indigo-500 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm text-slate-700">
                {riskAnalysis.overall_rationale}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Premium Recommendation */}
      {premium && (
        <div className="px-6 py-4 border-b border-slate-100 bg-slate-50">
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
            Premium Recommendation
          </h3>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-600">Decision:</span>
              <span className={`font-medium ${
                premium.base_decision === 'Standard' ? 'text-emerald-600' :
                premium.base_decision === 'Rated' ? 'text-amber-600' :
                premium.base_decision === 'Decline' ? 'text-rose-600' :
                'text-slate-700'
              }`}>
                {premium.base_decision}
              </span>
            </div>
            {premium.loading_percentage && premium.loading_percentage !== '0%' && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-600">Loading:</span>
                <span className="font-medium text-amber-600">{premium.loading_percentage}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Top Findings */}
      <div className="px-6 py-4">
        <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
          Key Policy Findings
        </h3>
        
        {topFindings.length === 0 ? (
          <p className="text-sm text-slate-500 italic">
            No specific policy findings identified.
          </p>
        ) : (
          <div className="space-y-3">
            {topFindings.map((finding: RiskFinding, idx: number) => (
              <div
                key={idx}
                className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg"
              >
                <FileText className="w-4 h-4 text-indigo-500 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono text-xs bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded">
                      {finding.policy_id}
                    </span>
                    <span className="text-sm font-medium text-slate-700">
                      {finding.policy_name}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 mt-1 line-clamp-2">
                    {finding.finding}
                  </p>
                </div>
                <span className={`text-xs font-medium flex-shrink-0 px-2 py-0.5 rounded ${
                  finding.risk_level?.toLowerCase().includes('high')
                    ? 'bg-rose-100 text-rose-700'
                    : finding.risk_level?.toLowerCase().includes('moderate')
                    ? 'bg-amber-100 text-amber-700'
                    : 'bg-emerald-100 text-emerald-700'
                }`}>
                  {finding.risk_level}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex items-center gap-3">
        <button
          onClick={onViewFullReport}
          className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <FileText className="w-4 h-4" />
          View Full Report
        </button>
        <button
          onClick={handleRunRiskAnalysis}
          disabled={isRunningAnalysis}
          className="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50"
          title="Re-run risk analysis"
        >
          {isRunningAnalysis ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Play className="w-4 h-4" />
          )}
        </button>
      </div>
    </div>
  );
}
