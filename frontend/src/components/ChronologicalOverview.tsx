'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, FileText } from 'lucide-react';
import type { ApplicationMetadata } from '@/lib/types';
import ConfidenceIndicator from './ConfidenceIndicator';
import clsx from 'clsx';

interface ChronologicalOverviewProps {
  application: ApplicationMetadata;
  fullWidth?: boolean;
}

interface TimelineEntry {
  date: string;
  year: string;
  title: string;
  description?: string;
  color: 'orange' | 'yellow' | 'blue' | 'green' | 'purple' | 'red';
  details?: string;
  sortDate?: number;
  confidence?: number;
}

function parseDate(text: string): Date | null {
  // Try to match YYYY-MM-DD format
  let match = text.match(/(\d{4})-(\d{2})-(\d{2})/);
  if (match) {
    return new Date(parseInt(match[1]), parseInt(match[2]) - 1, parseInt(match[3]));
  }
  
  // Try to match YYYY-MM format
  match = text.match(/(\d{4})-(\d{2})/);
  if (match) {
    return new Date(parseInt(match[1]), parseInt(match[2]) - 1, 1);
  }
  
  // Try to match just YYYY
  match = text.match(/(\d{4})/);
  if (match) {
    return new Date(parseInt(match[1]), 0, 1);
  }
  
  return null;
}

function formatDateDisplay(date: Date | null): { date: string; year: string } {
  if (!date) {
    return { date: 'N/A', year: '' };
  }
  
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const month = months[date.getMonth()];
  const day = date.getDate().toString().padStart(2, '0');
  const year = date.getFullYear().toString();
  
  return {
    date: `${month}-${day}`,
    year: year,
  };
}

function getStringValue(field: any): string {
  if (!field) return '';
  if (typeof field === 'string') return field;
  if (field.valueString) return field.valueString;
  if (field.content) return field.content;
  if (field.text) return field.text;
  return '';
}

function buildTimelineFromData(application: ApplicationMetadata): TimelineEntry[] {
  const entries: TimelineEntry[] = [];
  const fields = application.extracted_fields || {};
  
  // Get confidence from underlying extracted fields
  const medicalField = Object.values(fields).find(f => f.field_name === 'MedicalConditionsSummary');
  const medicalConfidence = medicalField?.confidence;

  // First, try LLM outputs for conditions from other_medical_findings
  const llmOtherFindings = application.llm_outputs?.medical_summary?.other_medical_findings?.parsed as any;
  if (llmOtherFindings?.conditions && Array.isArray(llmOtherFindings.conditions)) {
    llmOtherFindings.conditions.forEach((condition: any, idx: number) => {
      const name = condition.name || 'Unknown condition';
      const onset = condition.onset || '';
      const status = condition.status || '';
      const details = condition.details || '';
      
      const title = `${name}${status ? ' (' + status + ')' : ''}`;
      const fullDetails = `${name}\nOnset: ${onset}\nStatus: ${status}\nDetails: ${details}`;
      
      const parsedDate = parseDate(onset);
      const displayDate = formatDateDisplay(parsedDate);
      
      entries.push({
        date: displayDate.date,
        year: displayDate.year,
        title: title.substring(0, 50) + (title.length > 50 ? '...' : ''),
        description: title,
        color: ['orange', 'yellow', 'blue', 'green', 'purple'][idx % 5] as TimelineEntry['color'],
        details: fullDetails,
        sortDate: parsedDate?.getTime() || 0,
        confidence: medicalConfidence,
      });
    });
  } else {
    // Fall back to extracted fields - Parse medical conditions (string format)
    if (medicalField?.value) {
      const conditions = String(medicalField.value).split(';').map(s => s.trim()).filter(Boolean);
      conditions.forEach((condition, idx) => {
        const parsedDate = parseDate(condition);
        const displayDate = formatDateDisplay(parsedDate);
        entries.push({
          date: displayDate.date,
          year: displayDate.year,
          title: condition.substring(0, 50) + (condition.length > 50 ? '...' : ''),
          description: condition,
          color: ['orange', 'yellow', 'blue', 'green', 'purple'][idx % 5] as TimelineEntry['color'],
          details: condition,
          sortDate: parsedDate?.getTime() || 0,
          confidence: medicalConfidence,
        });
      });
    }
  }

  // Parse surgeries and hospitalizations
  const surgeryField = Object.values(fields).find(f => f.field_name === 'SurgeriesAndHospitalizations');
  if (surgeryField?.value) {
    const surgeryConfidence = surgeryField.confidence;
    // Handle new format: array of objects
    if (Array.isArray(surgeryField.value)) {
      surgeryField.value.forEach((item: any) => {
        // Handle nested valueObject structure from Azure Content Understanding
        const surgery = item.valueObject || item;
        
        const procedure = getStringValue(surgery.procedure) || 'Unknown procedure';
        const date = getStringValue(surgery.date) || '';
        const reason = getStringValue(surgery.reason) || '';
        const outcome = getStringValue(surgery.outcome) || '';
        
        const title = `${procedure}${reason ? ' - ' + reason : ''}`;
        const details = `${procedure}\nDate: ${date}\nReason: ${reason}\nOutcome: ${outcome}`;
        
        const parsedDate = parseDate(date);
        const displayDate = formatDateDisplay(parsedDate);
        
        entries.push({
          date: displayDate.date,
          year: displayDate.year,
          title: title.substring(0, 50) + (title.length > 50 ? '...' : ''),
          description: title,
          color: 'red',
          details: details,
          sortDate: parsedDate?.getTime() || 0,
          confidence: surgeryConfidence,
        });
      });
    } else {
      // Handle old format: semicolon-separated string
      const surgeries = String(surgeryField.value).split(';').map(s => s.trim()).filter(Boolean);
      surgeries.forEach((surgery) => {
        const parsedDate = parseDate(surgery);
        const displayDate = formatDateDisplay(parsedDate);
        entries.push({
          date: displayDate.date,
          year: displayDate.year,
          title: surgery.substring(0, 50) + (surgery.length > 50 ? '...' : ''),
          description: surgery,
          color: 'red',
          details: surgery,
          sortDate: parsedDate?.getTime() || 0,
          confidence: surgeryConfidence,
        });
      });
    }
  }

  // Parse diagnostic tests
  const diagField = Object.values(fields).find(f => f.field_name === 'DiagnosticTestsSummary' || f.field_name === 'DiagnosticTests');
  if (diagField?.value) {
    const diagConfidence = diagField.confidence;
    // Handle new format: array of objects
    if (Array.isArray(diagField.value)) {
      diagField.value.forEach((item: any) => {
        // Handle nested valueObject structure from Azure Content Understanding
        const test = item.valueObject || item;
        
        const testType = getStringValue(test.testType) || 'Unknown test';
        const date = getStringValue(test.date) || '';
        const reason = getStringValue(test.reason) || '';
        const result = getStringValue(test.result) || '';
        
        const title = `${testType}${result ? ' - ' + result : ''}`;
        const details = `${testType}\nDate: ${date}\nReason: ${reason}\nResult: ${result}`;
        
        const parsedDate = parseDate(date);
        const displayDate = formatDateDisplay(parsedDate);
        
        entries.push({
          date: displayDate.date,
          year: displayDate.year,
          title: title.substring(0, 50) + (title.length > 50 ? '...' : ''),
          description: title,
          color: 'purple',
          details: details,
          sortDate: parsedDate?.getTime() || 0,
          confidence: diagConfidence,
        });
      });
    } else {
      // Handle old format: semicolon-separated string
      const tests = String(diagField.value).split(';').map(s => s.trim()).filter(Boolean);
      tests.forEach((test) => {
        const parsedDate = parseDate(test);
        const displayDate = formatDateDisplay(parsedDate);
        entries.push({
          date: displayDate.date,
          year: displayDate.year,
          title: test.substring(0, 50) + (test.length > 50 ? '...' : ''),
          description: test,
          color: 'purple',
          details: test,
          sortDate: parsedDate?.getTime() || 0,
          confidence: diagConfidence,
        });
      });
    }
  }

  // Sort entries by date in descending order (newest first)
  entries.sort((a, b) => (b.sortDate || 0) - (a.sortDate || 0));

  return entries;
}

function buildDocumentsFromData(application: ApplicationMetadata): { name: string; pages: number }[] {
  return (application.files || []).map(f => ({
    name: f.filename,
    pages: 1, // We don't have page count in metadata
  }));
}

export default function ChronologicalOverview({ application, fullWidth }: ChronologicalOverviewProps) {
  const [activeTab, setActiveTab] = useState<'medical' | 'documents'>('medical');
  const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set());

  const timelineItems = buildTimelineFromData(application);
  const documents = buildDocumentsFromData(application);

  const colorClasses: Record<string, string> = {
    orange: 'bg-orange-500',
    yellow: 'bg-yellow-500',
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
    red: 'bg-red-500',
  };

  const toggleExpand = (idx: number) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(idx)) {
      newExpanded.delete(idx);
    } else {
      newExpanded.add(idx);
    }
    setExpandedItems(newExpanded);
  };

  return (
    <div className={clsx(
      "bg-white rounded-xl shadow-sm border border-slate-200 h-full flex flex-col",
      fullWidth && "max-w-4xl"
    )}>
      {/* Header */}
      <div className="p-4 border-b border-slate-200">
        <h2 className="text-lg font-semibold text-slate-900">Chronological Overview</h2>
        <p className="text-xs text-slate-500 mt-1">
          Medical events and documents extracted from application
        </p>

        {/* Tabs */}
        <div className="flex mt-3 border-b border-slate-200">
          <button
            onClick={() => setActiveTab('medical')}
            className={clsx(
              'px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors',
              activeTab === 'medical'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            )}
          >
            Medical Items ({timelineItems.length})
          </button>
          <button
            onClick={() => setActiveTab('documents')}
            className={clsx(
              'px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors',
              activeTab === 'documents'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            )}
          >
            Documents ({documents.length})
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        {activeTab === 'medical' ? (
          timelineItems.length > 0 ? (
            <div className="relative">
              {/* Timeline line */}
              <div className="absolute left-8 top-0 bottom-0 w-px bg-slate-200" />

              {/* Timeline items */}
              <div className="space-y-4">
                {timelineItems.map((item, idx) => (
                  <div key={idx} className="relative flex gap-4">
                    {/* Date column */}
                    <div className="w-12 text-right flex-shrink-0">
                      <div className="text-xs font-medium text-slate-500">{item.date}</div>
                      <div className="text-xs text-slate-400">{item.year}</div>
                    </div>

                    {/* Timeline dot */}
                    <div
                      className={clsx(
                        'w-3 h-3 rounded-full flex-shrink-0 mt-1 z-10',
                        colorClasses[item.color]
                      )}
                    />

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <button
                        onClick={() => toggleExpand(idx)}
                        className="flex items-center justify-between w-full text-left group"
                      >
                        <div className="flex items-center gap-2">
                          <div className="text-sm font-medium text-slate-900 group-hover:text-blue-600 transition-colors">
                            {item.title}
                          </div>
                          {item.confidence !== undefined && (
                            <ConfidenceIndicator 
                              confidence={item.confidence} 
                              fieldName={item.title}
                            />
                          )}
                        </div>
                        {item.details && (
                          expandedItems.has(idx) ? (
                            <ChevronUp className="w-4 h-4 text-slate-400 flex-shrink-0" />
                          ) : (
                            <ChevronDown className="w-4 h-4 text-slate-400 flex-shrink-0" />
                          )
                        )}
                      </button>

                      {/* Expanded content */}
                      {expandedItems.has(idx) && item.details && (
                        <div className="mt-2 p-3 bg-slate-50 rounded-lg text-xs text-slate-600">
                          <p>{item.details}</p>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-500 italic text-center py-8">
              No medical timeline data extracted
            </p>
          )
        ) : (
          // Documents tab
          documents.length > 0 ? (
            <div className="space-y-2">
              {documents.map((doc, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg"
                >
                  <FileText className="w-5 h-5 text-blue-500" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900 truncate">
                      {doc.name}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500 italic text-center py-8">
              No documents uploaded
            </p>
          )
        )}
      </div>
    </div>
  );
}
