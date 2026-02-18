'use client';

import CitationTooltip, { CitationData, CitationBadge } from './CitationTooltip';
import type { ExtractedField } from '@/lib/types';

interface CitableValueProps {
  /** The value to display */
  value: string | number | null | undefined;
  /** Citation/source information for this value */
  citation?: ExtractedField | CitationData | null;
  /** Application ID for building PDF URLs */
  appId?: string;
  /** Additional CSS classes for the value text */
  className?: string;
  /** Callback when user clicks "View in Document" */
  onViewDocument?: (pageNumber: number, sourceFile?: string) => void;
  /** Position of the tooltip */
  tooltipPosition?: 'top' | 'bottom' | 'left' | 'right';
  /** Show citation even for empty values */
  showEmpty?: boolean;
  /** Placeholder text when value is empty */
  placeholder?: string;
  /** Use compact citation badge instead of tooltip */
  compact?: boolean;
}

/**
 * CitableValue - Wrapper component for displaying values with source citations
 * 
 * Usage:
 * ```tsx
 * <CitableValue 
 *   value={patient.bloodPressure}
 *   citation={extractedFields['BloodPressureReadings']}
 * />
 * ```
 * 
 * For extracted fields, maps the ExtractedField type to CitationData:
 * - source_file -> sourceFile
 * - page_number -> pageNumber  
 * - source_text -> sourceText
 * - confidence -> confidence
 * - field_name -> fieldName
 */
export default function CitableValue({
  value,
  citation,
  appId,
  className = '',
  onViewDocument,
  tooltipPosition = 'top',
  showEmpty = false,
  placeholder = 'N/A',
  compact = false,
}: CitableValueProps) {
  // Handle empty values
  const isEmpty = value === null || value === undefined || value === '';
  if (isEmpty && !showEmpty) {
    return null;
  }

  const displayValue = isEmpty ? placeholder : String(value);

  // If no citation, just render the value
  if (!citation) {
    return <span className={className}>{displayValue}</span>;
  }

  // Helper to check if citation is ExtractedField (snake_case) or CitationData (camelCase)
  const isExtractedField = (c: ExtractedField | CitationData): c is ExtractedField => {
    return 'field_name' in c;
  };

  // Map ExtractedField to CitationData format (without confidence - that's shown separately)
  const citationData: CitationData = isExtractedField(citation)
    ? {
        sourceFile: citation.source_file,
        pageNumber: citation.page_number,
        sourceText: citation.source_text,
        fieldName: citation.field_name,
        boundingBox: citation.bounding_box,
      }
    : citation;

  // Compact mode - just show badge
  if (compact) {
    return (
      <span className={`inline-flex items-center gap-1.5 ${className}`}>
        <span>{displayValue}</span>
        <CitationBadge 
          pageNumber={citationData.pageNumber} 
          sourceFile={citationData.sourceFile} 
        />
      </span>
    );
  }

  // Full tooltip mode
  return (
    <CitationTooltip
      citation={citationData}
      appId={appId}
      onViewDocument={onViewDocument}
      position={tooltipPosition}
    >
      <span className={className}>{displayValue}</span>
    </CitationTooltip>
  );
}

/**
 * Hook to get citation data for a field from extracted fields
 */
export function useCitation(
  extractedFields: Record<string, ExtractedField> | undefined,
  fieldName: string
): ExtractedField | undefined {
  if (!extractedFields) return undefined;
  
  // Direct lookup
  if (extractedFields[fieldName]) {
    return extractedFields[fieldName];
  }
  
  // Try with file prefix pattern "filename:FieldName"
  for (const key of Object.keys(extractedFields)) {
    if (key.endsWith(`:${fieldName}`)) {
      return extractedFields[key];
    }
  }
  
  return undefined;
}

/**
 * Helper to find citation by partial field name match
 */
export function findCitation(
  extractedFields: Record<string, ExtractedField> | undefined,
  searchTerms: string[]
): ExtractedField | undefined {
  if (!extractedFields) return undefined;
  
  for (const term of searchTerms) {
    const lowerTerm = term.toLowerCase();
    for (const [key, field] of Object.entries(extractedFields)) {
      if (key.toLowerCase().includes(lowerTerm)) {
        return field;
      }
    }
  }
  
  return undefined;
}

/**
 * CitableField - Labeled field with citation support
 */
interface CitableFieldProps {
  label: string;
  value: string | number | null | undefined;
  citation?: ExtractedField | CitationData | null;
  onViewDocument?: (pageNumber: number, sourceFile?: string) => void;
  labelClassName?: string;
  valueClassName?: string;
}

export function CitableField({
  label,
  value,
  citation,
  onViewDocument,
  labelClassName = 'text-xs text-slate-500 uppercase tracking-wide',
  valueClassName = 'text-sm font-medium text-slate-900',
}: CitableFieldProps) {
  const isEmpty = value === null || value === undefined || value === '';
  
  return (
    <div className="space-y-1">
      <div className={labelClassName}>{label}</div>
      {isEmpty ? (
        <div className="text-sm text-slate-400">—</div>
      ) : (
        <CitableValue
          value={value}
          citation={citation}
          className={valueClassName}
          onViewDocument={onViewDocument}
        />
      )}
    </div>
  );
}

/**
 * CitableList - List of values with citations
 */
interface CitableListProps {
  items: Array<{
    value: string;
    citation?: ExtractedField | CitationData | null;
  }>;
  onViewDocument?: (pageNumber: number, sourceFile?: string) => void;
  itemClassName?: string;
  listClassName?: string;
}

export function CitableList({
  items,
  onViewDocument,
  itemClassName = 'text-sm text-slate-700',
  listClassName = 'space-y-1',
}: CitableListProps) {
  if (!items || items.length === 0) {
    return <div className="text-sm text-slate-400">None reported</div>;
  }

  return (
    <ul className={listClassName}>
      {items.map((item, index) => (
        <li key={index} className="flex items-start gap-2">
          <span className="text-slate-300 mt-1">•</span>
          <CitableValue
            value={item.value}
            citation={item.citation}
            className={itemClassName}
            onViewDocument={onViewDocument}
          />
        </li>
      ))}
    </ul>
  );
}
