/**
 * TypeScript interfaces for the Commercial Brokerage workbench.
 * Mirrors the backend API models at /api/broker/*.
 */

// Dashboard metrics from GET /api/broker/dashboard
export interface DashboardMetrics {
  total_accounts: number;
  total_bound_premium: number;
  open_submissions: number;
  renewals_due_90_days: number;
}

// Client from GET /api/broker/clients
export interface Client {
  id: string;
  company_name: string;
  industry: string;
  contact_name: string;
  contact_email: string;
  renewal_date: string;
  active_submissions: number;
  total_premium: number;
  status: 'active' | 'prospect' | 'inactive';
  created_at: string;
}

export interface CreateClientRequest {
  company_name: string;
  industry: string;
  contact_name: string;
  contact_email: string;
  renewal_date: string;
}

// Submission from GET /api/broker/submissions/{id}
export interface Submission {
  id: string;
  client_id: string;
  client_name: string;
  status: 'draft' | 'submitted' | 'quoted' | 'bound';
  coverage_type: string;
  effective_date: string;
  expiration_date: string;
  total_insured_value: number;
  acord_fields: AcordFieldGroup[];
  documents: SubmissionDocument[];
  quotes: Quote[];
  created_at: string;
  updated_at: string;
}

export interface CreateSubmissionRequest {
  client_id: string;
  coverage_type: string;
  effective_date: string;
  expiration_date: string;
  total_insured_value: number;
}

export interface AcordFieldGroup {
  form_type: 'ACORD 125' | 'ACORD 140';
  fields: AcordField[];
}

export interface AcordField {
  name: string;
  value: string | number | null;
  source_document: string;
  confidence: number;
  needs_review: boolean;
}

export interface SubmissionDocument {
  id: string;
  filename: string;
  type: 'application' | 'loss_run' | 'schedule' | 'quote' | 'other';
  uploaded_at: string;
  status: 'pending' | 'processed' | 'error';
  carrier_name?: string;
}

// Quote from carrier
export interface Quote {
  id: string;
  carrier_name: string;
  carrier_am_best: string;
  annual_premium: number;
  total_insured_value: number;
  building_limit: number;
  contents_limit: number;
  bi_limit: number;
  deductible: number;
  flood_sublimit: number;
  earthquake_sublimit: number;
  exclusions: string[];
  policy_period: string;
  uploaded_at: string;
}

// Comparison result from POST /api/broker/submissions/{id}/compare
export interface PlacementScoring {
  score: number;
  rank: number;
  factors: { name: string; impact: 'positive' | 'negative' | 'neutral'; detail: string }[];
}

export interface ComparisonResult {
  submission_id: string;
  carriers: {
    carrier_name: string;
    quote: Quote;
    placement: PlacementScoring;
  }[];
  recommendation: {
    carrier_name: string;
    rationale: string;
    confidence: number;
  };
}

// Research brief from POST /api/broker/clients/{id}/research
export interface ResearchBrief {
  client_id: string;
  company_name: string;
  sections: ResearchSection[];
  generated_at: string;
}

export interface ResearchSection {
  title: string;
  content: string;
  citations: { text: string; url: string }[];
  confidence: number;
}
