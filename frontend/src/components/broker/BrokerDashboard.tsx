'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Users, TrendingUp, FileText, Clock, Plus, Building2,
  AlertTriangle, Briefcase, CalendarClock, AlertCircle,
} from 'lucide-react';
import { getBrokerDashboard, getClients, createClient } from '../../lib/broker-api';
import type { DashboardMetrics, Client } from '../../lib/broker-types';

interface BrokerDashboardProps {
  onSelectClient: (clientId: string) => void;
}

function formatCurrency(value: number | undefined | null): string {
  if (value == null) return '$0';
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
  return `$${value.toLocaleString()}`;
}

export default function BrokerDashboard({
  onSelectClient,
}: BrokerDashboardProps) {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showNewClientModal, setShowNewClientModal] = useState(false);
  const [newClientData, setNewClientData] = useState({
    name: '',
    industry_code: '',
    business_type: '',
    headquarters_address: '',
    annual_revenue: '',
  });

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [dashboardData, clientsData] = await Promise.all([
        getBrokerDashboard(),
        getClients(),
      ]);
      setMetrics(dashboardData);
      setClients(clientsData);
    } catch (err) {
      console.error('Failed to fetch dashboard:', err);
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleCreateClient = async () => {
    if (!newClientData.name || !newClientData.industry_code) {
      alert('Please fill in at least the name and industry code');
      return;
    }
    try {
      await createClient(newClientData);
      setShowNewClientModal(false);
      setNewClientData({
        name: '',
        industry_code: '',
        business_type: '',
        headquarters_address: '',
        annual_revenue: '',
      });
      await fetchData(); // Refresh the client list
    } catch (err) {
      console.error('Failed to create client:', err);
      alert('Failed to create client. Please try again.');
    }
  };

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // AC-1.2: Compute upcoming renewals (within 90 days) — must be before conditional returns
  const upcomingRenewals = useMemo(() => {
    const now = new Date();
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() + 90);
    return clients
      .filter((c) => {
        if (!c.renewal_date) return false;
        const rd = new Date(c.renewal_date);
        return rd >= now && rd <= cutoff;
      })
      .sort((a, b) => new Date(a.renewal_date!).getTime() - new Date(b.renewal_date!).getTime());
  }, [clients]);

  // AC-1.3: Helper to check if a date is stale (>7 days ago)
  const isStale = useCallback((dateStr: string | undefined | null): boolean => {
    if (!dateStr) return false;
    const d = new Date(dateStr);
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
    return d < sevenDaysAgo;
  }, []);

  const metricCards = useMemo(() => metrics
    ? [
        { label: 'Total Accounts', value: metrics.total_accounts, icon: Users, alert: false },
        { label: 'Bound Premium', value: metrics.total_bound_premium, icon: TrendingUp, alert: false },
        { label: 'Open Submissions', value: metrics.open_submissions, icon: FileText, alert: false },
        { label: 'Renewals Due (90d)', value: metrics.renewals_due_90_days, icon: Clock, alert: false },
        { label: 'Stale Submissions', value: metrics.stale_submissions, icon: AlertCircle, alert: (metrics.stale_submissions ?? 0) > 0 },
      ]
    : [], [metrics]);

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-600" />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-red-600">
        <AlertTriangle className="w-12 h-12 mb-4" />
        <p className="text-lg font-medium">{error}</p>
        <button
          onClick={fetchData}
          className="mt-4 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {metricCards.map((m) => (
          <div
            key={m.label}
            className={`bg-white rounded-lg border p-5 flex items-center gap-4 ${
              m.alert ? 'border-red-300' : 'border-slate-200'
            }`}
          >
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
              m.alert ? 'bg-red-100' : 'bg-amber-100'
            }`}>
              <m.icon className={`w-5 h-5 ${m.alert ? 'text-red-600' : 'text-amber-600'}`} />
            </div>
            <div>
              <p className="text-sm text-slate-500">{m.label}</p>
              <p className={`text-xl font-semibold ${m.alert ? 'text-red-700' : 'text-slate-900'}`}>{m.value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* AC-1.2: Upcoming Renewals Section */}
      {upcomingRenewals.length > 0 && (
        <div className="bg-white rounded-lg border border-amber-200">
          <div className="flex items-center gap-2 px-5 py-4 border-b border-amber-200 bg-amber-50 rounded-t-lg">
            <CalendarClock className="w-5 h-5 text-amber-600" />
            <h2 className="text-base font-semibold text-slate-900">Upcoming Renewals</h2>
            <span className="ml-auto text-xs font-medium text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full">
              {upcomingRenewals.length} within 90 days
            </span>
          </div>
          <div className="divide-y divide-amber-100">
            {upcomingRenewals.map((client) => {
              const renewalDate = new Date(client.renewal_date!);
              const daysUntil = Math.ceil((renewalDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
              return (
                <button
                  key={client.id}
                  onClick={() => onSelectClient(client.id)}
                  className="w-full text-left px-5 py-3 hover:bg-amber-50 transition-colors flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center">
                      <Building2 className="w-4 h-4 text-amber-600" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-900">{client.name}</p>
                      <p className="text-xs text-slate-500">
                        {client.industry_code || 'No industry'} • {client.annual_revenue || '$0'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
                      daysUntil <= 14
                        ? 'bg-red-100 text-red-700'
                        : daysUntil <= 30
                        ? 'bg-orange-100 text-orange-700'
                        : 'bg-amber-100 text-amber-700'
                    }`}>
                      {daysUntil <= 0 ? 'Today' : `${daysUntil}d`}
                    </span>
                    <span className="text-sm font-medium text-amber-700">
                      {renewalDate.toLocaleDateString()}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Accounts Section */}
      <div className="bg-white rounded-lg border border-slate-200">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200">
          <h2 className="text-base font-semibold text-slate-900">Accounts</h2>
          <button
            onClick={() => setShowNewClientModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Client
          </button>
        </div>

        {clients.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-slate-400">
            <Building2 className="w-10 h-10 mb-3" />
            <p className="text-sm">No clients yet. Add your first account to get started.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {clients.map((client) => (
              <button
                key={client.id}
                onClick={() => onSelectClient(client.id)}
                className="w-full text-left px-5 py-4 hover:bg-slate-50 transition-colors flex items-center justify-between"
              >
                <div className="flex items-center gap-4">
                  <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center">
                    <Building2 className="w-4 h-4 text-slate-500" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">{client.name}</p>
                    <p className="text-xs text-slate-500">
                      {client.industry_code || 'No industry'} • {client.business_type || 'No type'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-right">
                  <div>
                    <p className="text-sm font-medium text-slate-900">
                      {client.annual_revenue || '$0'}
                    </p>
                    <p className="text-xs text-slate-500">
                      {client.contacts?.length || 0} contact{client.contacts?.length !== 1 ? 's' : ''}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    {isStale(client.updated_at) && (
                      <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-red-100 text-red-700">
                        Stale
                      </span>
                    )}
                    <span className="text-xs text-slate-400">
                      {client.renewal_date ? `Renews ${new Date(client.renewal_date).toLocaleDateString()}` : 'No renewal date'}
                    </span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* New Client Modal */}
      {showNewClientModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">New Client</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Company Name *
                </label>
                <input
                  type="text"
                  value={newClientData.name}
                  onChange={(e) => setNewClientData({ ...newClientData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
                  placeholder="Acme Corp"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Industry Code *
                </label>
                <input
                  type="text"
                  value={newClientData.industry_code}
                  onChange={(e) => setNewClientData({ ...newClientData, industry_code: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
                  placeholder="Manufacturing"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Business Type
                </label>
                <input
                  type="text"
                  value={newClientData.business_type}
                  onChange={(e) => setNewClientData({ ...newClientData, business_type: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
                  placeholder="LLC"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Address
                </label>
                <input
                  type="text"
                  value={newClientData.headquarters_address}
                  onChange={(e) => setNewClientData({ ...newClientData, headquarters_address: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
                  placeholder="123 Main St, City, State"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Annual Revenue
                </label>
                <input
                  type="text"
                  value={newClientData.annual_revenue}
                  onChange={(e) => setNewClientData({ ...newClientData, annual_revenue: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
                  placeholder="$1,000,000"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowNewClientModal(false)}
                className="flex-1 px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateClient}
                className="flex-1 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
