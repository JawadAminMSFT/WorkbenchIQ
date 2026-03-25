/**
 * TypeScript interfaces for the Commercial Brokerage workbench.
 * Mirrors the backend API models at /api/broker/*.
 */

// Dashboard metrics from GET /api/broker/dashboard
export interface DashboardMetrics {
  total_accounts: number;
  total_bound_premium: string;
  open_submissions: number;
  renewals_due_90_days: number;
  stale_submissions: number;
}

// Client from GET /api/broker/clients
export interface Client {
  id: string;
  name: string;
  industry_code: string;
  business_type: string;
  years_in_business?: number | null;
  annual_revenue: string;
  employee_count?: number | null;
  headquarters_address: string;
  property_locations: string[];
  renewal_date?: string | null;
  broker_notes: string;
  research_brief?: string | null;
  contacts: Array<{ name?: string; email?: string; phone?: string; role?: string }>;
  created_at: string;
  updated_at: string;
}

export interface CreateClientRequest {
  name: string;
  industry_code: string;
  business_type: string;
  years_in_business?: number;
  annual_revenue: string;
  employee_count?: number;
  headquarters_address: string;
  renewal_date?: string;
  broker_notes?: string;
  contacts?: Array<{ name?: string; email?: string; phone?: string; role?: string }>;
}

// Quote fields — values are dollar strings like "$38,750"
export interface QuoteFields {
  annual_premium?: string;
  total_insured_value?: string;
  building_limit?: string;
  contents_limit?: string;
  business_interruption_limit?: string;
  deductible?: string;
  flood_sublimit?: string;
  earthquake_sublimit?: string;
  named_perils_exclusions?: string[];
  special_conditions?: string[];
  policy_period?: string;
  carrier_am_best_rating?: string;
  quote_reference_number?: string;
  expiry_date?: string | null;
  underwriter?: string;
  [key: string]: unknown;
}

export interface QuoteScoring {
  placement_score: number;
  placement_rank: number;
  recommendation_rationale: string;
  coverage_adequacy: string;
  coverage_gaps: string[];
  premium_percentile: string;
}

// Quote from carrier (nested in submission)
export interface Quote {
  id: string;
  submission_id: string;
  carrier_name: string;
  source_format: string;
  source_file_name: string;
  received_date: string | null;
  status: string;
  fields: QuoteFields;
  scoring: QuoteScoring;
  confidence_scores: Record<string, number>;
  created_at: string;
}

export interface SubmissionDocument {
  id: string;
  filename: string;
  type: string;
  uploaded_at: string;
  status: string;
  carrier_name?: string;
}

// Submission from GET /api/broker/submissions/{id}
export interface Submission {
  id: string;
  client_id: string;
  line_of_business: string;
  acord_form_types: string[];
  status: string;
  effective_date: string;
  expiration_date: string;
  total_insured_value: string;
  coverage_requested: Record<string, unknown>;
  submitted_carriers: string[];
  documents: SubmissionDocument[];
  quotes: Quote[];
  submission_date: string | null;
  created_at: string;
  updated_at: string;
  acord_125_fields: Record<string, unknown>;
  acord_140_fields: Record<string, unknown>;
  acord_field_confidence: Record<string, number>;
}

export interface CreateSubmissionRequest {
  client_id: string;
  line_of_business: string;
  effective_date: string;
  expiration_date: string;
  total_insured_value: string;
}

// Research brief from POST /api/broker/clients/{id}/research
export interface ResearchBrief {
  company_name: string;
  brief: string;
  sources: string[];
}
