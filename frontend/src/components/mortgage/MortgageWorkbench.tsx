/**
 * Mortgage Workbench Component
 * 
 * Main 3-column layout for mortgage underwriting:
 * - Left: Evidence Panel (documents, extraction results)
 * - Center: Data + Policy Tabs (worksheet, calculations, policy checks, conditions)
 * - Right: Risk + Narrative Panel
 * 
 * Based on mortgage-research/underwriter_workbench_ux_spec.md
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Home, FileText, Calculator, Shield, AlertTriangle, CheckCircle, XCircle,
  Upload, RefreshCw, Sparkles, ChevronRight, DollarSign, User, Building,
  Clock, Info, BookOpen, Scale, TrendingUp, AlertCircle, HelpCircle
} from 'lucide-react';
import EvidencePanel from './EvidencePanel';
import DataWorksheet from './DataWorksheet';
import CalculationsPanel from './CalculationsPanel';
import PolicyChecksPanel from './PolicyChecksPanel';
import RiskPanel from './RiskPanel';
import DecisionFooter from './DecisionFooter';
import PDFViewer from '../claims/PDFViewer';

// Types for mortgage data
export interface MortgageBorrower {
  name: string;
  first_name?: string;
  last_name?: string;
  co_borrower_name?: string;
  credit_score: number;
  employment_type?: string;
  employer_name?: string;
  occupation?: string;
  years_employed?: number;
}

export interface MortgageIncome {
  primary_borrower_income?: number;
  co_borrower_income?: number;
  annual_salary?: number;  // Fallback for legacy
  other_income?: number;
  total_annual_income: number;
  monthly_income?: number;
}

export interface MortgageProperty {
  address: string;
  purchase_price: number;
  appraised_value?: number;
  property_type: string;
  occupancy?: string;
}

export interface MortgageLoan {
  amount: number;
  down_payment: number;
  down_payment_source?: string;
  amortization_years: number;
  contract_rate?: number;  // New field
  rate?: number;  // Legacy fallback
  qualifying_rate?: number;
  term?: string;  // "5 years Fixed"
  term_years?: number;  // Legacy fallback
}

export interface MortgageLiabilities {
  property_taxes_monthly: number;
  heating_monthly: number;
  condo_fees_monthly?: number;
  other_debts_monthly?: number;
}

export interface MortgageRatios {
  gds: number;
  tds: number;
  ltv: number;
}

export interface MortgageStressRatios {
  gds: number;
  tds: number;
  qualifying_rate: number;
}

export interface MortgageFinding {
  rule_id?: string;
  type?: string;  // 'success', 'warning', 'condition', 'info'
  severity?: 'pass' | 'warning' | 'fail' | 'info';
  category?: string;
  message: string;
  evidence?: {
    calculated_value?: number;
    limit?: number;
    source?: string;
  };
  // Citation data for source tracking
  source_file?: string;
  confidence?: number;
  sources?: string[];  // List of source document types
}

export interface RiskSignal {
  id: string;
  category: string;
  severity: 'low' | 'medium' | 'high';
  title: string;
  description: string;
  source_documents?: string[];
}

// Field-level citation for confidence indicators
export interface FieldCitation {
  field_name: string;
  value?: string | number | null;
  confidence?: number;
  source_file?: string;
  page_number?: number | null;
  source_text?: string | null;
  bounding_box?: number[] | null;
}

export interface MortgageApplication {
  application_id: string;
  borrower: MortgageBorrower;
  co_borrower?: MortgageBorrower;
  income: MortgageIncome;
  property: MortgageProperty;
  loan: MortgageLoan;
  liabilities: MortgageLiabilities;
  ratios: MortgageRatios;
  stress_ratios: MortgageStressRatios;
  decision: 'APPROVE' | 'DECLINE' | 'REFER';
  findings: MortgageFinding[];
  risk_signals: RiskSignal[];
  documents?: MortgageDocument[];
  narrative?: string;
  policy_checks_count?: number;
  field_citations?: Record<string, FieldCitation>;
}

export interface MortgageDocument {
  id: string;
  type: string;
  filename: string;
  uploaded_at: string;
  status: 'pending' | 'processed' | 'error';
  url?: string;
  fields_extracted?: number;
  confidence?: number;
}

interface MortgageWorkbenchProps {
  applicationId: string;
  isLoading?: boolean;
}

type CenterTab = 'data' | 'calculations' | 'policy' | 'conditions';

/**
 * Mortgage Workbench - Main Component
 */
export default function MortgageWorkbench({
  applicationId,
  isLoading = false,
}: MortgageWorkbenchProps) {
  const [application, setApplication] = useState<MortgageApplication | null>(null);
  const [activeTab, setActiveTab] = useState<CenterTab>('data');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [decisionNotes, setDecisionNotes] = useState('');
  const [selectedDocument, setSelectedDocument] = useState<MortgageDocument | null>(null);

  // Handle document view click
  const handleViewDocument = (doc: MortgageDocument) => {
    if (doc.url) {
      setSelectedDocument(doc);
    }
  };

  // Fetch mortgage application data
  const fetchApplicationData = useCallback(async () => {
    setIsRefreshing(true);
    setError(null);
    try {
      // Call the mortgage analyze endpoint
      const response = await fetch(`/api/mortgage/applications/${applicationId}`);
      if (!response.ok) {
        throw new Error('Failed to load application');
      }
      const data = await response.json();
      
      // Transform API response to component format
      const app: MortgageApplication = {
        application_id: data.id || applicationId,
        borrower: data.borrower || {
          name: 'Unknown',
          credit_score: 0,
        },
        income: {
          primary_borrower_income: data.income?.primary_borrower_income || 0,
          co_borrower_income: data.income?.co_borrower_income || 0,
          annual_salary: data.income?.annual_salary || data.income?.primary_borrower_income || 0,
          total_annual_income: data.income?.total_annual_income || 0,
          monthly_income: data.income?.monthly_income || 0,
        },
        property: data.property || {
          address: 'Unknown',
          purchase_price: 0,
          property_type: 'unknown',
        },
        loan: {
          amount: data.loan?.amount || 0,
          down_payment: data.loan?.down_payment || 0,
          down_payment_source: data.loan?.down_payment_source,
          amortization_years: data.loan?.amortization_years || 25,
          contract_rate: data.loan?.contract_rate || data.loan?.rate || 5.25,
          rate: data.loan?.contract_rate || data.loan?.rate || 5.25,
          qualifying_rate: data.loan?.qualifying_rate,
          term: data.loan?.term,
        },
        liabilities: data.liabilities || {
          property_taxes_monthly: 0,
          heating_monthly: 0,
        },
        ratios: data.ratios || {
          gds: 0,
          tds: 0,
          ltv: 0,
        },
        stress_ratios: data.stress_ratios || {
          gds: 0,
          tds: 0,
          qualifying_rate: 5.25,
        },
        decision: data.decision || 'REFER',
        findings: data.findings || [],
        risk_signals: data.risk_signals || [],
        documents: data.documents || [],
        narrative: data.narrative,
        policy_checks_count: data.policy_checks_count || 0,
        field_citations: data.field_citations || {},
      };
      
      setApplication(app);
    } catch (err) {
      console.error('Failed to fetch mortgage data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load mortgage data');
    } finally {
      setIsRefreshing(false);
    }
  }, [applicationId]);

  useEffect(() => {
    fetchApplicationData();
  }, [fetchApplicationData]);

  // Handle decision actions
  const handleApprove = async () => {
    console.log('Approve application:', applicationId, decisionNotes);
  };

  const handleDecline = async () => {
    console.log('Decline application:', applicationId, decisionNotes);
  };

  const handleRefer = async () => {
    console.log('Refer application:', applicationId, decisionNotes);
  };

  const tabs: { id: CenterTab; label: string; icon: typeof Calculator }[] = [
    { id: 'data', label: 'Data Worksheet', icon: FileText },
    { id: 'calculations', label: 'Calculations', icon: Calculator },
    { id: 'policy', label: 'Policy Checks', icon: Shield },
    { id: 'conditions', label: 'Conditions', icon: AlertCircle },
  ];

  if (isLoading || isRefreshing) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-red-600">
        <AlertTriangle className="w-12 h-12 mb-4" />
        <p className="text-lg font-medium">{error}</p>
        <button
          onClick={fetchApplicationData}
          className="mt-4 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!application) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-slate-500">
        <Home className="w-12 h-12 mb-4" />
        <p className="text-lg">No mortgage application selected</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-slate-50">
      {/* Header Bar */}
      <div className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
              <Home className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-slate-900">
                {application.borrower.name}
              </h1>
              <p className="text-sm text-slate-500">
                Case {application.application_id} • {application.property.address}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <DecisionBadge decision={application.decision} />
            <button
              onClick={fetchApplicationData}
              className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg"
              title="Refresh"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Main 3-Column Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Column - Evidence Panel */}
        <div className="w-80 border-r border-slate-200 bg-white overflow-y-auto">
          <EvidencePanel
            documents={application.documents || []}
            borrower={application.borrower}
            property={application.property}
            onViewDocument={handleViewDocument}
          />
        </div>

        {/* Center Column - Tabs */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Tab Navigation */}
          <div className="bg-white border-b border-slate-200 px-4">
            <div className="flex gap-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-emerald-600 text-emerald-600'
                      : 'border-transparent text-slate-600 hover:text-slate-900 hover:border-slate-300'
                  }`}
                >
                  <tab.icon className="w-4 h-4" />
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {activeTab === 'data' && (
              <DataWorksheet
                borrower={application.borrower}
                coBorrower={application.co_borrower}
                income={application.income}
                property={application.property}
                loan={application.loan}
                liabilities={application.liabilities}
                fieldCitations={application.field_citations}
              />
            )}
            {activeTab === 'calculations' && (
              <CalculationsPanel
                ratios={application.ratios}
                stressRatios={application.stress_ratios}
                loan={application.loan}
                income={application.income}
                liabilities={application.liabilities}
              />
            )}
            {activeTab === 'policy' && (
              <PolicyChecksPanel
                findings={application.findings}
                ratios={application.ratios}
                stressRatios={application.stress_ratios}
              />
            )}
            {activeTab === 'conditions' && (
              <ConditionsPanel findings={application.findings} />
            )}
          </div>
        </div>

        {/* Right Column - Risk & Narrative */}
        <div className="w-96 border-l border-slate-200 bg-white overflow-y-auto">
          <RiskPanel
            riskSignals={application.risk_signals}
            decision={application.decision}
            findings={application.findings}
            narrative={application.narrative}
            policyChecksCount={application.policy_checks_count}
          />
        </div>
      </div>

      {/* Decision Footer */}
      <DecisionFooter
        decision={application.decision}
        decisionNotes={decisionNotes}
        onNotesChange={setDecisionNotes}
        onApprove={handleApprove}
        onDecline={handleDecline}
        onRefer={handleRefer}
        findings={application.findings}
      />

      {/* PDF Viewer Modal */}
      {selectedDocument && selectedDocument.url && (
        <PDFViewer
          url={selectedDocument.url}
          filename={selectedDocument.filename}
          onClose={() => setSelectedDocument(null)}
        />
      )}
    </div>
  );
}

// Helper Components
function DecisionBadge({ decision }: { decision: 'APPROVE' | 'DECLINE' | 'REFER' }) {
  const styles = {
    APPROVE: 'bg-green-100 text-green-700 border-green-200',
    DECLINE: 'bg-red-100 text-red-700 border-red-200',
    REFER: 'bg-amber-100 text-amber-700 border-amber-200',
  };

  const icons = {
    APPROVE: CheckCircle,
    DECLINE: XCircle,
    REFER: AlertTriangle,
  };

  const Icon = icons[decision];

  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium border ${styles[decision]}`}>
      <Icon className="w-4 h-4" />
      {decision}
    </span>
  );
}

function ConditionsPanel({ findings }: { findings: MortgageFinding[] }) {
  const failedFindings = findings.filter(f => f.severity === 'fail' || f.severity === 'warning');

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Conditions / Stipulations</h3>
        {failedFindings.length === 0 ? (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center gap-2 text-green-700">
              <CheckCircle className="w-5 h-5" />
              <span className="font-medium">No conditions required</span>
            </div>
            <p className="text-sm text-green-600 mt-1">
              All policy checks passed. Application can proceed without additional conditions.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {failedFindings.map((finding, idx) => (
              <div
                key={finding.rule_id}
                className={`border rounded-lg p-4 ${
                  finding.severity === 'fail'
                    ? 'border-red-200 bg-red-50'
                    : 'border-amber-200 bg-amber-50'
                }`}
              >
                <div className="flex items-start gap-3">
                  <AlertTriangle
                    className={`w-5 h-5 mt-0.5 ${
                      finding.severity === 'fail' ? 'text-red-500' : 'text-amber-500'
                    }`}
                  />
                  <div className="flex-1">
                    <p className={`font-medium ${
                      finding.severity === 'fail' ? 'text-red-700' : 'text-amber-700'
                    }`}>
                      {finding.message}
                    </p>
                    <p className="text-sm text-slate-600 mt-1">
                      Rule: {finding.rule_id} • Category: {finding.category}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
