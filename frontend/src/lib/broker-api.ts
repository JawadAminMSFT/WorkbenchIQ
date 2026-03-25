/**
 * API client for the Commercial Brokerage workbench.
 * Follows the same pattern as api.ts — relative URLs routed through the Next.js proxy.
 */

import type {
  DashboardMetrics,
  Client,
  CreateClientRequest,
  Submission,
  CreateSubmissionRequest,
  ResearchBrief,
} from './broker-types';

const API_BASE_URL = '';

class BrokerAPIError extends Error {
  constructor(
    public status: number,
    message: string,
    public details?: unknown
  ) {
    super(message);
    this.name = 'BrokerAPIError';
  }
}

async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new BrokerAPIError(response.status, response.statusText, errorData);
  }

  return response.json();
}

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------

export async function getBrokerDashboard(): Promise<DashboardMetrics> {
  return apiFetch<DashboardMetrics>('/api/broker/dashboard');
}

// ---------------------------------------------------------------------------
// Clients
// ---------------------------------------------------------------------------

export async function getClients(): Promise<Client[]> {
  return apiFetch<Client[]>('/api/broker/clients');
}

export async function getClient(clientId: string): Promise<Client> {
  return apiFetch<Client>(`/api/broker/clients/${clientId}`);
}

export async function createClient(
  data: CreateClientRequest
): Promise<Client> {
  return apiFetch<Client>('/api/broker/clients', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ---------------------------------------------------------------------------
// Submissions
// ---------------------------------------------------------------------------

export async function getClientSubmissions(clientId: string): Promise<Submission[]> {
  return apiFetch<Submission[]>(`/api/broker/clients/${clientId}/submissions`);
}

export async function getSubmission(
  submissionId: string
): Promise<Submission> {
  return apiFetch<Submission>(`/api/broker/submissions/${submissionId}`);
}

export async function createSubmission(
  data: CreateSubmissionRequest
): Promise<Submission> {
  return apiFetch<Submission>('/api/broker/submissions', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ---------------------------------------------------------------------------
// Quote upload (multipart form)
// ---------------------------------------------------------------------------

export async function uploadQuote(
  submissionId: string,
  file: File,
  carrierName: string
): Promise<{ id: string; filename: string }> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('carrier_name', carrierName);

  const url = `${API_BASE_URL}/api/broker/submissions/${submissionId}/quotes`;
  const response = await fetch(url, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new BrokerAPIError(response.status, response.statusText, errorData);
  }

  return response.json();
}

// ---------------------------------------------------------------------------
// Client Research
// ---------------------------------------------------------------------------

export async function runClientResearch(
  clientId: string,
  companyName: string
): Promise<ResearchBrief> {
  return apiFetch<ResearchBrief>(
    `/api/broker/clients/${clientId}/research`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ company_name: companyName }),
    }
  );
}
