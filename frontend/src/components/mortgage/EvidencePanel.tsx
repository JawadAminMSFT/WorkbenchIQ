/**
 * Evidence Panel Component
 * 
 * Left column of the mortgage workbench showing:
 * - Document groups (Identity, Income, Assets, Property, Credit)
 * - Document status and extraction confidence
 * - Quick property/borrower summary
 */

'use client';

import React, { useState } from 'react';
import {
  FileText, User, Building, DollarSign, CreditCard, Shield,
  CheckCircle, Clock, AlertTriangle, ChevronDown, ChevronRight,
  Eye, Download, Upload
} from 'lucide-react';
import type { MortgageDocument, MortgageBorrower, MortgageProperty } from './MortgageWorkbench';

interface EvidencePanelProps {
  documents: MortgageDocument[];
  borrower: MortgageBorrower;
  property: MortgageProperty;
  onViewDocument?: (doc: MortgageDocument) => void;
}
interface DocumentGroup {
  id: string;
  label: string;
  icon: typeof FileText;
  types: string[];
}

const DOCUMENT_GROUPS: DocumentGroup[] = [
  { id: 'identity', label: 'Identity', icon: User, types: ['id', 'passport', 'drivers_license', 'identity'] },
  { id: 'income', label: 'Income', icon: DollarSign, types: ['paystub', 'pay_stub', 'employment_letter', 'employment', 't4', 'noa', 'notice_of_assessment'] },
  { id: 'assets', label: 'Assets / Down Payment', icon: CreditCard, types: ['bank_statement', 'bank', 'investment', 'gift_letter', 'gift'] },
  { id: 'property', label: 'Property', icon: Building, types: ['purchase_agreement', 'purchase', 'appraisal', 'mls', 'title', 'agreement'] },
  { id: 'credit', label: 'Credit', icon: Shield, types: ['credit_report', 'credit'] },
  { id: 'other', label: 'Other', icon: FileText, types: ['other', 'application', 'mortgage_application'] },
];

export default function EvidencePanel({ documents, borrower, property, onViewDocument }: EvidencePanelProps) {
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set(['income', 'property']));

  const toggleGroup = (groupId: string) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(groupId)) {
      newExpanded.delete(groupId);
    } else {
      newExpanded.add(groupId);
    }
    setExpandedGroups(newExpanded);
  };

  const getDocumentsForGroup = (group: DocumentGroup): MortgageDocument[] => {
    if (group.id === 'other') {
      // "Other" is a catch-all: only documents not matched by any other group
      const nonOtherGroups = DOCUMENT_GROUPS.filter(g => g.id !== 'other');
      const matchedInOtherGroups = new Set(
        nonOtherGroups.flatMap(g => 
          documents.filter(doc => {
            const filename = doc.filename.toLowerCase().replace(/[_-]/g, ' ');
            return g.types.some(t => filename.includes(t.replace('_', ' ')));
          }).map(d => d.id)
        )
      );
      return documents.filter(doc => !matchedInOtherGroups.has(doc.id));
    }
    
    return documents.filter(doc => {
      const filename = doc.filename.toLowerCase().replace(/[_-]/g, ' ');
      return group.types.some(t => filename.includes(t.replace('_', ' ')));
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'processed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-amber-500" />;
      case 'error':
        return <AlertTriangle className="w-4 h-4 text-red-500" />;
      default:
        return <FileText className="w-4 h-4 text-slate-400" />;
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-CA', {
      style: 'currency',
      currency: 'CAD',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-slate-200">
        <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">
          Evidence
        </h2>
      </div>

      {/* Quick Summary */}
      <div className="p-4 border-b border-slate-200 bg-slate-50">
        <div className="space-y-3">
          {/* Borrower */}
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center flex-shrink-0">
              <User className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-900 truncate">{borrower.name}</p>
              <p className="text-xs text-slate-500">
                Credit Score: <span className="font-medium">{borrower.credit_score}</span>
              </p>
            </div>
          </div>

          {/* Property */}
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
              <Building className="w-4 h-4 text-blue-600" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-900 truncate">{property.address}</p>
              <p className="text-xs text-slate-500">
                {formatCurrency(property.purchase_price)} • {property.property_type}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Document Groups */}
      <div className="flex-1 overflow-y-auto">
        {DOCUMENT_GROUPS.map((group) => {
          const groupDocs = getDocumentsForGroup(group);
          const isExpanded = expandedGroups.has(group.id);
          const hasDocuments = groupDocs.length > 0;
          const allProcessed = groupDocs.every(d => d.status === 'processed');

          return (
            <div key={group.id} className="border-b border-slate-100">
              <button
                onClick={() => toggleGroup(group.id)}
                className="w-full px-4 py-3 flex items-center gap-3 hover:bg-slate-50 transition-colors"
              >
                {isExpanded ? (
                  <ChevronDown className="w-4 h-4 text-slate-400" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-slate-400" />
                )}
                <group.icon className="w-4 h-4 text-slate-500" />
                <span className="flex-1 text-left text-sm font-medium text-slate-700">
                  {group.label}
                </span>
                {hasDocuments && (
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    allProcessed
                      ? 'bg-green-100 text-green-700'
                      : 'bg-amber-100 text-amber-700'
                  }`}>
                    {groupDocs.length}
                  </span>
                )}
                {!hasDocuments && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-500">
                    0
                  </span>
                )}
              </button>

              {isExpanded && (
                <div className="px-4 pb-3">
                  {groupDocs.length === 0 ? (
                    <div className="flex items-center gap-2 py-2 px-3 bg-slate-50 rounded-lg text-sm text-slate-500">
                      <Upload className="w-4 h-4" />
                      <span>No documents uploaded</span>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {groupDocs.map((doc) => (
                        <div
                          key={doc.id}
                          className="flex items-center gap-3 py-2 px-3 bg-slate-50 rounded-lg hover:bg-slate-100 cursor-pointer transition-colors"
                          onClick={() => onViewDocument?.(doc)}
                        >
                          {getStatusIcon(doc.status)}
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-slate-700 truncate">{doc.filename}</p>
                            <p className="text-xs text-slate-500">
                              {doc.status === 'processed' 
                                ? (doc.fields_extracted ? `${doc.fields_extracted} fields extracted` : 'Processed')
                                : doc.status === 'pending' ? 'Pending...' : 'Error'}
                              {doc.confidence && (
                                <span className="ml-2">
                                  • {Math.round(doc.confidence * 100)}% confidence
                                </span>
                              )}
                            </p>
                          </div>
                          <button 
                            className="p-1 hover:bg-slate-200 rounded"
                            onClick={(e) => {
                              e.stopPropagation();
                              onViewDocument?.(doc);
                            }}
                          >
                            <Eye className="w-4 h-4 text-slate-400 hover:text-slate-600" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Upload Button */}
      <div className="p-4 border-t border-slate-200">
        <button className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-emerald-50 text-emerald-700 rounded-lg hover:bg-emerald-100 transition-colors text-sm font-medium">
          <Upload className="w-4 h-4" />
          Upload Documents
        </button>
      </div>
    </div>
  );
}
