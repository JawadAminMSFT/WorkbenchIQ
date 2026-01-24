'use client';

import { Briefcase, AlertTriangle } from 'lucide-react';
import type { ApplicationMetadata, ExtractedField } from '@/lib/types';
import ConfidenceIndicator from './ConfidenceIndicator';
import CitationTooltip from './CitationTooltip';

interface OccupationPanelProps {
  application: ApplicationMetadata;
}

interface OccupationFieldData {
  value: string | null;
  confidence?: number;
  citation?: ExtractedField;
}

interface OccupationData {
  occupation: OccupationFieldData;
  hazardousActivities: OccupationFieldData;
  foreignTravel: OccupationFieldData;
}

/**
 * Safely convert a field value to a displayable string
 */
function safeStringify(value: unknown): string | null {
  if (value === null || value === undefined) return null;
  if (typeof value === 'string') return value;
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  if (Array.isArray(value)) {
    // Handle arrays - join non-empty items
    return value
      .map(item => safeStringify(item))
      .filter(Boolean)
      .join(', ') || null;
  }
  if (typeof value === 'object') {
    // Handle objects - try to extract meaningful values
    const obj = value as Record<string, unknown>;
    // Check for common value patterns
    if ('valueString' in obj) return safeStringify(obj.valueString);
    if ('value' in obj) return safeStringify(obj.value);
    // Try to build a readable string from object properties
    const parts: string[] = [];
    for (const [key, val] of Object.entries(obj)) {
      const strVal = safeStringify(val);
      if (strVal && !key.startsWith('_')) {
        parts.push(`${key}: ${strVal}`);
      }
    }
    return parts.length > 0 ? parts.join(', ') : null;
  }
  return null;
}

/**
 * Parse hazardous activities from the complex nested structure
 */
function parseHazardousActivities(value: unknown): string | null {
  if (!value) return null;
  if (typeof value === 'string') return value;
  if (Array.isArray(value)) {
    const activities: string[] = [];
    for (const item of value) {
      const obj = item?.valueObject || item;
      const activity = obj?.activity?.valueString || obj?.activity;
      const details = obj?.details?.valueString || obj?.details;
      if (activity) {
        let text = activity;
        if (details && details !== activity) {
          text += ` (${details})`;
        }
        activities.push(text);
      }
    }
    return activities.length > 0 ? activities.join('; ') : null;
  }
  return safeStringify(value);
}

/**
 * Parse foreign travel, handling French responses
 */
function parseForeignTravel(value: unknown): string | null {
  if (!value) return null;
  const strVal = safeStringify(value);
  if (!strVal) return null;
  // Handle French "Non" or "Oui"
  if (strVal.toLowerCase() === 'non') return 'None planned';
  if (strVal.toLowerCase() === 'oui') return 'Yes - see details';
  return strVal;
}

function parseOccupationData(application: ApplicationMetadata): OccupationData {
  const fields = application.extracted_fields || {};
  
  // Try to get occupation from LLM outputs first
  let occupationValue: string | null = null;
  const customerProfile = (application.llm_outputs as any)?.application_summary?.customer_profile?.parsed;
  if (customerProfile?.key_fields) {
    const occField = customerProfile.key_fields.find((f: any) => f.label === 'Occupation');
    if (occField?.value && occField.value !== 'Not specified') {
      occupationValue = occField.value;
    }
  }
  
  // Fall back to extracted fields
  const occupationField = Object.values(fields).find(f => f.field_name === 'Occupation');
  if (!occupationValue && occupationField?.value) {
    occupationValue = safeStringify(occupationField.value);
  }
  
  const hazardousField = Object.values(fields).find(f => f.field_name === 'HazardousActivities');
  const travelField = Object.values(fields).find(f => f.field_name === 'ForeignTravelPlans');

  return {
    occupation: { 
      value: occupationValue,
      confidence: occupationField?.confidence,
      citation: occupationField,
    },
    hazardousActivities: { 
      value: parseHazardousActivities(hazardousField?.value),
      confidence: hazardousField?.confidence,
      citation: hazardousField,
    },
    foreignTravel: { 
      value: parseForeignTravel(travelField?.value),
      confidence: travelField?.confidence,
      citation: travelField,
    },
  };
}

export default function OccupationPanel({ application }: OccupationPanelProps) {
  const data = parseOccupationData(application);
  const hasData = data.occupation.value || data.hazardousActivities.value || data.foreignTravel.value;

  // Helper to build citation data
  const buildCitation = (field: OccupationFieldData) => field.citation ? {
    sourceFile: field.citation.source_file,
    pageNumber: field.citation.page_number,
    sourceText: field.citation.source_text,
  } : undefined;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center">
          <Briefcase className="w-5 h-5 text-indigo-600" />
        </div>
        <h2 className="text-base font-semibold text-slate-900">Occupation & Risk Factors</h2>
      </div>

      {/* Content */}
      {hasData ? (
        <div className="space-y-4">
          {data.occupation.value && (
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h4 className="text-xs font-medium text-slate-500 uppercase">Occupation</h4>
                {data.occupation.confidence !== undefined && (
                  <ConfidenceIndicator confidence={data.occupation.confidence} fieldName="Occupation" />
                )}
                {buildCitation(data.occupation) && (
                  <CitationTooltip citation={buildCitation(data.occupation)!} appId={application.id}>
                    <span></span>
                  </CitationTooltip>
                )}
              </div>
              <p className="text-sm text-slate-700">{data.occupation.value}</p>
            </div>
          )}
          {data.hazardousActivities.value && (
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h4 className="text-xs font-medium text-slate-500 uppercase flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3 text-amber-500" />
                  Hazardous Activities
                </h4>
                {data.hazardousActivities.confidence !== undefined && (
                  <ConfidenceIndicator confidence={data.hazardousActivities.confidence} fieldName="Hazardous Activities" />
                )}
                {buildCitation(data.hazardousActivities) && (
                  <CitationTooltip citation={buildCitation(data.hazardousActivities)!} appId={application.id}>
                    <span></span>
                  </CitationTooltip>
                )}
              </div>
              <p className="text-sm text-slate-700">{data.hazardousActivities.value}</p>
            </div>
          )}
          {data.foreignTravel.value && (
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h4 className="text-xs font-medium text-slate-500 uppercase">Foreign Travel</h4>
                {data.foreignTravel.confidence !== undefined && (
                  <ConfidenceIndicator confidence={data.foreignTravel.confidence} fieldName="Foreign Travel" />
                )}
                {buildCitation(data.foreignTravel) && (
                  <CitationTooltip citation={buildCitation(data.foreignTravel)!} appId={application.id}>
                    <span></span>
                  </CitationTooltip>
                )}
              </div>
              <p className="text-sm text-slate-700">{data.foreignTravel.value}</p>
            </div>
          )}
        </div>
      ) : (
        <p className="text-sm text-slate-500 italic">No occupation data extracted</p>
      )}
    </div>
  );
}
