'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Users, TrendingUp, FileText, Clock, Plus, Building2,
  AlertTriangle, Briefcase,
} from 'lucide-react';
import { getBrokerDashboard, getClients } from '../../lib/broker-api';
import type { DashboardMetrics, Client } from '../../lib/broker-types';

interface BrokerDashboardProps {
  onSelectClient: (clientId: string) => void;
  onSelectSubmission?: (submissionId: string) => void;
}

function formatCurrency(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
  return `$${value.toLocaleString()}`;
}

export default function BrokerDashboard({
  onSelectClient,
  onSelectSubmission,
}: BrokerDashboardProps) {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  useEffect(() => {
    fetchData();
  }, [fetchData]);

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

  const metricCards = metrics
    ? [
        { label: 'Total Accounts', value: metrics.total_accounts, icon: Users },
        { label: 'Bound Premium', value: formatCurrency(metrics.total_bound_premium), icon: TrendingUp },
        { label: 'Open Submissions', value: metrics.open_submissions, icon: FileText },
        { label: 'Renewals Due (90d)', value: metrics.renewals_due_90_days, icon: Clock },
      ]
    : [];

  const statusColor: Record<Client['status'], string> = {
    active: 'bg-green-100 text-green-700',
    prospect: 'bg-amber-100 text-amber-700',
    inactive: 'bg-slate-100 text-slate-500',
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {metricCards.map((m) => (
          <div
            key={m.label}
            className="bg-white rounded-lg border border-slate-200 p-5 flex items-center gap-4"
          >
            <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center shrink-0">
              <m.icon className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500">{m.label}</p>
              <p className="text-xl font-semibold text-slate-900">{m.value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Accounts Section */}
      <div className="bg-white rounded-lg border border-slate-200">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200">
          <h2 className="text-base font-semibold text-slate-900">Accounts</h2>
          <button className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 rounded-lg transition-colors">
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
                    <p className="text-sm font-medium text-slate-900">{client.company_name}</p>
                    <p className="text-xs text-slate-500">
                      {client.industry} • {client.contact_name}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-right">
                  <div>
                    <p className="text-sm font-medium text-slate-900">
                      {formatCurrency(client.total_premium)}
                    </p>
                    <p className="text-xs text-slate-500">
                      {client.active_submissions} submission{client.active_submissions !== 1 ? 's' : ''}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span
                      className={`inline-block text-xs font-medium px-2 py-0.5 rounded-full ${statusColor[client.status]}`}
                    >
                      {client.status}
                    </span>
                    <span className="text-xs text-slate-400">
                      Renews {new Date(client.renewal_date).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
