'use client';

import {
  Package,
  AlertTriangle,
  ShieldCheck,
  Shield,
  ShieldAlert,
  TrendingUp,
  Calendar,
} from 'lucide-react';
import type { Customer360View } from '@/lib/customer360-types';
import clsx from 'clsx';

interface CustomerJourneyMetricsProps {
  data: Customer360View;
}

export default function CustomerJourneyMetrics({ data }: CustomerJourneyMetricsProps) {
  const { profile, total_products, active_claims, journey_events, risk_correlations } = data;

  const criticalCorrelations = risk_correlations.filter(c => c.severity === 'critical').length;
  const warningCorrelations = risk_correlations.filter(c => c.severity === 'warning').length;

  const riskConfig = {
    low: { icon: ShieldCheck, color: 'text-emerald-600', bg: 'bg-emerald-50', label: 'Low' },
    medium: { icon: Shield, color: 'text-amber-600', bg: 'bg-amber-50', label: 'Medium' },
    high: { icon: ShieldAlert, color: 'text-rose-600', bg: 'bg-rose-50', label: 'High' },
  }[profile.risk_tier] || { icon: Shield, color: 'text-slate-600', bg: 'bg-slate-50', label: profile.risk_tier };

  const RiskIcon = riskConfig.icon;

  const metrics = [
    {
      icon: Package,
      label: 'Total Products',
      value: String(total_products),
      color: 'text-indigo-600',
      bg: 'bg-indigo-50',
    },
    {
      icon: AlertTriangle,
      label: 'Active Claims',
      value: String(active_claims),
      color: active_claims > 0 ? 'text-amber-600' : 'text-slate-600',
      bg: active_claims > 0 ? 'bg-amber-50' : 'bg-slate-50',
    },
    {
      icon: RiskIcon,
      label: 'Risk Score',
      value: riskConfig.label,
      color: riskConfig.color,
      bg: riskConfig.bg,
    },
    {
      icon: TrendingUp,
      label: 'Journey Events',
      value: String(journey_events.length),
      color: 'text-violet-600',
      bg: 'bg-violet-50',
    },
    {
      icon: AlertTriangle,
      label: 'Risk Insights',
      value: `${criticalCorrelations + warningCorrelations}`,
      color: criticalCorrelations > 0 ? 'text-rose-600' : warningCorrelations > 0 ? 'text-amber-600' : 'text-slate-600',
      bg: criticalCorrelations > 0 ? 'bg-rose-50' : warningCorrelations > 0 ? 'bg-amber-50' : 'bg-slate-50',
      sublabel: criticalCorrelations > 0 ? `${criticalCorrelations} critical` : undefined,
    },
  ];

  return (
    <div className="grid grid-cols-5 gap-4">
      {metrics.map(metric => {
        const Icon = metric.icon;
        return (
          <div
            key={metric.label}
            className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 flex items-center gap-3"
          >
            <div className={clsx('w-10 h-10 rounded-lg flex items-center justify-center', metric.bg)}>
              <Icon className={clsx('w-5 h-5', metric.color)} />
            </div>
            <div>
              <div className="text-xs text-slate-500">{metric.label}</div>
              <div className={clsx('text-lg font-bold', metric.color)}>{metric.value}</div>
              {(metric as any).sublabel && (
                <div className="text-xs text-rose-500 font-medium">{(metric as any).sublabel}</div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
