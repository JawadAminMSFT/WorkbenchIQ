'use client';

import { useState, useEffect, useRef } from 'react';
import { X, FileText, Download, RefreshCw, Shield, AlertTriangle, CheckCircle, Clock, Play, Loader2 } from 'lucide-react';
import type { ApplicationMetadata, RiskFinding, RiskAnalysisResult } from '@/lib/types';

interface PolicyReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  application: ApplicationMetadata;
  onRerunAnalysis?: () => Promise<void>;
}

function getRatingBadge(rating: string) {
  const lowerRating = (rating || '').toLowerCase();
  if (lowerRating.includes('high')) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-rose-100 text-rose-700 rounded-full text-xs font-medium">
        <AlertTriangle className="w-3 h-3" />
        High Risk
      </span>
    );
  }
  if (lowerRating.includes('moderate')) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full text-xs font-medium">
        <Clock className="w-3 h-3" />
        Moderate Risk
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-emerald-100 text-emerald-700 rounded-full text-xs font-medium">
      <CheckCircle className="w-3 h-3" />
      Low Risk
    </span>
  );
}

export default function PolicyReportModal({
  isOpen,
  onClose,
  application,
  onRerunAnalysis,
}: PolicyReportModalProps) {
  const [isRerunning, setIsRerunning] = useState(false);
  const [isRunningRiskAnalysis, setIsRunningRiskAnalysis] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const modalRef = useRef<HTMLDivElement>(null);
  
  const riskAnalysis = application.risk_analysis?.parsed as RiskAnalysisResult | undefined;
  const hasRiskAnalysis = !!riskAnalysis;
  const findings = riskAnalysis?.findings || [];
  const overallRating = riskAnalysis?.overall_risk_level || 'Not Assessed';

  // Close on escape
  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        onClose();
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen, onClose]);

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (modalRef.current && !modalRef.current.contains(event.target as Node)) {
        onClose();
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen, onClose]);

  async function handleRerun() {
    if (onRerunAnalysis) {
      setIsRerunning(true);
      try {
        await onRerunAnalysis();
      } finally {
        setIsRerunning(false);
      }
    }
  }

  async function handleRunRiskAnalysis() {
    setIsRunningRiskAnalysis(true);
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
      if (onRerunAnalysis) {
        await onRerunAnalysis();
      }
    } catch (err) {
      console.error('Risk analysis error:', err);
      setError(err instanceof Error ? err.message : 'Failed to run risk analysis');
    } finally {
      setIsRunningRiskAnalysis(false);
    }
  }

  function handleExportPDF() {
    const printContent = generatePrintableReport();
    const printWindow = window.open('', '_blank');
    if (printWindow) {
      printWindow.document.write(printContent);
      printWindow.document.close();
      printWindow.print();
    }
  }

  function generatePrintableReport(): string {
    const customerProfile = application.llm_outputs?.application_summary?.customer_profile?.parsed;
    const patientName = customerProfile?.full_name || customerProfile?.summary?.split('.')[0] || 'Unknown Patient';
    const dateGenerated = new Date().toLocaleDateString();
    const premium = riskAnalysis?.premium_recommendation;

    return `
      <!DOCTYPE html>
      <html>
        <head>
          <title>Underwriting Policy Report - ${patientName}</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 40px; color: #333; }
            h1 { color: #1e293b; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
            h2 { color: #475569; margin-top: 30px; }
            .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
            .rating { font-size: 18px; font-weight: bold; padding: 8px 16px; border-radius: 8px; }
            .rating.high { background: #fee2e2; color: #b91c1c; }
            .rating.moderate { background: #fef3c7; color: #b45309; }
            .rating.low { background: #d1fae5; color: #047857; }
            .finding { margin: 15px 0; padding: 15px; background: #f8fafc; border-radius: 8px; border-left: 4px solid #6366f1; }
            .policy-id { font-family: monospace; background: #e0e7ff; padding: 2px 6px; border-radius: 4px; color: #4338ca; }
            .summary-box { padding: 20px; background: #f1f5f9; border-radius: 8px; margin: 20px 0; }
            .premium-box { padding: 20px; background: #fef3c7; border-radius: 8px; margin: 20px 0; }
            .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; color: #64748b; font-size: 12px; }
            @media print { body { margin: 20px; } }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>Underwriting Policy Report</h1>
            <div class="rating ${overallRating.toLowerCase()}">${overallRating}</div>
          </div>
          
          <p><strong>Patient:</strong> ${patientName}</p>
          <p><strong>Application ID:</strong> ${application.id}</p>
          <p><strong>Date Generated:</strong> ${dateGenerated}</p>
          
          ${riskAnalysis?.overall_rationale ? `
          <div class="summary-box">
            <h3>Overall Assessment</h3>
            <p>${riskAnalysis.overall_rationale}</p>
          </div>
          ` : ''}
          
          ${premium ? `
          <div class="premium-box">
            <h3>Premium Recommendation</h3>
            <p><strong>Decision:</strong> ${premium.base_decision}</p>
            ${premium.loading_percentage && premium.loading_percentage !== '0%' ? `<p><strong>Loading:</strong> ${premium.loading_percentage}</p>` : ''}
            ${premium.exclusions?.length ? `<p><strong>Exclusions:</strong> ${premium.exclusions.join(', ')}</p>` : ''}
            ${premium.conditions?.length ? `<p><strong>Conditions:</strong> ${premium.conditions.join(', ')}</p>` : ''}
          </div>
          ` : ''}
          
          <h2>Policy Findings (${findings.length})</h2>
          ${findings.length === 0 ? '<p>No policy findings recorded.</p>' : ''}
          ${findings.map((f: RiskFinding) => `
            <div class="finding">
              <div><span class="policy-id">${f.policy_id}</span> ${f.policy_name}</div>
              <p><strong>Category:</strong> ${f.category}</p>
              <p><strong>Finding:</strong> ${f.finding}</p>
              <p><strong>Risk Level:</strong> ${f.risk_level}</p>
              <p><strong>Action:</strong> ${f.action}</p>
              ${f.rationale ? `<p><strong>Rationale:</strong> ${f.rationale}</p>` : ''}
            </div>
          `).join('')}
          
          ${riskAnalysis?.underwriting_action ? `
          <h2>Recommended Action</h2>
          <p>${riskAnalysis.underwriting_action}</p>
          ` : ''}
          
          ${riskAnalysis?.data_gaps?.length ? `
          <h2>Data Gaps</h2>
          <ul>
            ${riskAnalysis.data_gaps.map((gap: string) => `<li>${gap}</li>`).join('')}
          </ul>
          ` : ''}
          
          <div class="footer">
            <p>This report was generated automatically by the Underwriting Assistant. Please review all findings before making final decisions.</p>
          </div>
        </body>
      </html>
    `;
  }

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div
        ref={modalRef}
        className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col"
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-indigo-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-900">
                Policy Risk Analysis Report
              </h2>
              <p className="text-sm text-slate-500">
                Application {application.id.substring(0, 8)}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {!hasRiskAnalysis ? (
            // No risk analysis - show prompt to run
            <div className="text-center py-12">
              <div className="w-20 h-20 rounded-full bg-indigo-100 flex items-center justify-center mx-auto mb-6">
                <FileText className="w-10 h-10 text-indigo-600" />
              </div>
              <h3 className="text-xl font-medium text-slate-900 mb-2">
                Risk Analysis Not Run
              </h3>
              <p className="text-slate-600 mb-6 max-w-md mx-auto">
                Run a comprehensive policy-based risk analysis to evaluate this application against underwriting guidelines and generate a detailed report.
              </p>
              
              {error && (
                <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-lg text-sm text-rose-700 max-w-md mx-auto">
                  {error}
                </div>
              )}

              <button
                onClick={handleRunRiskAnalysis}
                disabled={isRunningRiskAnalysis || application.status !== 'completed'}
                className="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isRunningRiskAnalysis ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Running Analysis...
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5" />
                    Run Risk Analysis
                  </>
                )}
              </button>

              {application.status !== 'completed' && (
                <p className="text-sm text-slate-500 mt-4">
                  Standard analysis must be completed first
                </p>
              )}
            </div>
          ) : (
            // Show risk analysis results
            <>
              {/* Overall Assessment */}
              <div className="mb-6 p-4 bg-slate-50 rounded-lg">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-sm font-medium text-slate-500 uppercase">
                      Overall Risk Assessment
                    </h3>
                    <div className="mt-2">
                      {getRatingBadge(overallRating)}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-slate-900">
                      {findings.length}
                    </div>
                    <div className="text-sm text-slate-500">
                      Policy Findings
                    </div>
                  </div>
                </div>
                
                {riskAnalysis.overall_rationale && (
                  <p className="text-sm text-slate-700 mt-3 pt-3 border-t border-slate-200">
                    {riskAnalysis.overall_rationale}
                  </p>
                )}
              </div>

              {/* Premium Recommendation */}
              {riskAnalysis.premium_recommendation && (
                <div className="mb-6 p-4 bg-amber-50 rounded-lg border border-amber-200">
                  <h3 className="text-sm font-semibold text-amber-800 uppercase tracking-wide mb-3">
                    Premium Recommendation
                  </h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-amber-700">Decision:</span>
                      <span className="ml-2 font-medium text-amber-900">
                        {riskAnalysis.premium_recommendation.base_decision}
                      </span>
                    </div>
                    {riskAnalysis.premium_recommendation.loading_percentage && 
                     riskAnalysis.premium_recommendation.loading_percentage !== '0%' && (
                      <div>
                        <span className="text-amber-700">Loading:</span>
                        <span className="ml-2 font-medium text-amber-900">
                          {riskAnalysis.premium_recommendation.loading_percentage}
                        </span>
                      </div>
                    )}
                  </div>
                  {riskAnalysis.premium_recommendation.exclusions && riskAnalysis.premium_recommendation.exclusions.length > 0 && (
                    <div className="mt-2 text-sm">
                      <span className="text-amber-700">Exclusions:</span>
                      <span className="ml-2 text-amber-900">
                        {riskAnalysis.premium_recommendation.exclusions.join(', ')}
                      </span>
                    </div>
                  )}
                </div>
              )}

              {/* Policy Findings */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
                  Policy Findings
                </h3>
                
                {findings.length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No specific policy findings identified.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {findings.map((finding: RiskFinding, idx: number) => (
                      <div
                        key={idx}
                        className="p-4 bg-white border border-slate-200 rounded-lg hover:border-indigo-300 transition-colors"
                      >
                        <div className="flex items-start gap-3">
                          <FileText className="w-5 h-5 text-indigo-500 mt-0.5 flex-shrink-0" />
                          <div className="flex-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-mono text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded">
                                {finding.policy_id}
                              </span>
                              <span className="font-medium text-slate-800">
                                {finding.policy_name}
                              </span>
                              <span className={`text-xs px-2 py-0.5 rounded ${
                                finding.risk_level?.toLowerCase().includes('high')
                                  ? 'bg-rose-100 text-rose-700'
                                  : finding.risk_level?.toLowerCase().includes('moderate')
                                  ? 'bg-amber-100 text-amber-700'
                                  : 'bg-emerald-100 text-emerald-700'
                              }`}>
                                {finding.risk_level}
                              </span>
                            </div>
                            
                            <p className="mt-2 text-sm text-slate-600">
                              {finding.finding}
                            </p>
                            
                            <div className="mt-3 text-sm text-slate-500">
                              <span className="font-medium">Action:</span> {finding.action}
                            </div>
                            
                            {finding.rationale && (
                              <div className="mt-1 text-sm text-slate-500">
                                <span className="font-medium">Rationale:</span> {finding.rationale}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Underwriting Action */}
              {riskAnalysis.underwriting_action && (
                <div className="mt-6 p-4 bg-indigo-50 rounded-lg border border-indigo-200">
                  <h3 className="text-sm font-semibold text-indigo-800 uppercase tracking-wide mb-2">
                    Recommended Action
                  </h3>
                  <p className="text-sm text-indigo-900">
                    {riskAnalysis.underwriting_action}
                  </p>
                </div>
              )}

              {/* Data Gaps */}
              {riskAnalysis.data_gaps && riskAnalysis.data_gaps.length > 0 && (
                <div className="mt-6 p-4 bg-slate-50 rounded-lg">
                  <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-2">
                    Data Gaps
                  </h3>
                  <ul className="list-disc list-inside text-sm text-slate-600 space-y-1">
                    {riskAnalysis.data_gaps.map((gap: string, idx: number) => (
                      <li key={idx}>{gap}</li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="text-sm text-slate-500">
            {application.risk_analysis?.timestamp 
              ? `Last analyzed: ${new Date(application.risk_analysis.timestamp).toLocaleString()}`
              : 'Not yet analyzed'}
          </div>
          <div className="flex items-center gap-3">
            {hasRiskAnalysis && (
              <>
                <button
                  onClick={handleRunRiskAnalysis}
                  disabled={isRunningRiskAnalysis}
                  className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 transition-colors"
                >
                  {isRunningRiskAnalysis ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <RefreshCw className="w-4 h-4" />
                  )}
                  Re-run
                </button>
                <button
                  onClick={handleExportPDF}
                  className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  <Download className="w-4 h-4" />
                  Export PDF
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
