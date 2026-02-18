'use client';

import { Users } from 'lucide-react';
import type { ApplicationMetadata, ExtractedField } from '@/lib/types';
import ConfidenceIndicator from './ConfidenceIndicator';
import CitationTooltip from './CitationTooltip';

interface FamilyHistoryPanelProps {
  application: ApplicationMetadata;
}

interface FamilyHistoryData {
  summary?: string;
  conditions: string[];
  riskAssessment?: string;
  confidence?: number;
  citation?: ExtractedField;
}

function parseFamilyHistory(application: ApplicationMetadata): FamilyHistoryData {
  const fields = application.extracted_fields || {};
  
  // Get confidence from underlying extracted fields
  const summaryField = Object.values(fields).find(f => f.field_name === 'FamilyHistorySummary');
  const arrayField = Object.values(fields).find(f => f.field_name === 'FamilyHistory');
  const extractedConfidence = summaryField?.confidence ?? arrayField?.confidence;
  const citationField = summaryField || arrayField;
  
  // First, try LLM outputs (preferred - processed and cleaned)
  const llmFamilyHistory = application.llm_outputs?.medical_summary?.family_history?.parsed as any;
  if (llmFamilyHistory && llmFamilyHistory.relatives) {
    const relatives = Array.isArray(llmFamilyHistory.relatives) ? llmFamilyHistory.relatives : [];
    const conditions = relatives.map((rel: any) => {
      const parts: string[] = [];
      if (rel.relationship) parts.push(rel.relationship);
      if (rel.condition && rel.condition !== 'None reported') parts.push(rel.condition);
      if (rel.age_at_death) parts.push(`died at ${rel.age_at_death}`);
      if (rel.age_at_onset && rel.age_at_onset !== 'N/A') parts.push(`onset ${rel.age_at_onset}`);
      if (rel.notes) parts.push(`(${rel.notes})`);
      return parts.join(': ');
    }).filter(Boolean);
    
    return {
      summary: llmFamilyHistory.summary,
      conditions,
      riskAssessment: llmFamilyHistory.risk_assessment,
      confidence: extractedConfidence,
      citation: citationField,
    };
  }
  
  // Fall back to extracted fields
  // Try FamilyHistorySummary (string) first for best display, then FamilyHistory (array)
  
  // Prefer the summary string if it has a value
  if (summaryField?.value && typeof summaryField.value === 'string') {
    const valueStr = String(summaryField.value);
    const conditions = valueStr
      .split(/[;\n]/)
      .map(s => s.trim())
      .filter(s => s.length > 0);
    return { conditions, confidence: summaryField.confidence, citation: summaryField };
  }
  
  // Fall back to array format
  if (arrayField?.value && Array.isArray(arrayField.value)) {
    const conditions = arrayField.value.map((item: any) => {
      const parts: string[] = [];
      // Handle nested valueObject format from Azure Content Understanding
      const obj = item.valueObject || item;
      const relationship = obj.relationship?.valueString || obj.relationship;
      const condition = obj.condition?.valueString || obj.condition;
      const age = obj.ageAtDiagnosis?.valueString || obj.ageAtDiagnosis;
      const status = obj.livingStatus?.valueString || obj.livingStatus;
      
      if (relationship) parts.push(relationship);
      if (condition) parts.push(condition);
      if (age) parts.push(`age ${age}`);
      if (status) parts.push(status);
      return parts.join(': ');
    }).filter(Boolean);
    return { conditions, confidence: arrayField.confidence, citation: arrayField };
  }
  
  // Legacy: check if FamilyHistory has a string value
  if (arrayField?.value && typeof arrayField.value === 'string') {
    const valueStr = String(arrayField.value);
    const conditions = valueStr
      .split(/[;\n]/)
      .map(s => s.trim())
      .filter(s => s.length > 0);
    return { conditions, confidence: arrayField.confidence, citation: arrayField };
  }
  
  return { conditions: [] };
}

export default function FamilyHistoryPanel({ application }: FamilyHistoryPanelProps) {
  const { summary, conditions, riskAssessment, confidence, citation } = parseFamilyHistory(application);

  // Build citation data for tooltip
  const citationData = citation ? {
    sourceFile: citation.source_file,
    pageNumber: citation.page_number,
    sourceText: citation.source_text,
  } : undefined;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 max-h-[400px] overflow-y-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-4 sticky top-0 bg-white pb-2 -mt-2 pt-2 z-10">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-teal-100 rounded-lg flex items-center justify-center flex-shrink-0">
            <Users className="w-5 h-5 text-teal-600" />
          </div>
          <h2 className="text-base font-semibold text-slate-900">Family History</h2>
        </div>
        <div className="flex items-center gap-2">
          {/* Confidence & Citation indicators */}
          {confidence !== undefined && (
            <ConfidenceIndicator confidence={confidence} fieldName="Family History" />
          )}
          {citationData && (
            <CitationTooltip citation={citationData} appId={application.id}>
              <span></span>
            </CitationTooltip>
          )}
          {/* Risk badge */}
          {riskAssessment && (
            <span className={`px-2.5 py-1 rounded-full text-xs font-medium whitespace-nowrap max-w-[120px] truncate ${
              riskAssessment.toLowerCase().includes('high') 
                ? 'bg-rose-100 text-rose-700'
                : riskAssessment.toLowerCase().includes('moderate')
                ? 'bg-amber-100 text-amber-700'
                : 'bg-emerald-100 text-emerald-700'
            }`} title={`${riskAssessment} Risk`}>
              {riskAssessment.length > 10 ? riskAssessment.split('-')[0] : riskAssessment} Risk
            </span>
          )}
        </div>
      </div>

      {/* Summary */}
      {summary && (
        <p className="text-sm text-slate-600 mb-4">{summary}</p>
      )}

      {/* Conditions List */}
      {conditions.length > 0 ? (
        <ul className="space-y-2">
          {conditions.map((condition, idx) => (
            <li key={idx} className="flex items-start gap-2 text-sm text-slate-700">
              <span className="text-slate-400 mt-1">•</span>
              <span>{condition}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-slate-500 italic">No family history data available</p>
      )}
    </div>
  );
}
