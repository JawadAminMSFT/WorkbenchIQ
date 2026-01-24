/**
 * Data Worksheet Component
 * 
 * Displays canonical mortgage data with provenance tracking:
 * - Borrower information
 * - Income details
 * - Property details
 * - Loan terms
 * - Liabilities
 * 
 * Each field shows value, confidence, and source citations.
 */

'use client';

import React, { useState } from 'react';
import {
  User, DollarSign, Building, FileText,
  Edit2, ChevronDown, ChevronRight
} from 'lucide-react';
import type {
  MortgageBorrower,
  MortgageIncome,
  MortgageProperty,
  MortgageLoan,
  MortgageLiabilities,
  FieldCitation,
} from './MortgageWorkbench';
import ConfidenceIndicator from '../ConfidenceIndicator';
import CitableValue from '../CitableValue';

interface DataWorksheetProps {
  borrower: MortgageBorrower;
  coBorrower?: MortgageBorrower;
  income: MortgageIncome;
  property: MortgageProperty;
  loan: MortgageLoan;
  liabilities: MortgageLiabilities;
  fieldCitations?: Record<string, FieldCitation>;
}

interface DataField {
  label: string;
  value: string | number;
  fieldName?: string;  // Maps to field_citations key
  editable?: boolean;
  isCalculated?: boolean;  // For calculated fields without citations
}

interface DataSection {
  id: string;
  title: string;
  icon: typeof User;
  fields: DataField[];
}

export default function DataWorksheet({
  borrower,
  coBorrower,
  income,
  property,
  loan,
  liabilities,
  fieldCitations = {},
}: DataWorksheetProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['borrower', 'income', 'property', 'loan', 'liabilities'])
  );

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-CA', {
      style: 'currency',
      currency: 'CAD',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatPercent = (value: number) => {
    if (!isFinite(value)) return 'N/A';
    return `${(value * 100).toFixed(2)}%`;
  };

  // Helper to get citation for a field
  const getCitation = (fieldName?: string): FieldCitation | undefined => {
    if (!fieldName) return undefined;
    return fieldCitations[fieldName];
  };

  const sections: DataSection[] = [
    {
      id: 'borrower',
      title: 'Borrower Information',
      icon: User,
      fields: [
        { label: 'Name', value: borrower.name, fieldName: 'BorrowerName' },
        { label: 'Co-Borrower', value: borrower.co_borrower_name || 'N/A', fieldName: 'CoBorrowerName' },
        { label: 'Credit Score', value: borrower.credit_score, fieldName: 'CreditScore' },
        { label: 'Employment Type', value: borrower.employment_type || 'Permanent', fieldName: 'EmploymentStatus' },
        { label: 'Employer', value: borrower.employer_name || 'Not specified', fieldName: 'EmployerName' },
        { label: 'Occupation', value: borrower.occupation || 'Not specified', fieldName: 'OccupationTitle' },
      ],
    },
    {
      id: 'income',
      title: 'Income Details',
      icon: DollarSign,
      fields: [
        { label: 'Primary Borrower Income', value: formatCurrency(income.primary_borrower_income || income.annual_salary || 0), fieldName: 'BaseSalary', editable: true },
        { label: 'Co-Borrower Income', value: formatCurrency(income.co_borrower_income || 0), fieldName: 'CoBorrowerIncome', editable: true },
        { label: 'Total Annual Income', value: formatCurrency(income.total_annual_income), isCalculated: true },
        { label: 'Monthly Income', value: formatCurrency(income.monthly_income || income.total_annual_income / 12), isCalculated: true },
      ],
    },
    {
      id: 'property',
      title: 'Property Details',
      icon: Building,
      fields: [
        { label: 'Address', value: property.address, fieldName: 'PropertyAddress' },
        { label: 'Purchase Price', value: formatCurrency(property.purchase_price), fieldName: 'PurchasePrice' },
        { label: 'Appraised Value', value: formatCurrency(property.appraised_value || property.purchase_price), fieldName: 'AppraisedValue' },
        { label: 'Property Type', value: property.property_type, fieldName: 'PropertyType' },
        { label: 'Occupancy', value: property.occupancy || 'Owner Occupied', fieldName: 'PropertyOccupancy' },
      ],
    },
    {
      id: 'loan',
      title: 'Loan Terms',
      icon: FileText,
      fields: [
        { label: 'Loan Amount', value: formatCurrency(loan.amount), fieldName: 'RequestedLoanAmount' },
        { label: 'Down Payment', value: formatCurrency(loan.down_payment), fieldName: 'DownPaymentAmount' },
        { label: 'Down Payment %', value: formatPercent(loan.down_payment / property.purchase_price), isCalculated: true },
        { label: 'Down Payment Source', value: loan.down_payment_source || 'Savings', fieldName: 'DownPaymentSource' },
        { label: 'Amortization', value: `${loan.amortization_years} years`, fieldName: 'AmortizationYears' },
        { label: 'Contract Rate', value: `${loan.contract_rate || loan.rate}%`, fieldName: 'ContractRate' },
        { label: 'Term', value: loan.term || `${loan.term_years || 5} years`, fieldName: 'RateTerm' },
      ],
    },
    {
      id: 'liabilities',
      title: 'Monthly Liabilities',
      icon: DollarSign,
      fields: [
        { label: 'Property Taxes', value: formatCurrency(liabilities.property_taxes_monthly), isCalculated: true, editable: true },
        { label: 'Heating', value: formatCurrency(liabilities.heating_monthly), isCalculated: true, editable: true },
        { label: 'Condo Fees', value: formatCurrency(liabilities.condo_fees_monthly || 0), fieldName: 'CondoFees', editable: true },
        { label: 'Other Debts', value: formatCurrency(liabilities.other_debts_monthly || 0), fieldName: 'OtherDebtsMonthly', editable: true },
      ],
    },
  ];

  return (
    <div className="space-y-4">
      {sections.map((section) => {
        const isExpanded = expandedSections.has(section.id);
        const Icon = section.icon;

        return (
          <div key={section.id} className="bg-white rounded-lg border border-slate-200 overflow-hidden">
            <button
              onClick={() => toggleSection(section.id)}
              className="w-full px-4 py-3 flex items-center gap-3 hover:bg-slate-50 transition-colors"
            >
              {isExpanded ? (
                <ChevronDown className="w-4 h-4 text-slate-400" />
              ) : (
                <ChevronRight className="w-4 h-4 text-slate-400" />
              )}
              <div className="w-8 h-8 bg-emerald-100 rounded-lg flex items-center justify-center">
                <Icon className="w-4 h-4 text-emerald-600" />
              </div>
              <span className="flex-1 text-left font-medium text-slate-900">
                {section.title}
              </span>
            </button>

            {isExpanded && (
              <div className="px-4 pb-4">
                <div className="divide-y divide-slate-100">
                  {section.fields.map((field, idx) => {
                    const citation = getCitation(field.fieldName);
                    
                    return (
                      <div key={idx} className="py-3 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-slate-600">{field.label}</span>
                          {field.editable && (
                            <button className="p-1 hover:bg-slate-100 rounded">
                              <Edit2 className="w-3 h-3 text-slate-400" />
                            </button>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          {/* Value with citation tooltip */}
                          {citation ? (
                            <CitableValue
                              value={field.value}
                              citation={{
                                field_name: citation.field_name,
                                value: citation.value,
                                confidence: citation.confidence || 0,
                                source_file: citation.source_file,
                                page_number: citation.page_number || undefined,
                                source_text: citation.source_text || undefined,
                                bounding_box: citation.bounding_box || undefined,
                              }}
                              className="text-sm font-medium text-slate-900"
                            />
                          ) : (
                            <span className="text-sm font-medium text-slate-900">{field.value}</span>
                          )}
                          
                          {/* Confidence indicator */}
                          {citation?.confidence !== undefined && (
                            <ConfidenceIndicator 
                              confidence={citation.confidence} 
                              fieldName={field.label}
                            />
                          )}
                          
                          {/* Calculated badge for computed fields */}
                          {field.isCalculated && (
                            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                              Calculated
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        );
      })}

      {/* Co-Borrower Section */}
      {coBorrower && (
        <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
          <div className="px-4 py-3 flex items-center gap-3 bg-slate-50">
            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
              <User className="w-4 h-4 text-blue-600" />
            </div>
            <span className="font-medium text-slate-900">Co-Borrower Information</span>
          </div>
          <div className="px-4 py-4">
            <div className="divide-y divide-slate-100">
              <div className="py-3 flex items-center justify-between">
                <span className="text-sm text-slate-600">Name</span>
                <div className="flex items-center gap-2">
                  {fieldCitations['CoBorrowerName'] ? (
                    <CitableValue
                      value={coBorrower.name}
                      citation={{
                        field_name: 'CoBorrowerName',
                        value: coBorrower.name,
                        confidence: fieldCitations['CoBorrowerName'].confidence || 0,
                        source_file: fieldCitations['CoBorrowerName'].source_file,
                        page_number: fieldCitations['CoBorrowerName'].page_number || undefined,
                      }}
                      className="text-sm font-medium text-slate-900"
                    />
                  ) : (
                    <span className="text-sm font-medium text-slate-900">{coBorrower.name}</span>
                  )}
                  {fieldCitations['CoBorrowerName']?.confidence !== undefined && (
                    <ConfidenceIndicator 
                      confidence={fieldCitations['CoBorrowerName'].confidence} 
                      fieldName="Co-Borrower Name"
                    />
                  )}
                </div>
              </div>
              <div className="py-3 flex items-center justify-between">
                <span className="text-sm text-slate-600">Credit Score</span>
                <span className="text-sm font-medium text-slate-900">{coBorrower.credit_score}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
