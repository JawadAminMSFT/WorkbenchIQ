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
  CompareResponse,
  SubmissionDocument,
  CarrierProfile,
  GeneratePackageResponse,
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

export async function getClientDocuments(
  clientId: string
): Promise<SubmissionDocument[]> {
  return apiFetch<SubmissionDocument[]>(`/api/broker/clients/${clientId}/documents`);
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
  companyName: string,
  documentIds?: string[]
): Promise<ResearchBrief> {
  return apiFetch<ResearchBrief>(
    `/api/broker/clients/${clientId}/research`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        company_name: companyName,
        document_ids: documentIds || [],
      }),
    }
  );
}

export interface ResearchHistoryEntry {
  id: string;
  generated_at: string;
  company_name: string;
  confidence_level: string;
  data_sources: string[];
  brief: ResearchBrief;
}

export async function getResearchHistory(
  clientId: string
): Promise<ResearchHistoryEntry[]> {
  return apiFetch<ResearchHistoryEntry[]>(
    `/api/broker/clients/${clientId}/research-history`
  );
}

export async function updateResearchBrief(
  clientId: string,
  updates: Partial<ResearchBrief>
): Promise<ResearchBrief> {
  return apiFetch<ResearchBrief>(
    `/api/broker/clients/${clientId}/research-brief`,
    {
      method: 'PUT',
      body: JSON.stringify(updates),
    }
  );
}

// ---------------------------------------------------------------------------
// Quote Comparison
// ---------------------------------------------------------------------------

export interface CompareWeights {
  premium_weight: number;
  coverage_weight: number;
  financial_weight: number;
  completeness_weight: number;
}

export async function runQuoteComparison(
  submissionId: string,
  weights?: CompareWeights
): Promise<CompareResponse> {
  const body = weights ? { weights } : undefined;
  return apiFetch<CompareResponse>(
    `/api/broker/submissions/${submissionId}/compare`,
    {
      method: 'POST',
      ...(body ? { body: JSON.stringify(body) } : {}),
    }
  );
}

// ---------------------------------------------------------------------------
// Document Upload (multipart form)
// ---------------------------------------------------------------------------

export async function uploadDocument(
  submissionId: string,
  file: File,
  documentType: string
): Promise<SubmissionDocument> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('document_type', documentType);

  const url = `${API_BASE_URL}/api/broker/submissions/${submissionId}/documents`;
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
// Carriers
// ---------------------------------------------------------------------------

export async function getCarriers(): Promise<CarrierProfile[]> {
  return apiFetch<CarrierProfile[]>('/api/broker/carriers');
}

// ---------------------------------------------------------------------------
// ACORD Extraction
// ---------------------------------------------------------------------------

export async function extractAcordFields(
  submissionId: string
): Promise<{
  submission_id: string;
  acord_125: Record<string, unknown>;
  acord_140: Record<string, unknown>;
  confidence: Record<string, number>;
  fields_extracted: number;
}> {
  return apiFetch(`/api/broker/submissions/${submissionId}/extract-acord`, {
    method: 'POST',
  });
}

// ---------------------------------------------------------------------------
// ACORD Field Updates
// ---------------------------------------------------------------------------

export async function updateAcordFields(
  submissionId: string,
  acord125Fields?: Record<string, unknown>,
  acord140Fields?: Record<string, unknown>
): Promise<{ submission_id: string; updated_at: string }> {
  return apiFetch(`/api/broker/submissions/${submissionId}/acord-fields`, {
    method: 'PUT',
    body: JSON.stringify({
      acord_125_fields: acord125Fields,
      acord_140_fields: acord140Fields,
    }),
  });
}

// ---------------------------------------------------------------------------
// Submission Updates
// ---------------------------------------------------------------------------

export async function updateSubmission(
  submissionId: string,
  data: Partial<Submission>
): Promise<Submission> {
  return apiFetch<Submission>(`/api/broker/submissions/${submissionId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

// ---------------------------------------------------------------------------
// Generate Submission Package
// ---------------------------------------------------------------------------

export async function generatePackage(
  submissionId: string,
  carriers: string[]
): Promise<GeneratePackageResponse> {
  return apiFetch<GeneratePackageResponse>(
    `/api/broker/submissions/${submissionId}/generate-package`,
    {
      method: 'POST',
      body: JSON.stringify({ carriers }),
    }
  );
}

// ---------------------------------------------------------------------------
// Mark Submission as Sent
// ---------------------------------------------------------------------------

export async function markSubmissionSent(
  submissionId: string,
  carriers: string[]
): Promise<{ submission_id: string; status: string; sent_at: string; submitted_carriers: string[] }> {
  return apiFetch(`/api/broker/submissions/${submissionId}/mark-sent`, {
    method: 'POST',
    body: JSON.stringify({ carriers }),
  });
}
