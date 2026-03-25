'use client';

import {
  ClipboardList,
  Stethoscope,
  Car,
  Home,
  CheckCircle2,
  Clock,
  AlertTriangle,
  XCircle,
  Search as SearchIcon,
  FileText,
  ArrowRight,
} from 'lucide-react';
import type { CustomerJourneyEvent } from '@/lib/customer360-types';
import clsx from 'clsx';
import Link from 'next/link';

interface CustomerTimelineProps {
  events: CustomerJourneyEvent[];
}

const PERSONA_CONFIG: Record<string, { icon: typeof ClipboardList; color: string; bg: string; border: string; label: string }> = {
  underwriting: { icon: ClipboardList, color: 'text-indigo-700', bg: 'bg-indigo-50', border: 'border-indigo-200', label: 'Life & Health Underwriting' },
  life_health_claims: { icon: Stethoscope, color: 'text-cyan-700', bg: 'bg-cyan-50', border: 'border-cyan-200', label: 'Life & Health Claims' },
  automotive_claims: { icon: Car, color: 'text-red-700', bg: 'bg-red-50', border: 'border-red-200', label: 'Automotive Claims' },
  mortgage_underwriting: { icon: Home, color: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200', label: 'Mortgage Underwriting' },
};

const STATUS_CONFIG: Record<string, { icon: typeof CheckCircle2; color: string; label: string }> = {
  approved: { icon: CheckCircle2, color: 'text-emerald-500', label: 'Approved' },
  completed: { icon: CheckCircle2, color: 'text-emerald-500', label: 'Completed' },
  closed: { icon: CheckCircle2, color: 'text-slate-500', label: 'Closed' },
  conditional: { icon: AlertTriangle, color: 'text-amber-500', label: 'Conditional' },
  referred: { icon: Clock, color: 'text-amber-500', label: 'Referred' },
  pending: { icon: Clock, color: 'text-blue-500', label: 'Pending' },
  in_progress: { icon: Clock, color: 'text-blue-500', label: 'In Progress' },
  investigating: { icon: SearchIcon, color: 'text-orange-500', label: 'Investigating' },
  declined: { icon: XCircle, color: 'text-rose-500', label: 'Declined' },
};

const EVENT_TYPE_ICONS: Record<string, typeof FileText> = {
  application_submitted: FileText,
  claim_filed: FileText,
  underwriting_complete: CheckCircle2,
  claim_resolved: CheckCircle2,
  additional_info_requested: Clock,
  investigation_opened: SearchIcon,
};

export default function CustomerTimeline({ events }: CustomerTimelineProps) {
  if (events.length === 0) {
    return (
      <div className="text-center py-12 text-slate-400">
        <Clock className="w-10 h-10 mx-auto mb-2 opacity-40" />
        <p>No journey events yet.</p>
      </div>
    );
  }

  // Group events by year
  const eventsByYear = events.reduce<Record<string, CustomerJourneyEvent[]>>((acc, event) => {
    const year = event.date.slice(0, 4);
    (acc[year] ??= []).push(event);
    return acc;
  }, {});

  const years = Object.keys(eventsByYear).sort((a, b) => b.localeCompare(a));

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
      <h2 className="text-lg font-semibold text-slate-900 mb-6 flex items-center gap-2">
        <Clock className="w-5 h-5 text-indigo-500" />
        Customer Journey
      </h2>

      <div className="space-y-8">
        {years.map(year => (
          <div key={year}>
            <div className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">{year}</div>
            <div className="relative">
              {/* Vertical line */}
              <div className="absolute left-5 top-0 bottom-0 w-px bg-slate-200" />

              <div className="space-y-4">
                {eventsByYear[year].map((event, idx) => {
                  const personaCfg = PERSONA_CONFIG[event.persona] || PERSONA_CONFIG.underwriting;
                  const statusCfg = STATUS_CONFIG[event.status] || STATUS_CONFIG.pending;
                  const PersonaIcon = personaCfg.icon;
                  const StatusIcon = statusCfg.icon;
                  const EventIcon = EVENT_TYPE_ICONS[event.event_type] || FileText;

                  return (
                    <div key={`${event.application_id}-${event.event_type}-${idx}`} className="relative flex gap-4 pl-0">
                      {/* Timeline dot */}
                      <div className={clsx('w-10 h-10 rounded-full flex items-center justify-center z-10 border-2 border-white shadow-sm', personaCfg.bg)}>
                        <PersonaIcon className={clsx('w-4.5 h-4.5', personaCfg.color)} />
                      </div>

                      {/* Event card */}
                      <Link
                        href={`/?app=${event.application_id}&persona=${mapPersonaToFrontendId(event.persona)}`}
                        className={clsx('flex-1 rounded-lg border p-4 hover:shadow-md transition-shadow block', personaCfg.border, 'bg-white')}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className={clsx('text-xs font-medium px-2 py-0.5 rounded-full', personaCfg.bg, personaCfg.color)}>
                                {personaCfg.label}
                              </span>
                              <span className="text-xs text-slate-400">{formatDate(event.date)}</span>
                            </div>
                            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-1.5">
                              <EventIcon className="w-4 h-4 text-slate-400" />
                              {event.title}
                            </h3>
                            <p className="text-sm text-slate-600 mt-1 leading-relaxed">{event.summary}</p>
                          </div>

                          {/* Status badge */}
                          <div className="flex items-center gap-1 ml-4 shrink-0">
                            <StatusIcon className={clsx('w-4 h-4', statusCfg.color)} />
                            <span className={clsx('text-xs font-medium', statusCfg.color)}>{statusCfg.label}</span>
                          </div>
                        </div>

                        {/* Key metrics */}
                        {Object.keys(event.key_metrics).length > 0 && (
                          <div className="mt-3 pt-3 border-t border-slate-100">
                            <div className="flex flex-wrap gap-x-4 gap-y-1.5">
                              {Object.entries(event.key_metrics).slice(0, 6).map(([key, value]) => (
                                <div key={key} className="text-xs">
                                  <span className="text-slate-400">{formatMetricLabel(key)}:</span>{' '}
                                  <span className="text-slate-700 font-medium">{value}</span>
                                </div>
                              ))}
                              {Object.keys(event.key_metrics).length > 6 && (
                                <span className="text-xs text-slate-400 flex items-center gap-0.5">
                                  +{Object.keys(event.key_metrics).length - 6} more <ArrowRight className="w-3 h-3" />
                                </span>
                              )}
                            </div>
                          </div>
                        )}
                      </Link>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function mapPersonaToFrontendId(persona: string): string {
  if (persona === 'mortgage_underwriting') return 'mortgage';
  return persona;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-CA', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function formatMetricLabel(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase());
}
