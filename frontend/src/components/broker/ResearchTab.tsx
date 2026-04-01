'use client';

import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  Search, FileText, AlertTriangle, ExternalLink,
  Loader2, RefreshCw, Building2, DollarSign, Shield,
  Newspaper, Upload, Clock, X, CheckCircle, Plus,
  Edit3, Save, Info,
} from 'lucide-react';
import { runClientResearch, updateResearchBrief } from '../../lib/broker-api';
import type { Client, ResearchBrief } from '../../lib/broker-types';

interface ResearchTabProps {
  clientId: string;
  client: Client | null;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fallback(value: string | number | null | undefined, placeholder = '—'): string {
  if (value === null || value === undefined || value === '') return placeholder;
  return String(value);
}

// ---------------------------------------------------------------------------
// Legacy markdown parser (backward compatibility)
// ---------------------------------------------------------------------------
interface BriefSection { title: string; content: string; }

function parseBrief(markdown: string): BriefSection[] {
  const sections: BriefSection[] = [];
  const lines = markdown.split('\n');
  let currentTitle = '';
  let currentContent: string[] = [];
  for (const line of lines) {
    if (line.startsWith('## ')) {
      if (currentTitle) sections.push({ title: currentTitle, content: currentContent.join('\n').trim() });
      currentTitle = line.replace('## ', '');
      currentContent = [];
    } else if (!line.startsWith('# ')) {
      currentContent.push(line);
    }
  }
  if (currentTitle) sections.push({ title: currentTitle, content: currentContent.join('\n').trim() });
  return sections;
}

function isLegacyBrief(data: ResearchBrief): boolean {
  return typeof data.brief === 'string' && data.brief.length > 0 && !data.business_description;
}

// ---------------------------------------------------------------------------
// Badge / indicator helpers
// ---------------------------------------------------------------------------

function ConfidenceBadge({ level }: { level?: string }) {
  const l = (level ?? '').toLowerCase();
  const cls = l === 'high' ? 'bg-green-100 text-green-700' : l === 'low' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700';
  return <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${cls}`}>{fallback(level, 'N/A')}</span>;
}

function RevenueTrend({ trend }: { trend?: string }) {
  const t = (trend ?? '').toLowerCase();
  const arrow = t === 'growing' ? '↗' : t === 'declining' ? '↘' : '→';
  const cls = t === 'growing' ? 'text-green-600' : t === 'declining' ? 'text-red-600' : 'text-slate-600';
  return <span className={`font-medium ${cls}`}>{arrow} {fallback(trend, 'N/A')}</span>;
}

function LossFrequency({ level }: { level?: string }) {
  const l = (level ?? '').toLowerCase();
  const filled = l === 'high' ? 3 : l === 'moderate' ? 2 : 1;
  const cls = l === 'high' ? 'text-red-500' : l === 'moderate' ? 'text-amber-500' : 'text-green-500';
  return (
    <span className={`font-medium ${cls}`}>
      {'●'.repeat(filled)}{'○'.repeat(3 - filled)} {fallback(level, 'N/A')}
    </span>
  );
}

function PriorityBadge({ priority }: { priority?: string }) {
  const p = (priority ?? '').toLowerCase();
  const cls =
    p === 'primary' ? 'bg-amber-100 text-amber-700' :
    p === 'required' ? 'bg-blue-100 text-blue-700' :
    p === 'recommended' ? 'bg-green-100 text-green-700' :
    'bg-slate-100 text-slate-600';
  return <span className={`text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap ${cls}`}>{fallback(priority, 'N/A')}</span>;
}

function RatingBadge({ rating }: { rating?: string }) {
  const r = (rating ?? '').toUpperCase();
  const cls =
    r.startsWith('A++') ? 'bg-green-100 text-green-700' :
    r.startsWith('A+') ? 'bg-green-100 text-green-700' :
    r.startsWith('A') ? 'bg-yellow-100 text-yellow-700' :
    r.startsWith('B') ? 'bg-orange-100 text-orange-700' :
    'bg-slate-100 text-slate-600';
  return <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${cls}`}>{fallback(rating, 'N/R')}</span>;
}

function AppetiteBadge({ appetite }: { appetite?: string }) {
  const a = (appetite ?? '').toLowerCase();
  const cls =
    a === 'strong' ? 'text-green-600' :
    a === 'good' ? 'text-blue-600' :
    a === 'moderate' ? 'text-amber-600' :
    'text-slate-500';
  return <span className={`text-xs font-medium ${cls}`}>{fallback(appetite, 'N/A')}</span>;
}

function PerilPill({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center text-xs font-medium bg-slate-100 text-slate-600 px-2.5 py-1 rounded-full">
      {label}
    </span>
  );
}

function DataSourcePill({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center gap-1 text-xs font-medium bg-amber-50 text-amber-700 px-2.5 py-1 rounded-full">
      {label}
    </span>
  );
}

function FieldConfidenceIndicator({ level }: { level?: string }) {
  if (!level || level.toLowerCase() !== 'low') return null;
  return (
    <span className="inline-flex items-center gap-1 text-xs text-amber-600 ml-2" title="Low confidence — limited public data">
      <Info className="w-3 h-3" />
      <span className="text-[10px]">Low confidence</span>
    </span>
  );
}

function CitationTypePill({ type }: { type: string }) {
  const cls =
    type === 'SEC Filing' ? 'bg-blue-100 text-blue-700' :
    type === 'News' ? 'bg-purple-100 text-purple-700' :
    type === 'Government' ? 'bg-green-100 text-green-700' :
    type === 'AM Best' ? 'bg-amber-100 text-amber-700' :
    type === 'Rating Agency' ? 'bg-indigo-100 text-indigo-700' :
    type === 'Academic' ? 'bg-teal-100 text-teal-700' :
    type === 'Financial Report' ? 'bg-cyan-100 text-cyan-700' :
    'bg-slate-100 text-slate-600';
  return <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${cls}`}>{type}</span>;
}

// ---------------------------------------------------------------------------
// Card wrapper
// ---------------------------------------------------------------------------

function CardHeader({ icon: Icon, title }: { icon: React.ComponentType<React.SVGProps<SVGSVGElement>>; title: string }) {
  return (
    <div className="px-5 py-3 bg-amber-50 border-b border-amber-100 flex items-center gap-2">
      <Icon className="w-4 h-4 text-amber-600" />
      <h3 className="font-semibold text-slate-800">{title}</h3>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Structured cards
// ---------------------------------------------------------------------------

function BusinessOverviewCard({ data, editing, editData, onEditChange }: { data: ResearchBrief; editing?: boolean; editData?: Partial<ResearchBrief>; onEditChange?: (field: string, value: unknown) => void }) {
  const fc = data.field_confidence ?? {};
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <CardHeader icon={Building2} title="Business Overview" />
      <div className="p-5 text-sm text-slate-700 space-y-3">
        {editing && onEditChange ? (
          <textarea
            className="w-full border border-slate-200 rounded-lg p-2 text-sm resize-y min-h-[80px]"
            value={editData?.business_description ?? data.business_description ?? ''}
            onChange={(e) => onEditChange('business_description', e.target.value)}
          />
        ) : (
          <p>{fallback(data.business_description, 'No description available.')}</p>
        )}
        <FieldConfidenceIndicator level={fc.business_description} />
        <div className="grid grid-cols-2 gap-x-6 gap-y-2">
          <div><span className="font-medium text-slate-500">HQ:</span> {fallback(data.headquarters)}</div>
          <div><span className="font-medium text-slate-500">Founded:</span> {fallback(data.year_founded)}</div>
          <div><span className="font-medium text-slate-500">Employees:</span> {fallback(data.employee_count)}</div>
          <div><span className="font-medium text-slate-500">Type:</span> {fallback(data.ownership_type)}</div>
        </div>
        {(data.key_operations?.length ?? 0) > 0 && (
          <div>
            <span className="font-medium text-slate-500">Key Operations:</span>
            <ul className="mt-1 space-y-1 pl-1">
              {data.key_operations.map((op, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-amber-400 shrink-0" />
                  <span>{op}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

function FinancialSummaryCard({ data, editing, editData, onEditChange }: { data: ResearchBrief; editing?: boolean; editData?: Partial<ResearchBrief>; onEditChange?: (field: string, value: unknown) => void }) {
  const fc = data.field_confidence ?? {};
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <CardHeader icon={DollarSign} title="Financial Summary" />
      <div className="p-5 text-sm text-slate-700 space-y-3">
        <div className="grid grid-cols-1 gap-y-2">
          <div><span className="font-medium text-slate-500">Revenue:</span> {fallback(data.annual_revenue)}</div>
          <div><span className="font-medium text-slate-500">Trend:</span> <RevenueTrend trend={data.revenue_trend} /></div>
          <div><span className="font-medium text-slate-500">Credit Rating:</span> {fallback(data.credit_rating)}</div>
        </div>
        <FieldConfidenceIndicator level={fc.financial_highlights} />
        {(data.financial_highlights?.length ?? 0) > 0 && (
          <div>
            <span className="font-medium text-slate-500">Highlights:</span>
            {editing && onEditChange ? (
              <textarea
                className="w-full border border-slate-200 rounded-lg p-2 text-sm resize-y min-h-[80px] mt-1"
                value={(editData?.financial_highlights ?? data.financial_highlights ?? []).join('\n')}
                onChange={(e) => onEditChange('financial_highlights', e.target.value.split('\n').filter(Boolean))}
              />
            ) : (
              <ul className="mt-1 space-y-1 pl-1">
                {data.financial_highlights.map((h, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-amber-400 shrink-0" />
                    <span>{h}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function RiskProfileCard({ data, editing, editData, onEditChange }: { data: ResearchBrief; editing?: boolean; editData?: Partial<ResearchBrief>; onEditChange?: (field: string, value: unknown) => void }) {
  const fc = data.field_confidence ?? {};
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden col-span-full">
      <CardHeader icon={Shield} title="Industry Risk Profile" />
      <div className="p-5 text-sm text-slate-700 space-y-3">
        <div className="flex flex-wrap gap-x-8 gap-y-2">
          <div>
            <span className="font-medium text-slate-500">Sector:</span>{' '}
            {fallback(data.industry_sector)}
            {data.naics_code ? ` (NAICS ${data.naics_code})` : ''}
          </div>
          <div>
            <span className="font-medium text-slate-500">Loss Frequency:</span>{' '}
            <LossFrequency level={data.loss_frequency} />
          </div>
        </div>

        {(data.common_perils?.length ?? 0) > 0 && (
          <div>
            <span className="font-medium text-slate-500 mr-2">Common Perils:</span>
            <div className="flex flex-wrap gap-2 mt-1">
              {data.common_perils.map((p, i) => <PerilPill key={i} label={p} />)}
            </div>
          </div>
        )}

        {(data.risk_factors?.length ?? 0) > 0 && (
          <div>
            <span className="font-medium text-slate-500">Risk Factors:</span>
            <FieldConfidenceIndicator level={fc.risk_factors} />
            {editing && onEditChange ? (
              <textarea
                className="w-full border border-slate-200 rounded-lg p-2 text-sm resize-y min-h-[60px] mt-1"
                value={(editData?.risk_factors ?? data.risk_factors ?? []).join('\n')}
                onChange={(e) => onEditChange('risk_factors', e.target.value.split('\n').filter(Boolean))}
              />
            ) : (
              <ul className="mt-1 space-y-1">
                {data.risk_factors.map((rf, i) => (
                  <li key={i} className="flex items-start gap-2 text-amber-700">
                    <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
                    <span className="text-slate-700">{rf}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function InsuranceNeedsCard({ data }: { data: ResearchBrief }) {
  const needs = data.insurance_needs ?? [];
  const fc = data.field_confidence ?? {};
  if (needs.length === 0) return null;
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden col-span-full">
      <div className="px-5 py-3 bg-amber-50 border-b border-amber-100 flex items-center gap-2">
        <FileText className="w-4 h-4 text-amber-600" />
        <h3 className="font-semibold text-slate-800">Insurance Needs Assessment</h3>
        <FieldConfidenceIndicator level={fc.insurance_needs} />
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              <th className="px-5 py-2.5 text-left font-semibold text-slate-700">Line</th>
              <th className="px-5 py-2.5 text-left font-semibold text-slate-700">Priority</th>
              <th className="px-5 py-2.5 text-left font-semibold text-slate-700">Est. Premium</th>
              <th className="px-5 py-2.5 text-left font-semibold text-slate-700">Rationale</th>
            </tr>
          </thead>
          <tbody>
            {needs.map((n, i) => (
              <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-slate-50'}>
                <td className="px-5 py-3 font-medium text-slate-800 whitespace-nowrap">{fallback(n.line)}</td>
                <td className="px-5 py-3"><PriorityBadge priority={n.priority} /></td>
                <td className="px-5 py-3 text-slate-600 whitespace-nowrap">{fallback(n.estimated_premium)}</td>
                <td className="px-5 py-3 text-slate-600">{fallback(n.rationale)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function CarrierMatchesCard({ data }: { data: ResearchBrief }) {
  const carriers = data.carrier_matches ?? [];
  const fc = data.field_confidence ?? {};
  if (carriers.length === 0) return null;
  const hasMetrics = carriers.some(c => c.fsr || c.icr || c.outlook || c.combined_ratio);
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-5 py-3 bg-amber-50 border-b border-amber-100 flex items-center gap-2">
        <Building2 className="w-4 h-4 text-amber-600" />
        <h3 className="font-semibold text-slate-800">Carrier Appetite</h3>
        <FieldConfidenceIndicator level={fc.carrier_matches} />
      </div>
      <div className="p-5 space-y-3">
        {carriers.map((c, i) => (
          <div key={i} className="text-sm border-b border-slate-100 pb-3 last:border-b-0 last:pb-0">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-800">{fallback(c.carrier)}</span>
              <RatingBadge rating={c.rating} />
              <AppetiteBadge appetite={c.appetite} />
            </div>
            <p className="text-slate-500 mt-0.5">{fallback(c.rationale)}</p>
            {hasMetrics && (c.fsr || c.icr || c.outlook || c.combined_ratio || c.balance_sheet_strength || c.operating_performance || c.nwp_to_surplus_ratio) && (
              <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-slate-500">
                {c.fsr && <div><span className="font-medium">FSR:</span> {c.fsr}</div>}
                {c.icr && <div><span className="font-medium">ICR:</span> {c.icr}</div>}
                {c.outlook && <div><span className="font-medium">Outlook:</span> {c.outlook}</div>}
                {c.balance_sheet_strength && <div><span className="font-medium">Balance Sheet:</span> {c.balance_sheet_strength}</div>}
                {c.operating_performance && <div><span className="font-medium">Operating Perf:</span> {c.operating_performance}</div>}
                {c.combined_ratio && <div><span className="font-medium">Combined Ratio:</span> {c.combined_ratio}</div>}
                {c.nwp_to_surplus_ratio && <div><span className="font-medium">NWP/Surplus:</span> {c.nwp_to_surplus_ratio}</div>}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function RecentNewsCard({ data }: { data: ResearchBrief }) {
  const news = data.recent_news ?? [];
  const fc = data.field_confidence ?? {};
  if (news.length === 0) return null;
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-5 py-3 bg-amber-50 border-b border-amber-100 flex items-center gap-2">
        <Newspaper className="w-4 h-4 text-amber-600" />
        <h3 className="font-semibold text-slate-800">Recent News</h3>
        <FieldConfidenceIndicator level={fc.recent_news} />
      </div>
      <div className="p-5 space-y-3">
        {news.map((n, i) => (
          <div key={i} className="text-sm">
            <span className="text-slate-400 text-xs mr-2">{fallback(n.date)}</span>
            <span className="text-slate-800">{fallback(n.headline)}</span>
            {n.source && (
              <span className="text-slate-400 text-xs ml-1">— {n.source}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function CitationsCard({ citations, citationTypes }: { citations?: string[]; citationTypes?: Record<string, string> }) {
  if (!citations?.length) return null;
  const types = citationTypes ?? {};
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 col-span-full space-y-2">
      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Citations</p>
      <div className="flex flex-wrap gap-3">
        {citations.map((src, i) => {
          const isUrl = src.startsWith('http');
          const displayText = isUrl ? new URL(src).hostname.replace('www.', '') : src;
          const citationType = isUrl ? types[src] : undefined;
          return isUrl ? (
            <a key={i} href={src} target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs text-amber-700 bg-amber-50 hover:bg-amber-100 px-2.5 py-1 rounded-full transition-colors">
              <ExternalLink className="w-3 h-3" />
              {displayText}
              {citationType && <CitationTypePill type={citationType} />}
            </a>
          ) : (
            <span key={i} className="inline-flex items-center gap-1.5 text-xs text-slate-600 bg-slate-50 px-2.5 py-1 rounded-full">
              {src}
            </span>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Legacy section card (backward compat for markdown briefs)
// ---------------------------------------------------------------------------
const SECTION_ICONS: Record<string, React.ComponentType<React.SVGProps<SVGSVGElement>>> = {
  'Business': Building2,
  'Financial': DollarSign,
  'Risk': Shield,
  'Insurance': FileText,
  'Carrier': Building2,
  'News': Newspaper,
};

function iconForSection(title: string) {
  for (const [key, Icon] of Object.entries(SECTION_ICONS)) {
    if (title.toLowerCase().includes(key.toLowerCase())) return Icon;
  }
  return FileText;
}

function LegacySectionCard({ section, fullWidth }: { section: BriefSection; fullWidth?: boolean }) {
  const Icon = iconForSection(section.title);
  return (
    <div className={`bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden ${fullWidth ? 'col-span-full' : ''}`}>
      <CardHeader icon={Icon} title={section.title} />
      <div className="p-5 text-sm text-slate-700 whitespace-pre-line">{section.content || <span className="text-slate-400 italic">No data available</span>}</div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Upload area component
// ---------------------------------------------------------------------------

interface UploadedFile {
  id: string;
  name: string;
}

function DocumentUploadArea({
  files,
  onFilesSelected,
  onRemoveFile,
}: {
  files: UploadedFile[];
  onFilesSelected: (newFiles: File[]) => void;
  onRemoveFile: (id: string) => void;
}) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const dropped = Array.from(e.dataTransfer.files);
    if (dropped.length > 0) onFilesSelected(dropped);
  }, [onFilesSelected]);

  const handleDragOver = useCallback((e: React.DragEvent) => { e.preventDefault(); setDragOver(true); }, []);
  const handleDragLeave = useCallback(() => setDragOver(false), []);

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <CardHeader icon={Upload} title="Upload Documents" />
      <div className="p-5 space-y-3">
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
            dragOver ? 'border-amber-400 bg-amber-50' : 'border-slate-200 hover:border-slate-300'
          }`}
        >
          <Upload className="w-8 h-8 text-slate-300 mx-auto mb-2" />
          <p className="text-sm text-slate-500">
            Drop AM Best reports, annual reports, or other docs here to include in research.
          </p>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="mt-2 text-xs font-medium text-amber-600 hover:text-amber-700"
          >
            Browse
          </button>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt"
            className="hidden"
            onChange={(e) => {
              const selected = Array.from(e.target.files ?? []);
              if (selected.length > 0) onFilesSelected(selected);
              e.target.value = '';
            }}
          />
        </div>

        {files.length > 0 && (
          <div className="space-y-1">
            {files.map((f) => (
              <div key={f.id} className="flex items-center gap-2 text-sm text-slate-700">
                <CheckCircle className="w-4 h-4 text-green-500 shrink-0" />
                <span className="flex-1 truncate">{f.name}</span>
                <button onClick={() => onRemoveFile(f.id)} className="text-slate-400 hover:text-red-500">
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
export default function ResearchTab({ clientId, client }: ResearchTabProps) {
  const [brief, setBrief] = useState<ResearchBrief | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [researchedAt, setResearchedAt] = useState<Date | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState<Partial<ResearchBrief>>({});
  const [saving, setSaving] = useState(false);
  const [history, setHistory] = useState<Array<{
    id: string;
    generated_at: string;
    company_name: string;
    confidence_level: string;
    data_sources: string[];
    brief: ResearchBrief;
  }>>([]);
  const [selectedHistoryId, setSelectedHistoryId] = useState<string | null>(null);
  const [historyLoaded, setHistoryLoaded] = useState(false);

  // Load research history on mount
  const loadHistory = useCallback(async () => {
    try {
      const { getResearchHistory } = await import('../../lib/broker-api');
      const data = await getResearchHistory(clientId);
      setHistory(data);
      setHistoryLoaded(true);
    } catch {
      setHistoryLoaded(true);
    }
  }, [clientId]);

  // Load history on mount
  React.useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const hasBrief = brief !== null;

  const handleFilesSelected = useCallback((newFiles: File[]) => {
    const mapped: UploadedFile[] = newFiles.map((f) => ({
      id: `${f.name}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      name: f.name,
    }));
    setUploadedFiles((prev) => [...prev, ...mapped]);
  }, []);

  const handleRemoveFile = useCallback((id: string) => {
    setUploadedFiles((prev) => prev.filter((f) => f.id !== id));
  }, []);

  const handleRunResearch = useCallback(async () => {
    if (!client?.name) return;
    setLoading(true);
    setError(null);
    setBrief(null);
    setSelectedHistoryId(null);
    try {
      const docIds = uploadedFiles.map((f) => f.id);
      const data = await runClientResearch(clientId, client.name, docIds.length > 0 ? docIds : undefined);
      setBrief(data);
      setResearchedAt(new Date());
      // Refresh history to include the new entry
      await loadHistory();
    } catch (err) {
      console.error('Research failed:', err);
      setError(err instanceof Error ? err.message : 'Research request failed');
    } finally {
      setLoading(false);
    }
  }, [clientId, client?.name, uploadedFiles, loadHistory]);

  const handleSelectHistory = (entry: typeof history[0]) => {
    setSelectedHistoryId(entry.id);
    setBrief(entry.brief);
    setResearchedAt(new Date(entry.generated_at));
    setError(null);
  };

  const handleNewResearch = () => {
    setSelectedHistoryId(null);
    setBrief(null);
    setResearchedAt(null);
    setError(null);
    setEditing(false);
    setEditData({});
  };

  const handleEditToggle = () => {
    if (editing) {
      setEditing(false);
      setEditData({});
    } else {
      setEditing(true);
      setEditData({});
    }
  };

  const handleEditChange = useCallback((field: string, value: unknown) => {
    setEditData(prev => ({ ...prev, [field]: value }));
  }, []);

  const handleSaveEdits = useCallback(async () => {
    if (!brief || Object.keys(editData).length === 0) return;
    setSaving(true);
    try {
      const updated = await updateResearchBrief(clientId, editData);
      setBrief(updated as ResearchBrief);
      setEditing(false);
      setEditData({});
    } catch (err) {
      console.error('Save failed:', err);
      setError(err instanceof Error ? err.message : 'Failed to save edits');
    } finally {
      setSaving(false);
    }
  }, [clientId, brief, editData]);

  // Determine whether response is legacy markdown or new structured JSON
  const legacy = brief ? isLegacyBrief(brief) : false;
  const legacySections = brief && legacy ? parseBrief(brief.brief!) : [];

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString(undefined, {
        month: 'short', day: 'numeric', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
      });
    } catch { return iso; }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex gap-6">
        {/* History sidebar */}
        {historyLoaded && history.length > 0 && (
          <div className="w-64 flex-shrink-0">
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="px-4 py-3 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">History</p>
                <button
                  onClick={handleNewResearch}
                  className="flex items-center gap-1 text-xs font-medium text-amber-600 hover:text-amber-700 transition-colors"
                >
                  <Plus className="w-3 h-3" />
                  New
                </button>
              </div>
              <div className="divide-y divide-slate-100 max-h-[600px] overflow-y-auto">
                {history.map((entry) => (
                  <button
                    key={entry.id}
                    onClick={() => handleSelectHistory(entry)}
                    className={`w-full text-left px-4 py-3 hover:bg-amber-50 transition-colors ${
                      selectedHistoryId === entry.id
                        ? 'bg-amber-50 border-l-2 border-l-amber-500'
                        : ''
                    }`}
                  >
                    <p className="text-xs font-medium text-slate-700 truncate">
                      {entry.company_name || 'Research Brief'}
                    </p>
                    <p className="text-[10px] text-slate-400 mt-0.5 flex items-center gap-1">
                      <Clock className="w-2.5 h-2.5" />
                      {formatDate(entry.generated_at)}
                    </p>
                    <div className="flex items-center gap-1.5 mt-1">
                      <ConfidenceBadge level={entry.confidence_level} />
                      {entry.data_sources?.includes('Bing Web Search') && (
                        <span className="text-[9px] font-medium text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">Web</span>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Main content */}
        <div className="flex-1 space-y-6 min-w-0">
      {/* Header */}
      <div className="bg-white rounded-lg border border-slate-200 p-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Search className="w-5 h-5 text-amber-600" />
            <div>
              <h3 className="text-base font-semibold text-slate-900">
                Research Brief{brief?.company_name ? `: ${brief.company_name}` : ''}
              </h3>
              <div className="flex items-center gap-3 mt-0.5">
                {researchedAt && (
                  <span className="flex items-center gap-1 text-xs text-slate-400">
                    <Clock className="w-3 h-3" />
                    Last updated {researchedAt.toLocaleString()}
                  </span>
                )}
                {brief && !legacy && (brief.data_sources?.length ?? 0) > 0 && (
                  <span className="flex items-center gap-1.5 text-xs text-slate-400">
                    Sources: {brief.data_sources!.map((s, i) => <DataSourcePill key={i} label={s} />)}
                  </span>
                )}
                {brief && !legacy && brief.confidence_level && (
                  <span className="flex items-center gap-1.5 text-xs text-slate-400">
                    Confidence: <ConfidenceBadge level={brief.confidence_level} />
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {hasBrief && !legacy && !loading && (
              editing ? (
                <>
                  <button
                    onClick={handleSaveEdits}
                    disabled={saving || Object.keys(editData).length === 0}
                    className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 disabled:opacity-50 rounded-lg transition-colors"
                  >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                    {saving ? 'Saving…' : 'Save'}
                  </button>
                  <button
                    onClick={handleEditToggle}
                    className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                  >
                    <X className="w-4 h-4" />
                    Cancel
                  </button>
                </>
              ) : (
                <button
                  onClick={handleEditToggle}
                  className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                >
                  <Edit3 className="w-4 h-4" />
                  Edit
                </button>
              )
            )}
            <button
              onClick={handleRunResearch}
              disabled={loading || !client?.name}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 disabled:opacity-50 rounded-lg transition-colors"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : hasBrief ? (
                <RefreshCw className="w-4 h-4" />
              ) : (
                <Search className="w-4 h-4" />
              )}
              {loading ? 'Researching…' : hasBrief ? 'Rerun Research' : uploadedFiles.length > 0 ? `Run Research (with ${uploadedFiles.length} doc${uploadedFiles.length > 1 ? 's' : ''})` : 'Run Research'}
            </button>
          </div>
        </div>
      </div>

      {/* Upload documents area */}
      <DocumentUploadArea
        files={uploadedFiles}
        onFilesSelected={handleFilesSelected}
        onRemoveFile={handleRemoveFile}
      />

      {/* Loading */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-20 text-amber-600">
          <Loader2 className="w-10 h-10 animate-spin mb-4" />
          <p className="text-sm font-medium">Generating research brief…</p>
          <p className="text-xs text-slate-400 mt-1">This may take a minute.</p>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="flex flex-col items-center justify-center py-16 text-red-600">
          <AlertTriangle className="w-12 h-12 mb-4" />
          <p className="text-lg font-medium">{error}</p>
          <button
            onClick={handleRunResearch}
            className="mt-4 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700"
          >
            Retry
          </button>
        </div>
      )}

      {/* New structured research brief */}
      {brief && !loading && !legacy && (
        <div className="space-y-5">
          {/* Row 1: Business Overview + Financial Summary */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <BusinessOverviewCard data={brief} editing={editing} editData={editData} onEditChange={handleEditChange} />
            <FinancialSummaryCard data={brief} editing={editing} editData={editData} onEditChange={handleEditChange} />
          </div>

          {/* Row 2: Industry Risk Profile (full width) */}
          <RiskProfileCard data={brief} editing={editing} editData={editData} onEditChange={handleEditChange} />

          {/* Row 3: Insurance Needs (full width table) */}
          <InsuranceNeedsCard data={brief} />

          {/* Row 4: Carrier Matches + Recent News */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <CarrierMatchesCard data={brief} />
            <RecentNewsCard data={brief} />
          </div>

          {/* Citations */}
          <CitationsCard citations={brief.citations} citationTypes={brief.citation_types} />
        </div>
      )}

      {/* Legacy markdown brief (backward compatibility) */}
      {brief && !loading && legacy && (
        <div className="space-y-6">
          <h2 className="text-lg font-semibold text-slate-900">{brief.company_name}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {legacySections.map((section, idx) => (
              <LegacySectionCard key={idx} section={section} fullWidth={idx === 0} />
            ))}
          </div>
          {(brief.sources?.length ?? 0) > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-2">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Sources</p>
              <div className="flex flex-wrap gap-3">
                {brief.sources?.map((src, i) => (
                  <span key={i} className="inline-flex items-center gap-1.5 text-xs text-amber-700 bg-amber-50 px-2.5 py-1 rounded-full">
                    <ExternalLink className="w-3 h-3" />
                    {src}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {!brief && !loading && !error && (
        <div className="flex flex-col items-center justify-center py-20 text-slate-400">
          <FileText className="w-12 h-12 mb-4" />
          <p className="text-lg">No research brief yet</p>
          <p className="text-sm mt-1">Click Run Research to generate an AI brief for {client?.name ?? 'this client'}.</p>
        </div>
      )}
        </div>{/* end main content */}
      </div>{/* end flex */}
    </div>
  );
}
