'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Users,
  Settings,
  LogOut,
  User,
  Database,
  Loader2,
} from 'lucide-react';
import { listCustomers, seedCustomer360Data } from '@/lib/customer360-api';
import type { CustomerProfile } from '@/lib/customer360-types';
import CustomerListView from '@/components/customer360/CustomerListView';
import PersonaSelector from '@/components/PersonaSelector';

export default function CustomersPage() {
  const [customers, setCustomers] = useState<CustomerProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const router = useRouter();
  const [authUser, setAuthUser] = useState<string | null>(null);
  const [authEnabled, setAuthEnabled] = useState(false);

  useEffect(() => {
    fetchCustomers();
    checkAuth();
  }, []);

  async function fetchCustomers() {
    try {
      setLoading(true);
      const data = await listCustomers();
      setCustomers(data);
    } catch (err) {
      console.error('Failed to load customers:', err);
      setCustomers([]);
    } finally {
      setLoading(false);
    }
  }

  async function checkAuth() {
    try {
      const res = await fetch('/api/auth/check');
      const data = await res.json();
      if (data.authEnabled) {
        setAuthEnabled(true);
        setAuthUser(data.username || null);
      }
    } catch {
      // ignore
    }
  }

  async function handleSeedData() {
    try {
      setSeeding(true);
      await seedCustomer360Data();
      await fetchCustomers();
    } catch (err) {
      console.error('Failed to seed data:', err);
    } finally {
      setSeeding(false);
    }
  }

  async function handleLogout() {
    await fetch('/api/auth/logout', { method: 'POST' });
    router.push('/login');
    router.refresh();
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/30">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="flex items-center justify-between px-6 py-3">
          <div className="flex items-center gap-6">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-lg flex items-center justify-center shadow-sm bg-gradient-to-br from-indigo-500 to-indigo-600">
                <span className="text-white font-bold text-xs">W.IQ</span>
              </div>
              <span className="font-semibold text-lg text-slate-900">WorkbenchIQ</span>
            </Link>

            <PersonaSelector />

            {/* Active tab indicator */}
            <div className="flex items-center gap-1 px-3 py-1.5 bg-indigo-50 border border-indigo-200 rounded-lg">
              <Users className="w-4 h-4 text-indigo-600" />
              <span className="text-sm font-medium text-indigo-700">Customer 360</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/admin"
              className="flex items-center gap-2 px-3 py-2 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <Settings className="w-4 h-4" />
              <span>Admin</span>
            </Link>

            {authEnabled && (
              <div className="flex items-center gap-2 ml-2 pl-2 border-l border-slate-200">
                {authUser && (
                  <span className="flex items-center gap-1.5 text-sm text-slate-500">
                    <User className="w-3.5 h-3.5" />
                    {authUser}
                  </span>
                )}
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-1.5 px-2.5 py-1.5 text-sm text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  title="Sign out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center">
                <Users className="w-5 h-5 text-white" />
              </div>
              Customer 360
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Unified cross-persona view of customer journeys across underwriting, claims, and mortgage.
            </p>
          </div>

          {/* Seed data button (for demo) */}
          {!loading && customers.length === 0 && (
            <button
              onClick={handleSeedData}
              disabled={seeding}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
            >
              {seeding ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Database className="w-4 h-4" />
              )}
              {seeding ? 'Seeding…' : 'Load Sample Data'}
            </button>
          )}
        </div>

        {/* Customer List */}
        <CustomerListView
          customers={customers}
          loading={loading}
          onSelectCustomer={(id) => router.push(`/customers/${id}`)}
        />
      </main>
    </div>
  );
}
