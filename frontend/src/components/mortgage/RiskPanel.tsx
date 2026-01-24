/**
 * Risk Panel Component
 * 
 * Right column showing:
 * - Risk tier with contributors
 * - Risk signals
 * - AI narrative draft
 * - Decision factors
 */

'use client';

import React, { useState } from 'react';
import {
  AlertTriangle, CheckCircle, XCircle, TrendingUp, TrendingDown,
  Sparkles, Shield, Edit2, Copy, RefreshCw, Info, AlertCircle, FileText
} from 'lucide-react';
import type { RiskSignal, MortgageFinding } from './MortgageWorkbench';
import ConfidenceIndicator from '../ConfidenceIndicator';

interface RiskPanelProps {
  riskSignals: RiskSignal[];
  decision: 'APPROVE' | 'DECLINE' | 'REFER';
  findings: MortgageFinding[];
  narrative?: string;
  policyChecksCount?: number;
}

export default function RiskPanel({
  riskSignals,
  decision,
  findings,
  narrative,
  policyChecksCount = 0,
}: RiskPanelProps) {
  const [isEditingNarrative, setIsEditingNarrative] = useState(false);
  const [narrativeText, setNarrativeText] = useState(narrative || generateDefaultNarrative(decision, findings, policyChecksCount));

  // Helper to get severity from finding (handles both old and new format)
  const getSeverity = (f: MortgageFinding): 'pass' | 'warning' | 'fail' | 'info' => {
    if (f.severity) return f.severity;
    // Map type to severity
    switch (f.type) {
      case 'success': return 'pass';
      case 'warning': return 'warning';
      case 'error':
      case 'fail': return 'fail';
      case 'condition':
      case 'info':
      default: return 'info';
    }
  };

  // Calculate risk score based on findings
  const calculateRiskScore = (): number => {
    const failCount = findings.filter(f => getSeverity(f) === 'fail').length;
    const warningCount = findings.filter(f => getSeverity(f) === 'warning').length;
    return Math.min(100, failCount * 30 + warningCount * 10);
  };

  const riskScore = calculateRiskScore();
  const riskLevel = riskScore < 25 ? 'low' : riskScore < 50 ? 'medium' : 'high';

  const getRiskLevelColor = () => {
    switch (riskLevel) {
      case 'low':
        return 'text-green-600 bg-green-100';
      case 'medium':
        return 'text-amber-600 bg-amber-100';
      case 'high':
        return 'text-red-600 bg-red-100';
    }
  };

  const getRiskLevelBg = () => {
    switch (riskLevel) {
      case 'low':
        return 'from-green-500 to-emerald-500';
      case 'medium':
        return 'from-amber-500 to-orange-500';
      case 'high':
        return 'from-red-500 to-rose-500';
    }
  };

  // Get key decision factors
  const getDecisionFactors = () => {
    const factors: string[] = [];
    const passFindings = findings.filter(f => getSeverity(f) === 'pass');
    const failFindings = findings.filter(f => getSeverity(f) === 'fail');

    passFindings.slice(0, 3).forEach(f => {
      factors.push(`✓ ${f.message}`);
    });

    failFindings.forEach(f => {
      factors.push(`✗ ${f.message}`);
    });

    return factors;
  };

  // What would change the decision
  const getChangeFactors = () => {
    if (decision === 'APPROVE') {
      return [];
    }
    
    const factors: string[] = [];
    const failFindings = findings.filter(f => getSeverity(f) === 'fail');
    
    failFindings.forEach(f => {
      if (f.category === 'ratio' && f.evidence?.calculated_value && f.evidence?.limit) {
        const diff = f.evidence.calculated_value - f.evidence.limit;
        if (f.rule_id?.includes('GDS')) {
          factors.push(`Reduce housing costs or increase income to lower GDS by ${(diff * 100).toFixed(1)}%`);
        } else if (f.rule_id?.includes('TDS')) {
          factors.push(`Pay down other debts to lower TDS by ${(diff * 100).toFixed(1)}%`);
        }
      }
    });

    if (factors.length === 0) {
      factors.push('Provide additional documentation to verify income');
      factors.push('Consider a co-signer with stronger credit profile');
    }

    return factors;
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-slate-200">
        <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">
          Risk Assessment
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Risk Tier */}
        <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm font-medium text-slate-700">Risk Score</span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskLevelColor()}`}>
                {riskLevel.toUpperCase()}
              </span>
            </div>
            
            {/* Risk Score Bar */}
            <div className="relative h-3 bg-slate-100 rounded-full overflow-hidden mb-2">
              <div
                className={`absolute left-0 top-0 h-full rounded-full bg-gradient-to-r ${getRiskLevelBg()} transition-all duration-500`}
                style={{ width: `${riskScore}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-slate-500">
              <span>Low Risk</span>
              <span>High Risk</span>
            </div>
          </div>

          {/* Top Contributors */}
          <div className="px-4 pb-4">
            <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">
              Top Contributors
            </h4>
            <div className="space-y-3">
              {findings
                .filter(f => getSeverity(f) === 'fail' || getSeverity(f) === 'warning')
                .slice(0, 3)
                .map((finding, idx) => (
                  <div key={idx} className="space-y-1">
                    <div
                      className={`flex items-center gap-2 text-sm ${
                        getSeverity(finding) === 'fail' ? 'text-red-600' : 'text-amber-600'
                      }`}
                    >
                      {getSeverity(finding) === 'fail' ? (
                        <XCircle className="w-4 h-4 flex-shrink-0" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                      )}
                      <span className="flex-1">{finding.category || finding.type}: {finding.rule_id || finding.message}</span>
                      {finding.confidence !== undefined && (
                        <ConfidenceIndicator 
                          confidence={finding.confidence} 
                          fieldName={finding.category}
                        />
                      )}
                    </div>
                    {/* Source documents */}
                    {(finding.sources || finding.source_file) && (
                      <div className="ml-6 flex items-center gap-1 text-xs text-slate-500">
                        <FileText className="w-3 h-3" />
                        <span>
                          {finding.sources 
                            ? finding.sources.join(', ')
                            : finding.source_file
                          }
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              {findings.filter(f => getSeverity(f) === 'fail' || getSeverity(f) === 'warning').length === 0 && (
                <div className="flex items-center gap-2 text-sm text-green-600">
                  <CheckCircle className="w-4 h-4" />
                  <span>No significant risk factors identified</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Risk Signals */}
        {riskSignals.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-slate-900 mb-3">Risk Signals</h3>
            <div className="space-y-2">
              {riskSignals.map((signal) => (
                <RiskSignalCard key={signal.id} signal={signal} />
              ))}
            </div>
          </div>
        )}

        {/* AI Narrative */}
        <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
          <div className="px-4 py-3 bg-gradient-to-r from-purple-50 to-blue-50 border-b border-slate-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-600" />
              <span className="text-sm font-medium text-slate-900">AI Underwriting Note</span>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setIsEditingNarrative(!isEditingNarrative)}
                className="p-1.5 hover:bg-white rounded text-slate-500 hover:text-slate-700"
                title="Edit"
              >
                <Edit2 className="w-4 h-4" />
              </button>
              <button
                onClick={() => navigator.clipboard.writeText(narrativeText)}
                className="p-1.5 hover:bg-white rounded text-slate-500 hover:text-slate-700"
                title="Copy"
              >
                <Copy className="w-4 h-4" />
              </button>
            </div>
          </div>
          <div className="p-4">
            {isEditingNarrative ? (
              <textarea
                value={narrativeText}
                onChange={(e) => setNarrativeText(e.target.value)}
                className="w-full h-40 text-sm text-slate-700 border border-slate-200 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            ) : (
              <div className="text-sm text-slate-700 space-y-2">
                {narrativeText.split('\n').map((line, idx) => {
                  // Handle bold text with **
                  const renderLine = (text: string) => {
                    const parts = text.split(/\*\*([^*]+)\*\*/g);
                    return parts.map((part, i) => 
                      i % 2 === 1 ? <strong key={i} className="font-semibold">{part}</strong> : part
                    );
                  };
                  
                  if (line.startsWith('• ')) {
                    return <div key={idx} className="flex items-start gap-2 ml-2">
                      <span className="text-emerald-600">•</span>
                      <span>{renderLine(line.substring(2))}</span>
                    </div>;
                  }
                  if (line.trim() === '') {
                    return <div key={idx} className="h-2" />;
                  }
                  return <p key={idx}>{renderLine(line)}</p>;
                })}
              </div>
            )}
          </div>
        </div>

        {/* Key Decision Factors */}
        <div>
          <h3 className="text-sm font-medium text-slate-900 mb-3">Key Decision Factors</h3>
          <div className="space-y-2">
            {getDecisionFactors().map((factor, idx) => (
              <div
                key={idx}
                className={`text-sm ${
                  factor.startsWith('✓') ? 'text-green-700' : 'text-red-700'
                }`}
              >
                {factor}
              </div>
            ))}
          </div>
        </div>

        {/* What Would Change Decision */}
        {decision !== 'APPROVE' && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start gap-2">
              <Info className="w-5 h-5 text-blue-600 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-blue-900">
                  What would change the decision?
                </h4>
                <ul className="mt-2 space-y-1">
                  {getChangeFactors().map((factor, idx) => (
                    <li key={idx} className="text-sm text-blue-700">• {factor}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Risk Signal Card
function RiskSignalCard({ signal }: { signal: RiskSignal }) {
  const getSeverityColor = () => {
    switch (signal.severity) {
      case 'low':
        return 'border-blue-200 bg-blue-50';
      case 'medium':
        return 'border-amber-200 bg-amber-50';
      case 'high':
        return 'border-red-200 bg-red-50';
    }
  };

  const getSeverityIcon = () => {
    switch (signal.severity) {
      case 'low':
        return <Info className="w-4 h-4 text-blue-500" />;
      case 'medium':
        return <AlertTriangle className="w-4 h-4 text-amber-500" />;
      case 'high':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
    }
  };

  return (
    <div className={`rounded-lg border p-3 ${getSeverityColor()}`}>
      <div className="flex items-start gap-2">
        {getSeverityIcon()}
        <div className="flex-1">
          <h4 className="text-sm font-medium text-slate-900">{signal.title}</h4>
          <p className="text-xs text-slate-600 mt-1">{signal.description}</p>
          {signal.source_documents && signal.source_documents.length > 0 && (
            <div className="flex gap-1 mt-2">
              {signal.source_documents.map((doc, idx) => (
                <span
                  key={idx}
                  className="text-xs px-2 py-0.5 bg-white rounded-full text-slate-500"
                >
                  {doc}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Helper to get severity from finding (handles both old and new format)
function getDefaultSeverity(f: MortgageFinding): 'pass' | 'warning' | 'fail' | 'info' {
  if (f.severity) return f.severity;
  switch (f.type) {
    case 'success': return 'pass';
    case 'warning': return 'warning';
    case 'error':
    case 'fail': return 'fail';
    case 'condition':
    case 'info':
    default: return 'info';
  }
}

// Generate default narrative based on decision and findings
function generateDefaultNarrative(
  decision: 'APPROVE' | 'DECLINE' | 'REFER',
  findings: MortgageFinding[],
  policyChecksCount: number = 6
): string {
  const passCount = policyChecksCount || findings.filter(f => getDefaultSeverity(f) === 'pass').length;
  const failCount = findings.filter(f => getDefaultSeverity(f) === 'fail').length;

  if (decision === 'APPROVE') {
    return `Application meets all OSFI B-20 underwriting requirements.

Key observations:
• All ${passCount} policy checks passed
• Debt service ratios are within acceptable limits
• Income and employment verification complete
• Property valuation supports the loan amount
• Credit profile meets minimum requirements

Recommendation: APPROVE for funding subject to standard conditions.`;
  }

  if (decision === 'DECLINE') {
    return `Application does not meet OSFI B-20 underwriting requirements.

Issues identified:
• ${failCount} policy check(s) failed
${findings
  .filter(f => getDefaultSeverity(f) === 'fail')
  .map(f => `• ${f.message}`)
  .join('\n')}

Recommendation: DECLINE - borrower does not qualify under current parameters.`;
  }

  return `Application requires additional review before final decision.

The application has aspects that need senior underwriter attention:
${findings
  .filter(f => getDefaultSeverity(f) === 'fail' || getDefaultSeverity(f) === 'warning')
  .map(f => `• ${f.message}`)
  .join('\n')}

Recommendation: REFER for senior review or exception approval.`;
}
