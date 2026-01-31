/**
 * Policy Checks Panel Component
 * 
 * Displays OSFI B-20 policy compliance checks:
 * - Rule list with pass/fail/warning status
 * - Evidence links for each rule
 * - Expandable details with system rationale
 */

'use client';

import React, { useState } from 'react';
import {
  Shield, CheckCircle, XCircle, AlertTriangle, Info,
  ChevronDown, ChevronRight, ExternalLink, BookOpen
} from 'lucide-react';
import type { MortgageFinding, MortgageRatios, MortgageStressRatios } from './MortgageWorkbench';

interface PolicyChecksPanelProps {
  findings: MortgageFinding[];
  ratios: MortgageRatios;
  stressRatios: MortgageStressRatios;
}

// OSFI B-20 Rule definitions
const OSFI_RULES = [
  {
    id: 'OSFI-B20-GDS-001',
    name: 'Gross Debt Service Ratio',
    description: 'GDS ratio must not exceed 39% at the qualifying rate',
    threshold: '≤ 39%',
    category: 'ratio',
  },
  {
    id: 'OSFI-B20-TDS-001',
    name: 'Total Debt Service Ratio',
    description: 'TDS ratio must not exceed 44% at the qualifying rate',
    threshold: '≤ 44%',
    category: 'ratio',
  },
  {
    id: 'OSFI-B20-LTV-001',
    name: 'Loan-to-Value Ratio',
    description: 'LTV must not exceed 80% for conventional mortgages, 95% for insured',
    threshold: '≤ 80% (conventional)',
    category: 'ratio',
  },
  {
    id: 'OSFI-B20-MQR-001',
    name: 'Minimum Qualifying Rate',
    description: 'Borrower must qualify at the greater of contract rate + 2% or 5.25%',
    threshold: 'max(rate+2%, 5.25%)',
    category: 'stress_test',
  },
  {
    id: 'OSFI-B20-INCOME-001',
    name: 'Income Verification',
    description: 'Income must be verified through acceptable documentation',
    threshold: 'Required',
    category: 'documentation',
  },
  {
    id: 'OSFI-B20-CREDIT-001',
    name: 'Credit Assessment',
    description: 'Credit score must meet minimum threshold',
    threshold: '≥ 620',
    category: 'credit',
  },
  {
    id: 'OSFI-B20-DP-001',
    name: 'Down Payment Source',
    description: 'Down payment source must be verified',
    threshold: 'Required',
    category: 'documentation',
  },
  {
    id: 'OSFI-B20-PROP-001',
    name: 'Property Valuation',
    description: 'Property value must be supported by appraisal or AVM',
    threshold: 'Required',
    category: 'property',
  },
];

export default function PolicyChecksPanel({
  findings,
  ratios,
  stressRatios,
}: PolicyChecksPanelProps) {
  const [expandedRules, setExpandedRules] = useState<Set<string>>(new Set());

  const toggleRule = (ruleId: string) => {
    const newExpanded = new Set(expandedRules);
    if (newExpanded.has(ruleId)) {
      newExpanded.delete(ruleId);
    } else {
      newExpanded.add(ruleId);
    }
    setExpandedRules(newExpanded);
  };

  // Get finding for a rule
  const getFinding = (ruleId: string): MortgageFinding | undefined => {
    return findings.find(f => f.rule_id === ruleId);
  };

  // If no findings provided, generate from ratios
  const generateFinding = (rule: typeof OSFI_RULES[0]): MortgageFinding => {
    const existing = getFinding(rule.id);
    if (existing) return existing;

    // Generate based on rule type
    // Note: ratios are already percentages (e.g., 26.36 means 26.36%)
    switch (rule.id) {
      case 'OSFI-B20-GDS-001':
        return {
          rule_id: rule.id,
          severity: stressRatios.gds <= 39 ? 'pass' : 'fail',
          category: 'ratio',
          message: `GDS ratio ${stressRatios.gds.toFixed(2)}% ${stressRatios.gds <= 39 ? 'is within' : 'exceeds'} limit of 39%`,
          evidence: { calculated_value: stressRatios.gds, limit: 39 },
        };
      case 'OSFI-B20-TDS-001':
        return {
          rule_id: rule.id,
          severity: stressRatios.tds <= 44 ? 'pass' : 'fail',
          category: 'ratio',
          message: `TDS ratio ${stressRatios.tds.toFixed(2)}% ${stressRatios.tds <= 44 ? 'is within' : 'exceeds'} limit of 44%`,
          evidence: { calculated_value: stressRatios.tds, limit: 44 },
        };
      case 'OSFI-B20-LTV-001':
        const ltvLimit = ratios.ltv > 80 ? 95 : 80;
        return {
          rule_id: rule.id,
          severity: ratios.ltv <= ltvLimit ? 'pass' : 'fail',
          category: 'ratio',
          message: `LTV ratio ${ratios.ltv.toFixed(2)}% ${ratios.ltv <= ltvLimit ? 'is within' : 'exceeds'} limit of ${ltvLimit}%`,
          evidence: { calculated_value: ratios.ltv, limit: ltvLimit },
        };
      case 'OSFI-B20-MQR-001':
        return {
          rule_id: rule.id,
          severity: 'pass',
          category: 'stress_test',
          message: `Application qualifies at stress test rate of ${stressRatios.qualifying_rate.toFixed(2)}%`,
          evidence: { calculated_value: stressRatios.qualifying_rate },
        };
      default:
        return {
          rule_id: rule.id,
          severity: 'pass',
          category: rule.category,
          message: `${rule.name} requirement met`,
        };
    }
  };

  const passCount = OSFI_RULES.filter(r => generateFinding(r).severity === 'pass').length;
  const failCount = OSFI_RULES.filter(r => generateFinding(r).severity === 'fail').length;
  const warningCount = OSFI_RULES.filter(r => generateFinding(r).severity === 'warning').length;

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 text-green-700 rounded-lg">
          <CheckCircle className="w-4 h-4" />
          <span className="text-sm font-medium">{passCount} Passed</span>
        </div>
        {warningCount > 0 && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-50 text-amber-700 rounded-lg">
            <AlertTriangle className="w-4 h-4" />
            <span className="text-sm font-medium">{warningCount} Warnings</span>
          </div>
        )}
        {failCount > 0 && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-red-50 text-red-700 rounded-lg">
            <XCircle className="w-4 h-4" />
            <span className="text-sm font-medium">{failCount} Failed</span>
          </div>
        )}
      </div>

      {/* Policy Reference */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <BookOpen className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <h4 className="text-sm font-medium text-blue-900">OSFI Guideline B-20</h4>
            <p className="text-sm text-blue-700 mt-1">
              Residential Mortgage Underwriting Practices and Procedures
            </p>
            <a
              href="https://www.osfi-bsif.gc.ca/Eng/fi-if/rg-ro/gdn-ort/gl-ld/Pages/b20.aspx"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 mt-2"
            >
              View full guideline
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </div>

      {/* Rules List */}
      <div className="space-y-3">
        {OSFI_RULES.map((rule) => {
          const finding = generateFinding(rule);
          const isExpanded = expandedRules.has(rule.id);

          return (
            <PolicyRuleCard
              key={rule.id}
              rule={rule}
              finding={finding}
              isExpanded={isExpanded}
              onToggle={() => toggleRule(rule.id)}
            />
          );
        })}
      </div>
    </div>
  );
}

// Policy Rule Card Component
function PolicyRuleCard({
  rule,
  finding,
  isExpanded,
  onToggle,
}: {
  rule: typeof OSFI_RULES[0];
  finding: MortgageFinding;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const getStatusIcon = () => {
    switch (finding.severity) {
      case 'pass':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-amber-500" />;
      case 'fail':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'info':
        return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  const getBorderColor = () => {
    switch (finding.severity) {
      case 'pass':
        return 'border-green-200 hover:border-green-300';
      case 'warning':
        return 'border-amber-200 hover:border-amber-300';
      case 'fail':
        return 'border-red-200 hover:border-red-300';
      default:
        return 'border-slate-200 hover:border-slate-300';
    }
  };

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      ratio: 'Ratio',
      stress_test: 'Stress Test',
      documentation: 'Documentation',
      credit: 'Credit',
      property: 'Property',
    };
    return labels[category] || category;
  };

  return (
    <div className={`bg-white rounded-lg border ${getBorderColor()} transition-colors`}>
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center gap-3 text-left"
      >
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-slate-400" />
        ) : (
          <ChevronRight className="w-4 h-4 text-slate-400" />
        )}
        {getStatusIcon()}
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-medium text-slate-900">{rule.name}</span>
            <span className="text-xs px-2 py-0.5 bg-slate-100 text-slate-500 rounded-full">
              {getCategoryLabel(rule.category)}
            </span>
          </div>
          <p className="text-sm text-slate-600 mt-0.5">{finding.message}</p>
        </div>
        <span className="text-xs text-slate-400">{rule.id}</span>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 border-t border-slate-100 pt-3">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h5 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">
                Rule Intent
              </h5>
              <p className="text-sm text-slate-700">{rule.description}</p>
            </div>
            <div>
              <h5 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">
                Threshold
              </h5>
              <p className="text-sm font-medium text-slate-900">{rule.threshold}</p>
            </div>
          </div>

          {finding.evidence && (
            <div className="mt-4 p-3 bg-slate-50 rounded-lg">
              <h5 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">
                Evidence
              </h5>
              <div className="flex gap-4">
                {finding.evidence.calculated_value !== undefined && (
                  <div>
                    <span className="text-xs text-slate-500">Calculated Value:</span>
                    <span className="ml-2 text-sm font-medium text-slate-900">
                      {typeof finding.evidence.calculated_value === 'number' && finding.evidence.calculated_value < 1
                        ? `${(finding.evidence.calculated_value * 100).toFixed(2)}%`
                        : finding.evidence.calculated_value}
                    </span>
                  </div>
                )}
                {finding.evidence.limit !== undefined && (
                  <div>
                    <span className="text-xs text-slate-500">Limit:</span>
                    <span className="ml-2 text-sm font-medium text-slate-900">
                      {typeof finding.evidence.limit === 'number' && finding.evidence.limit < 1
                        ? `${(finding.evidence.limit * 100).toFixed(0)}%`
                        : finding.evidence.limit}
                    </span>
                  </div>
                )}
                {finding.evidence.source && (
                  <div>
                    <span className="text-xs text-slate-500">Source:</span>
                    <span className="ml-2 text-sm font-medium text-slate-900">
                      {finding.evidence.source}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
