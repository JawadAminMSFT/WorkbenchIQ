'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Users, TrendingUp, FileText, Clock, Plus, Building2,
  AlertTriangle, Briefcase,
} from 'lucide-react';
import { getBrokerDashboard, getClients, createClient } from '../../lib/broker-api';
import type { DashboardMetrics, Client } from '../../lib/broker-types';

interface BrokerDashboardProps {
  onSelectClient: (clientId: string) => void;
  onSelectSubmission?: (submissionId: string) => void;
}

function formatCurrency(value: number | undefined | null): string {
  if (value == null) return '$0';
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
        { label: 'Bound Premium', value: metrics.total_bound_premium, icon: TrendingUp },
        { label: 'Open Submissions', value: metrics.open_submissions, icon: FileText },
        { label: 'Renewals Due (90d)', value: metrics.renewals_due_90_days, icon: Clock },
      ]
    : [];

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
