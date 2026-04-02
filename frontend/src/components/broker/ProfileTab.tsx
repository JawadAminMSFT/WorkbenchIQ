'use client';

import React, { useState, useEffect } from 'react';
import {
  Building2, Shield, AlertTriangle, FileText, Users, Phone,
  Mail, Loader2, ChevronRight, Briefcase,
} from 'lucide-react';
import { getClientDocuments } from '../../lib/broker-api';
import type { Client, SubmissionDocument } from '../../lib/broker-types';

interface ProfileTabProps {
  clientId: string;
  client: Client | null;
  onStartRenewal?: (lineOfBusiness: string, effectiveDate: string, expirationDate: string) => void;
}

function isWithin90Days(dateStr: string): boolean {
  const now = new Date();
  const expiry = new Date(dateStr);
  const diffMs = expiry.getTime() - now.getTime();
  const diffDays = diffMs / (1000 * 60 * 60 * 24);
  return diffDays >= 0 && diffDays <= 90;
}

function statusBadge(status: string) {
  const colors: Record<string, string> = {
    'in-force': 'bg-green-100 text-green-800',
    'expired': 'bg-red-100 text-red-800',
    'pending': 'bg-yellow-100 text-yellow-800',
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${colors[status] || 'bg-slate-100 text-slate-800'}`}>
      {status}
    </span>
  );
}

function claimStatusBadge(status: string) {
  const colors: Record<string, string> = {
    'closed': 'bg-slate-100 text-slate-700',
    'open': 'bg-amber-100 text-amber-800',
    'settled': 'bg-green-100 text-green-800',
    'denied': 'bg-red-100 text-red-800',
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${colors[status] || 'bg-slate-100 text-slate-800'}`}>
      {status}
    </span>
  );
}

function docTypeBadge(docType: string) {
  const labels: Record<string, string> = {
    acord_125: 'ACORD 125',
    acord_140: 'ACORD 140',
    sov: 'SOV',
    loss_runs: 'Loss Runs',
    prior_declaration: 'Prior Dec',
    property_photos: 'Photos',
    submission_email: 'Email',
    carrier_quote: 'Quote',
    other: 'Other',
  };
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
      {labels[docType] || docType}
    </span>
  );
}

export default function ProfileTab({ clientId, client, onStartRenewal }: ProfileTabProps) {
  const [documents, setDocuments] = useState<(SubmissionDocument & { line_of_business?: string })[]>([]);
  const [docsLoading, setDocsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const docs = await getClientDocuments(clientId);
        if (!cancelled) setDocuments(docs as (SubmissionDocument & { line_of_business?: string })[]);
      } catch (err) {
        console.error('Failed to load client documents:', err);
      } finally {
        if (!cancelled) setDocsLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [clientId]);

  if (!client) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-amber-600" />
      </div>
    );
  }

  const policies = client.policies || [];
  const claims = client.claims_history || [];
  const carrierContacts = client.carrier_contacts || [];
  const clientContacts = client.contacts || [];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* ── Company Details ── */}
      <section className="bg-white rounded-xl border border-slate-200 p-5">
        <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2 mb-4">
          <Building2 className="w-4 h-4 text-amber-600" />
          Company Details
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-slate-500 block text-xs">Company Name</span>
            <span className="font-medium text-slate-900">{client.name}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-xs">Industry</span>
            <span className="font-medium text-slate-900">
              {client.industry_code} — {client.business_type}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block text-xs">Annual Revenue</span>
            <span className="font-medium text-slate-900">{client.annual_revenue || '—'}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-xs">Employees</span>
            <span className="font-medium text-slate-900">
              {client.employee_count != null ? client.employee_count.toLocaleString() : '—'}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block text-xs">Headquarters</span>
            <span className="font-medium text-slate-900">{client.headquarters_address || '—'}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-xs">Years in Business</span>
            <span className="font-medium text-slate-900">
              {client.years_in_business != null ? client.years_in_business : '—'}
            </span>
          </div>
        </div>
      </section>

      {/* ── Policy Portfolio ── */}
      <section className="bg-white rounded-xl border border-slate-200 p-5">
        <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2 mb-4">
          <Shield className="w-4 h-4 text-amber-600" />
          Policy Portfolio
        </h3>
        {policies.length === 0 ? (
          <p className="text-sm text-slate-500 italic">No policies on file.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  <th className="pb-2 pr-3">Policy #</th>
                  <th className="pb-2 pr-3">Carrier</th>
                  <th className="pb-2 pr-3">LOB</th>
                  <th className="pb-2 pr-3">Status</th>
                  <th className="pb-2 pr-3">Effective</th>
                  <th className="pb-2 pr-3">Expiration</th>
                  <th className="pb-2 pr-3 text-right">Premium</th>
                  <th className="pb-2"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {policies.map((pol) => {
                  const expiring = pol.status === 'in-force' && pol.expiration_date && isWithin90Days(pol.expiration_date);
                  return (
                    <tr
                      key={pol.policy_number}
                      className={expiring ? 'bg-amber-50' : ''}
                    >
                      <td className="py-2.5 pr-3 font-medium text-slate-900">
                        {pol.policy_number}
                      </td>
                      <td className="py-2.5 pr-3 text-slate-700">{pol.carrier}</td>
                      <td className="py-2.5 pr-3 text-slate-700">{pol.line_of_business}</td>
                      <td className="py-2.5 pr-3">
                        {statusBadge(pol.status)}
                        {expiring && (
                          <span className="ml-1.5 inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                            ⚠ Renewal Due
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 pr-3 text-slate-600">
                        {pol.effective_date ? new Date(pol.effective_date).toLocaleDateString() : '—'}
                      </td>
                      <td className="py-2.5 pr-3 text-slate-600">
                        {pol.expiration_date ? new Date(pol.expiration_date).toLocaleDateString() : '—'}
                      </td>
                      <td className="py-2.5 pr-3 text-right text-slate-900 font-medium">
                        {pol.premium}
                      </td>
                      <td className="py-2.5 text-right">
                        {expiring && onStartRenewal && (
                          <button
                            onClick={() =>
                              onStartRenewal(
                                pol.line_of_business,
                                pol.expiration_date,
                                // New expiration = 1 year after current expiration
                                (() => {
                                  const d = new Date(pol.expiration_date);
                                  d.setFullYear(d.getFullYear() + 1);
                                  return d.toISOString().slice(0, 10);
                                })(),
                              )
                            }
                            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-amber-700 bg-amber-100 hover:bg-amber-200 rounded-lg transition-colors"
                          >
                            Start Renewal
                            <ChevronRight className="w-3 h-3" />
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* ── Claims Summary ── */}
      <section className="bg-white rounded-xl border border-slate-200 p-5">
        <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2 mb-4">
          <AlertTriangle className="w-4 h-4 text-amber-600" />
          Claims Summary
        </h3>
        {claims.length === 0 ? (
          <p className="text-sm text-slate-500 italic">No claims on record.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  <th className="pb-2 pr-3">Claim #</th>
                  <th className="pb-2 pr-3">Date</th>
                  <th className="pb-2 pr-3">Type</th>
                  <th className="pb-2 pr-3 text-right">Amount</th>
                  <th className="pb-2 pr-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {claims.map((cl) => (
                  <tr key={cl.claim_number}>
                    <td className="py-2.5 pr-3 font-medium text-slate-900">{cl.claim_number}</td>
                    <td className="py-2.5 pr-3 text-slate-600">
                      {cl.date ? new Date(cl.date).toLocaleDateString() : '—'}
                    </td>
                    <td className="py-2.5 pr-3 text-slate-700">{cl.type}</td>
                    <td className="py-2.5 pr-3 text-right text-slate-900 font-medium">{cl.amount}</td>
                    <td className="py-2.5 pr-3">{claimStatusBadge(cl.status)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* ── Contacts ── */}
      <section className="bg-white rounded-xl border border-slate-200 p-5">
        <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2 mb-4">
          <Users className="w-4 h-4 text-amber-600" />
          Contacts
        </h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Client Contacts */}
          <div>
            <h4 className="text-sm font-medium text-slate-700 mb-3">Client Contacts</h4>
            {clientContacts.length === 0 ? (
              <p className="text-sm text-slate-500 italic">No client contacts.</p>
            ) : (
              <div className="space-y-2">
                {clientContacts.map((c, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                    <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center shrink-0">
                      <Users className="w-3.5 h-3.5 text-amber-700" />
                    </div>
                    <div className="text-sm">
                      <p className="font-medium text-slate-900">{c.name || 'Unknown'}</p>
                      {c.role && <p className="text-xs text-slate-500">{c.role}</p>}
                      {c.email && (
                        <p className="flex items-center gap-1 text-slate-600 mt-0.5">
                          <Mail className="w-3 h-3" /> {c.email}
                        </p>
                      )}
                      {c.phone && (
                        <p className="flex items-center gap-1 text-slate-600">
                          <Phone className="w-3 h-3" /> {c.phone}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Carrier / Underwriter Contacts */}
          <div>
            <h4 className="text-sm font-medium text-slate-700 mb-3">Carrier / Underwriter Contacts</h4>
            {carrierContacts.length === 0 ? (
              <p className="text-sm text-slate-500 italic">No carrier contacts.</p>
            ) : (
              <div className="space-y-2">
                {carrierContacts.map((c, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                    <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center shrink-0">
                      <Briefcase className="w-3.5 h-3.5 text-blue-700" />
                    </div>
                    <div className="text-sm">
                      <p className="font-medium text-slate-900">{c.name}</p>
                      <p className="text-xs text-slate-500">{c.carrier} — {c.role}</p>
                      {c.email && (
                        <p className="flex items-center gap-1 text-slate-600 mt-0.5">
                          <Mail className="w-3 h-3" /> {c.email}
                        </p>
                      )}
                      {c.phone && (
                        <p className="flex items-center gap-1 text-slate-600">
                          <Phone className="w-3 h-3" /> {c.phone}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* ── Document Library ── */}
      <section className="bg-white rounded-xl border border-slate-200 p-5">
        <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2 mb-4">
          <FileText className="w-4 h-4 text-amber-600" />
          Document Library
        </h3>
        {docsLoading ? (
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Loader2 className="w-4 h-4 animate-spin" /> Loading documents…
          </div>
        ) : documents.length === 0 ? (
          <p className="text-sm text-slate-500 italic">No documents uploaded yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  <th className="pb-2 pr-3">File Name</th>
                  <th className="pb-2 pr-3">Type</th>
                  <th className="pb-2 pr-3">Submission</th>
                  <th className="pb-2 pr-3">Uploaded</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {documents.map((doc) => (
                  <tr key={doc.id}>
                    <td className="py-2.5 pr-3 font-medium text-slate-900 flex items-center gap-2">
                      <FileText className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      {doc.file_name}
                    </td>
                    <td className="py-2.5 pr-3">{docTypeBadge(doc.document_type)}</td>
                    <td className="py-2.5 pr-3 text-slate-600 text-xs font-mono">
                      {doc.submission_id?.slice(0, 8)}…
                      {doc.line_of_business ? (
                        <span className="ml-1 text-slate-500">
                          ({String(doc.line_of_business)})
                        </span>
                      ) : null}
                    </td>
                    <td className="py-2.5 pr-3 text-slate-600">
                      {doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
