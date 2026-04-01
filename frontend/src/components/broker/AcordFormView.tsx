'use client';

import React, { useState } from 'react';
import { Pencil, Check, X, FileText } from 'lucide-react';

/* ------------------------------------------------------------------ */
/*  Section grouping config for ACORD 125                             */
/* ------------------------------------------------------------------ */

const ACORD_125_SECTIONS: Array<{
  id: string;
  label: string;
  keywords: string[];
}> = [
  {
    id: 'applicant',
    label: 'Applicant Information',
    keywords: [
      'named_insured',
      'insured',
      'fein',
      'business_phone',
      'phone',
      'mailing_address',
      'address',
      'contact',
      'email',
      'website',
      'entity',
      'applicant',
    ],
  },
  {
    id: 'insurance_history',
    label: 'Insurance History',
    keywords: [
      'prior_carrier',
      'prior_premium',
      'prior_policy',
      'years_with',
      'claims',
      'loss_history',
      'current_carrier',
    ],
  },
  {
    id: 'classification',
    label: 'Classification',
    keywords: [
      'sic',
      'naics',
      'business_type',
      'class_code',
      'description',
      'industry',
    ],
  },
  {
    id: 'financial',
    label: 'Financial',
    keywords: ['revenue', 'payroll', 'assets', 'gross_sales', 'net_worth'],
  },
  {
    id: 'coverage',
    label: 'Coverage',
    keywords: [
      'coverage',
      'policy_period',
      'limit',
      'deductible',
      'premium',
      'retention',
      'modification',
    ],
  },
];

/* ------------------------------------------------------------------ */
/*  Helpers                                                           */
/* ------------------------------------------------------------------ */

function groupFieldsBySection(
  fields: Record<string, unknown>,
  sections: typeof ACORD_125_SECTIONS,
): Array<{ id: string; label: string; entries: [string, unknown][] }> {
  const allEntries = Object.entries(fields);
  const assigned = new Set<string>();
  const result: Array<{
    id: string;
    label: string;
    entries: [string, unknown][];
  }> = [];

  for (const section of sections) {
    const sectionEntries = allEntries.filter(([key]) => {
      const keyLower = key.toLowerCase();
      return (
        section.keywords.some((kw) => keyLower.includes(kw)) &&
        !assigned.has(key)
      );
    });
    if (sectionEntries.length > 0) {
      sectionEntries.forEach(([key]) => assigned.add(key));
      result.push({
        id: section.id,
        label: section.label,
        entries: sectionEntries,
      });
    }
  }

  const remaining = allEntries.filter(([key]) => !assigned.has(key));
  if (remaining.length > 0) {
    result.push({ id: 'other', label: 'General', entries: remaining });
  }

  return result;
}

function formatFieldLabel(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function confidenceBadge(confidence: number | undefined) {
  if (confidence == null) return null;
  const pct = Math.round(confidence * 100);
  if (pct >= 80) {
    return (
      <span className="text-xs font-medium text-green-700 bg-green-100 px-1.5 py-0.5 rounded whitespace-nowrap">
        {pct}% ✓
      </span>
    );
  }
  if (pct >= 60) {
    return (
      <span className="text-xs font-medium text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded whitespace-nowrap">
        {pct}% ⚠
      </span>
    );
  }
  return (
    <span className="text-xs font-medium text-red-700 bg-red-100 px-1.5 py-0.5 rounded whitespace-nowrap">
      {pct}% ✗
    </span>
  );
}

/**
 * Try to split ACORD 140 fields into per-location groups.
 * Supports "location_N_*" key patterns and nested location objects.
 */
function groupAcord140ByLocation(
  fields: Record<string, unknown>,
): Array<{ label: string; entries: [string, unknown][] }> {
  const entries = Object.entries(fields ?? {});
  if (entries.length === 0) return [];

  const locationPattern = /^(location|loc|loss)[_\s]?(\d+)[_\s]/i;
  const locationMap = new Map<string, [string, unknown][]>();
  const ungrouped: [string, unknown][] = [];

  for (const [key, value] of entries) {
    const match = key.match(locationPattern);
    if (match) {
      const prefix = match[1].toLowerCase();
      const label = prefix === 'loss'
        ? `Loss History ${match[2]}`
        : `Location ${match[2]}`;
      if (!locationMap.has(label)) locationMap.set(label, []);
      const shortKey = key.replace(locationPattern, '').replace(/^_/, '');
      locationMap.get(label)!.push([shortKey || key, value]);
    } else if (
      typeof value === 'object' &&
      value !== null &&
      !Array.isArray(value)
    ) {
      const nestedEntries = Object.entries(
        value as Record<string, unknown>,
      );
      if (nestedEntries.length > 0) {
        locationMap.set(formatFieldLabel(key), nestedEntries);
      }
    } else {
      ungrouped.push([key, value]);
    }
  }

  const result: Array<{ label: string; entries: [string, unknown][] }> = [];
  for (const [label, fieldEntries] of locationMap) {
    result.push({ label, entries: fieldEntries });
  }
  if (ungrouped.length > 0) {
    result.push({ label: 'General', entries: ungrouped });
  }

  // If no meaningful grouping was detected, return empty so caller renders flat
  if (result.length <= 1 && ungrouped.length === entries.length) return [];
  return result;
}

/* ------------------------------------------------------------------ */
/*  Inline editable field                                             */
/* ------------------------------------------------------------------ */

function EditableField({
  fieldKey,
  value,
  confidence,
  sourceName,
  onSave,
}: {
  fieldKey: string;
  value: unknown;
  confidence: number | undefined;
  sourceName: string | undefined;
  onSave: (key: string, value: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [editValue, setEditValue] = useState('');

  const displayValue =
    value !== null && value !== undefined ? String(value) : '—';

  const startEdit = () => {
    setEditValue(displayValue === '—' ? '' : displayValue);
    setEditing(true);
  };

  const saveEdit = () => {
    onSave(fieldKey, editValue);
    setEditing(false);
  };

  if (editing) {
    return (
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          className="flex-1 px-2 py-1 text-sm border border-amber-300 rounded focus:outline-none focus:ring-2 focus:ring-amber-500"
          autoFocus
          onKeyDown={(e) => {
            if (e.key === 'Enter') saveEdit();
            if (e.key === 'Escape') setEditing(false);
          }}
        />
        <button
          onClick={saveEdit}
          className="p-1 text-green-600 hover:text-green-700"
        >
          <Check className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => setEditing(false)}
          className="p-1 text-slate-400 hover:text-slate-600"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-slate-900 font-mono truncate max-w-[240px]">
        {displayValue}
      </span>
      {confidenceBadge(confidence)}
      {sourceName && (
        <span
          className="inline-flex items-center gap-0.5 text-xs text-slate-400 hover:text-slate-600 cursor-help"
          title={`From: ${sourceName}`}
        >
          <FileText className="w-3 h-3" />
        </span>
      )}
      <button
        onClick={startEdit}
        className="p-1 text-slate-400 hover:text-amber-600 transition-colors"
        title="Edit"
      >
        <Pencil className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Field table section renderer                                      */
/* ------------------------------------------------------------------ */

function FieldSection({
  label,
  entries,
  confidenceMap,
  sourceMap,
  formType,
  onFieldUpdate,
}: {
  label: string;
  entries: [string, unknown][];
  confidenceMap: Record<string, number>;
  sourceMap: Record<string, string>;
  formType: '125' | '140';
  onFieldUpdate: (form: '125' | '140', key: string, value: string) => void;
}) {
  return (
    <div>
      <div className="px-4 py-2 bg-slate-50/50 border-b border-slate-100">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
          {label}
        </p>
      </div>
      <table className="w-full">
        <tbody className="divide-y divide-slate-100">
          {entries.map(([key, value]) => (
            <tr key={key} className="hover:bg-slate-50">
              <td className="px-4 py-2.5 text-sm font-medium text-slate-700 w-1/3">
                {formatFieldLabel(key)}
              </td>
              <td className="px-4 py-2.5">
                <EditableField
                  fieldKey={key}
                  value={
                    typeof value === 'object'
                      ? JSON.stringify(value)
                      : value
                  }
                  confidence={confidenceMap[key]}
                  sourceName={sourceMap[key]}
                  onSave={(k, v) => onFieldUpdate(formType, k, v)}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main component                                                    */
/* ------------------------------------------------------------------ */

interface AcordFormViewProps {
  acord125Fields: Record<string, unknown>;
  acord140Fields: Record<string, unknown>;
  confidenceMap: Record<string, number>;
  sourceMap?: Record<string, string>;
  onFieldUpdate: (form: '125' | '140', key: string, value: string) => void;
}

export default function AcordFormView({
  acord125Fields,
  acord140Fields,
  confidenceMap,
  sourceMap = {},
  onFieldUpdate,
}: AcordFormViewProps) {
  const acord125Sections = groupFieldsBySection(
    acord125Fields,
    ACORD_125_SECTIONS,
  );
  const acord140Entries = Object.entries(acord140Fields ?? {});
  const locationGroups = groupAcord140ByLocation(acord140Fields);

  if (acord125Sections.length === 0 && acord140Entries.length === 0) {
    return (
      <div className="text-center py-8 text-slate-400">
        <p className="text-sm">
          No ACORD fields extracted yet. Upload documents and click
          &quot;Extract ACORD Fields&quot; in Step 1.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* ACORD 125 — Commercial Lines Application */}
      {acord125Sections.length > 0 && (
        <div className="border border-slate-200 rounded-lg overflow-hidden">
          <div className="px-4 py-3 bg-slate-50 border-b border-slate-200">
            <h4 className="text-sm font-semibold text-slate-900">
              ACORD 125 — Commercial Lines Application
            </h4>
          </div>
          {acord125Sections.map((section) => (
            <FieldSection
              key={section.id}
              label={section.label}
              entries={section.entries}
              confidenceMap={confidenceMap}
              sourceMap={sourceMap}
              formType="125"
              onFieldUpdate={onFieldUpdate}
            />
          ))}
        </div>
      )}

      {/* ACORD 140 — Property Section */}
      {acord140Entries.length > 0 && (
        <div className="border border-slate-200 rounded-lg overflow-hidden">
          <div className="px-4 py-3 bg-slate-50 border-b border-slate-200">
            <h4 className="text-sm font-semibold text-slate-900">
              ACORD 140 — Property Section
            </h4>
          </div>
          {locationGroups.length > 0 ? (
            locationGroups.map((group) => (
              <FieldSection
                key={group.label}
                label={group.label}
                entries={group.entries}
                confidenceMap={confidenceMap}
                sourceMap={sourceMap}
                formType="140"
                onFieldUpdate={onFieldUpdate}
              />
            ))
          ) : (
            <table className="w-full">
              <tbody className="divide-y divide-slate-100">
                {acord140Entries.map(([key, value]) => (
                  <tr key={key} className="hover:bg-slate-50">
                    <td className="px-4 py-2.5 text-sm font-medium text-slate-700 w-1/3">
                      {formatFieldLabel(key)}
                    </td>
                    <td className="px-4 py-2.5">
                      <EditableField
                        fieldKey={key}
                        value={
                          typeof value === 'object'
                            ? JSON.stringify(value)
                            : value
                        }
                        confidence={confidenceMap[key]}
                        sourceName={sourceMap[key]}
                        onSave={(k, v) => onFieldUpdate('140', k, v)}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
