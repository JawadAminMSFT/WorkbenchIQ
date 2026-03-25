'use client';

import { useState, useMemo } from 'react';
import {
  Search,
  Users,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Package,
  Calendar,
  ChevronRight,
  Loader2,
  ArrowUpDown,
} from 'lucide-react';
import type { CustomerProfile } from '@/lib/customer360-types';
import clsx from 'clsx';

interface CustomerListViewProps {
  customers: CustomerProfile[];
  loading: boolean;
  onSelectCustomer: (customerId: string) => void;
}

const RISK_TIER_CONFIG = {
  low: { label: 'Low Risk', icon: ShieldCheck, color: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200', dot: 'bg-emerald-500' },
  medium: { label: 'Medium Risk', icon: Shield, color: 'text-amber-700', bg: 'bg-amber-50', border: 'border-amber-200', dot: 'bg-amber-500' },
  high: { label: 'High Risk', icon: ShieldAlert, color: 'text-rose-700', bg: 'bg-rose-50', border: 'border-rose-200', dot: 'bg-rose-500' },
};

export default function CustomerListView({
  customers,
  loading,
  onSelectCustomer,
}: CustomerListViewProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortField, setSortField] = useState<'name' | 'risk_tier' | 'customer_since'>('name');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

  const filteredCustomers = useMemo(() => {
    let result = customers;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        c =>
          c.name.toLowerCase().includes(q) ||
          c.id.toLowerCase().includes(q) ||
          c.email.toLowerCase().includes(q) ||
          c.tags.some(t => t.toLowerCase().includes(q))
      );
    }

    const riskOrder = { low: 0, medium: 1, high: 2 };
    result = [...result].sort((a, b) => {
      let cmp = 0;
      if (sortField === 'name') cmp = a.name.localeCompare(b.name);
      else if (sortField === 'risk_tier') cmp = (riskOrder[a.risk_tier] ?? 0) - (riskOrder[b.risk_tier] ?? 0);
      else if (sortField === 'customer_since') cmp = a.customer_since.localeCompare(b.customer_since);
      return sortDir === 'asc' ? cmp : -cmp;
    });

    return result;
  }, [customers, searchQuery, sortField, sortDir]);

  const toggleSort = (field: typeof sortField) => {
    if (sortField === field) setSortDir(d => (d === 'asc' ? 'desc' : 'asc'));
    else { setSortField(field); setSortDir('asc'); }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
        <span className="ml-3 text-slate-500">Loading customers…</span>
      </div>
    );
  }

  return (
    <div>
      {/* Search & Filters */}
      <div className="flex items-center gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search customers by name, ID, or tag…"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <Users className="w-4 h-4" />
          <span>{filteredCustomers.length} customer{filteredCustomers.length !== 1 ? 's' : ''}</span>
        </div>
      </div>

      {/* Table */}
      {filteredCustomers.length === 0 ? (
        <div className="text-center py-16 text-slate-400">
          <Users className="w-12 h-12 mx-auto mb-3 opacity-40" />
          <p className="text-lg font-medium">No customers found</p>
          <p className="text-sm mt-1">Try adjusting your search or seed sample data.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/50">
                <th className="text-left px-5 py-3">
                  <button onClick={() => toggleSort('name')} className="flex items-center gap-1 text-xs font-semibold text-slate-500 uppercase tracking-wider hover:text-slate-700">
                    Customer <ArrowUpDown className="w-3 h-3" />
                  </button>
                </th>
                <th className="text-left px-5 py-3">
                  <button onClick={() => toggleSort('risk_tier')} className="flex items-center gap-1 text-xs font-semibold text-slate-500 uppercase tracking-wider hover:text-slate-700">
                    Risk Tier <ArrowUpDown className="w-3 h-3" />
                  </button>
                </th>
                <th className="text-left px-5 py-3">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Products</span>
                </th>
                <th className="text-left px-5 py-3">
                  <button onClick={() => toggleSort('customer_since')} className="flex items-center gap-1 text-xs font-semibold text-slate-500 uppercase tracking-wider hover:text-slate-700">
                    Customer Since <ArrowUpDown className="w-3 h-3" />
                  </button>
                </th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody>
              {filteredCustomers.map(customer => {
                const riskConfig = RISK_TIER_CONFIG[customer.risk_tier] || RISK_TIER_CONFIG.low;
                const RiskIcon = riskConfig.icon;
                const tenure = getCustomerTenure(customer.customer_since);

                return (
                  <tr
                    key={customer.id}
                    onClick={() => onSelectCustomer(customer.id)}
                    className="border-b border-slate-50 hover:bg-slate-50/80 cursor-pointer transition-colors group"
                  >
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-100 to-indigo-200 flex items-center justify-center text-indigo-700 font-semibold text-sm">
                          {getInitials(customer.name)}
                        </div>
                        <div>
                          <div className="font-medium text-slate-900">{customer.name}</div>
                          <div className="text-xs text-slate-500">{customer.id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      <span className={clsx('inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium', riskConfig.bg, riskConfig.color, 'border', riskConfig.border)}>
                        <RiskIcon className="w-3.5 h-3.5" />
                        {riskConfig.label}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-1.5">
                        <Package className="w-4 h-4 text-slate-400" />
                        <span className="text-sm text-slate-600">{customer.tags.filter(t => !['new-customer', 'investigation', 'health-watch', 'conditional', 'multi-risk'].includes(t)).length || '—'}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-1.5">
                        <Calendar className="w-4 h-4 text-slate-400" />
                        <span className="text-sm text-slate-600">{tenure}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4 text-right">
                      <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-indigo-500 transition-colors inline" />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function getInitials(name: string): string {
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
}

function getCustomerTenure(since: string): string {
  const start = new Date(since);
  const now = new Date();
  const years = now.getFullYear() - start.getFullYear();
  const months = now.getMonth() - start.getMonth();
  const totalMonths = years * 12 + months;
  if (totalMonths < 1) return 'New';
  if (totalMonths < 12) return `${totalMonths}mo`;
  const y = Math.floor(totalMonths / 12);
  const m = totalMonths % 12;
  return m > 0 ? `${y}y ${m}mo` : `${y}y`;
}
