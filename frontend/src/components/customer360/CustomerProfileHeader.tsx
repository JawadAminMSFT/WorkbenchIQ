'use client';

import {
  ShieldCheck,
  Shield,
  ShieldAlert,
  Mail,
  Phone,
  MapPin,
  Calendar,
  Package,
  AlertTriangle,
  Tag,
} from 'lucide-react';
import type { Customer360View } from '@/lib/customer360-types';
import clsx from 'clsx';

interface CustomerProfileHeaderProps {
  data: Customer360View;
}

const RISK_TIER_CONFIG = {
  low: { label: 'Low Risk', icon: ShieldCheck, color: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200', gradient: 'from-emerald-500 to-emerald-600' },
  medium: { label: 'Medium Risk', icon: Shield, color: 'text-amber-700', bg: 'bg-amber-50', border: 'border-amber-200', gradient: 'from-amber-500 to-amber-600' },
  high: { label: 'High Risk', icon: ShieldAlert, color: 'text-rose-700', bg: 'bg-rose-50', border: 'border-rose-200', gradient: 'from-rose-500 to-rose-600' },
};

export default function CustomerProfileHeader({ data }: CustomerProfileHeaderProps) {
  const { profile, total_products, active_claims, overall_risk } = data;
  const riskConfig = RISK_TIER_CONFIG[profile.risk_tier] || RISK_TIER_CONFIG.low;
  const RiskIcon = riskConfig.icon;

  const tenure = getCustomerTenure(profile.customer_since);
  const age = getAge(profile.date_of_birth);

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Top gradient bar */}
      <div className={clsx('h-1.5 bg-gradient-to-r', riskConfig.gradient)} />

      <div className="p-6">
        <div className="flex items-start justify-between">
          {/* Customer identity */}
          <div className="flex items-start gap-4">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-indigo-100 to-indigo-200 flex items-center justify-center text-indigo-700 font-bold text-xl shadow-sm">
              {getInitials(profile.name)}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">{profile.name}</h1>
              <div className="flex items-center gap-4 mt-1 text-sm text-slate-500">
                <span>{profile.id}</span>
                <span>•</span>
                <span>Age {age}</span>
                <span>•</span>
                <span>DOB {formatDate(profile.date_of_birth)}</span>
              </div>
              <div className="flex items-center gap-4 mt-2 text-sm text-slate-500">
                <span className="flex items-center gap-1"><Mail className="w-3.5 h-3.5" /> {profile.email}</span>
                <span className="flex items-center gap-1"><Phone className="w-3.5 h-3.5" /> {profile.phone}</span>
              </div>
              <div className="flex items-center gap-1 mt-1 text-sm text-slate-500">
                <MapPin className="w-3.5 h-3.5" /> {profile.address}
              </div>
            </div>
          </div>

          {/* Risk badge */}
          <div className={clsx('flex items-center gap-2 px-4 py-2 rounded-lg border', riskConfig.bg, riskConfig.border)}>
            <RiskIcon className={clsx('w-5 h-5', riskConfig.color)} />
            <div>
              <div className={clsx('text-sm font-semibold', riskConfig.color)}>{riskConfig.label}</div>
              <div className="text-xs text-slate-500">Overall Assessment</div>
            </div>
          </div>
        </div>

        {/* Stats strip */}
        <div className="flex items-center gap-6 mt-6 pt-5 border-t border-slate-100">
          <Stat icon={Calendar} label="Customer Since" value={formatDate(profile.customer_since)} sublabel={tenure} />
          <div className="w-px h-10 bg-slate-200" />
          <Stat icon={Package} label="Products" value={String(total_products)} />
          <div className="w-px h-10 bg-slate-200" />
          <Stat
            icon={AlertTriangle}
            label="Active Claims"
            value={String(active_claims)}
            valueColor={active_claims > 0 ? 'text-amber-600' : 'text-slate-900'}
          />
          <div className="w-px h-10 bg-slate-200" />
          <div className="flex items-center gap-2">
            <Tag className="w-4 h-4 text-slate-400" />
            <div className="flex flex-wrap gap-1.5">
              {profile.tags.map(tag => (
                <span key={tag} className="px-2 py-0.5 bg-slate-100 text-slate-600 text-xs rounded-full">
                  {tag}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Notes */}
        {profile.notes && (
          <div className="mt-4 p-3 bg-slate-50 rounded-lg text-sm text-slate-600 leading-relaxed">
            {profile.notes}
          </div>
        )}
      </div>
    </div>
  );
}

function Stat({
  icon: Icon,
  label,
  value,
  sublabel,
  valueColor = 'text-slate-900',
}: {
  icon: typeof Calendar;
  label: string;
  value: string;
  sublabel?: string;
  valueColor?: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <Icon className="w-4 h-4 text-slate-400" />
      <div>
        <div className="text-xs text-slate-500">{label}</div>
        <div className={clsx('text-sm font-semibold', valueColor)}>
          {value}
          {sublabel && <span className="text-xs text-slate-400 ml-1.5 font-normal">({sublabel})</span>}
        </div>
      </div>
    </div>
  );
}

function getInitials(name: string): string {
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
}

function getAge(dob: string): number {
  const birth = new Date(dob);
  const now = new Date();
  let age = now.getFullYear() - birth.getFullYear();
  const m = now.getMonth() - birth.getMonth();
  if (m < 0 || (m === 0 && now.getDate() < birth.getDate())) age--;
  return age;
}

function getCustomerTenure(since: string): string {
  const start = new Date(since);
  const now = new Date();
  const totalMonths = (now.getFullYear() - start.getFullYear()) * 12 + (now.getMonth() - start.getMonth());
  if (totalMonths < 1) return 'New';
  if (totalMonths < 12) return `${totalMonths} months`;
  const y = Math.floor(totalMonths / 12);
  const m = totalMonths % 12;
  return m > 0 ? `${y} yr ${m} mo` : `${y} yr`;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-CA', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}
