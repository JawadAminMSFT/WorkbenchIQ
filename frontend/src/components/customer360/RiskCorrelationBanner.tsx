'use client';

import {
  AlertTriangle,
  Info,
  AlertOctagon,
  ClipboardList,
  Stethoscope,
  Car,
  Home,
} from 'lucide-react';
import type { RiskCorrelation } from '@/lib/customer360-types';
import clsx from 'clsx';

interface RiskCorrelationBannerProps {
  correlations: RiskCorrelation[];
}

const SEVERITY_CONFIG = {
  info: {
    icon: Info,
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    iconColor: 'text-blue-500',
    titleColor: 'text-blue-800',
    textColor: 'text-blue-700',
  },
  warning: {
    icon: AlertTriangle,
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    iconColor: 'text-amber-500',
    titleColor: 'text-amber-800',
    textColor: 'text-amber-700',
  },
  critical: {
    icon: AlertOctagon,
    bg: 'bg-rose-50',
    border: 'border-rose-200',
    iconColor: 'text-rose-500',
    titleColor: 'text-rose-800',
    textColor: 'text-rose-700',
  },
};

const PERSONA_ICONS: Record<string, typeof ClipboardList> = {
  underwriting: ClipboardList,
  life_health_claims: Stethoscope,
  automotive_claims: Car,
  mortgage_underwriting: Home,
};

const PERSONA_LABELS: Record<string, string> = {
  underwriting: 'Underwriting',
  life_health_claims: 'Health Claims',
  automotive_claims: 'Auto Claims',
  mortgage_underwriting: 'Mortgage',
};

export default function RiskCorrelationBanner({ correlations }: RiskCorrelationBannerProps) {
  if (correlations.length === 0) return null;

  // Sort: critical first, then warning, then info
  const sorted = [...correlations].sort((a, b) => {
    const order = { critical: 0, warning: 1, info: 2 };
    return (order[a.severity] ?? 2) - (order[b.severity] ?? 2);
  });

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
        <AlertTriangle className="w-5 h-5 text-amber-500" />
        Cross-Persona Risk Insights
      </h2>

      {sorted.map((correlation, idx) => {
        const config = SEVERITY_CONFIG[correlation.severity] || SEVERITY_CONFIG.info;
        const SeverityIcon = config.icon;

        return (
          <div
            key={idx}
            className={clsx('rounded-lg border p-4', config.bg, config.border)}
          >
            <div className="flex items-start gap-3">
              <SeverityIcon className={clsx('w-5 h-5 mt-0.5 shrink-0', config.iconColor)} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h3 className={clsx('text-sm font-semibold', config.titleColor)}>
                    {correlation.title}
                  </h3>
                  <span className={clsx(
                    'text-xs font-medium px-2 py-0.5 rounded-full',
                    correlation.severity === 'critical' ? 'bg-rose-100 text-rose-700' :
                    correlation.severity === 'warning' ? 'bg-amber-100 text-amber-700' :
                    'bg-blue-100 text-blue-700'
                  )}>
                    {correlation.severity.charAt(0).toUpperCase() + correlation.severity.slice(1)}
                  </span>
                </div>
                <p className={clsx('text-sm mt-1 leading-relaxed', config.textColor)}>
                  {correlation.description}
                </p>
                {/* Persona tags */}
                <div className="flex items-center gap-2 mt-3">
                  <span className="text-xs text-slate-400">Involves:</span>
                  {correlation.personas_involved.map(persona => {
                    const Icon = PERSONA_ICONS[persona] || ClipboardList;
                    return (
                      <span
                        key={persona}
                        className="inline-flex items-center gap-1 px-2 py-0.5 bg-white/70 rounded-full text-xs font-medium text-slate-600 border border-white/50"
                      >
                        <Icon className="w-3 h-3" />
                        {PERSONA_LABELS[persona] || persona}
                      </span>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
