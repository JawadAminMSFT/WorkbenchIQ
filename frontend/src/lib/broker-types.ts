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

// Cached research brief stored on Client object
export interface ClientResearchBrief {
  company_overview: string;
  financials_summary: string;
  industry_risk_profile: string;
  insurance_needs: string[];
  carrier_appetite_matches: string[];
  recent_news: string[];
  citations: string[];
  _error?: string;
  _raw?: string;
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
  research_brief?: ClientResearchBrief | null;
  contacts: Array<{ name?: string; email?: string; phone?: string; role?: string }>;
  policies: Array<{
    policy_number: string;
    carrier: string;
    line_of_business: string;
    status: string;
    effective_date: string;
    expiration_date: string;
    premium: string;
  }>;
  claims_history: Array<{
    claim_number: string;
    date: string;
    type: string;
    amount: string;
    status: string;
  }>;
  carrier_contacts: Array<{
    name: string;
    carrier: string;
    email: string;
    phone: string;
    role: string;
  }>;
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
  effective_date?: string | null;
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
  submission_id: string;
  document_type: string;
  file_name: string;
  blob_url: string;
  extracted_fields: Record<string, unknown>;
  confidence_scores: Record<string, number>;
  uploaded_at: string;
}

export interface CarrierProfile {
  id: string;
  carrier_name: string;
  amb_number: string;
  naic_code: string;
  financial_strength_rating: string;
  issuer_credit_rating: string;
  rating_outlook: string;
  [key: string]: unknown;
}

export interface GeneratePackageResponse {
  submission_id: string;
  status: string;
  generated_at: string;
  client: {
    id: string;
    name: string;
    industry_code: string;
    headquarters_address: string;
  };
  submission_details: {
    line_of_business: string;
    effective_date: string;
    expiration_date: string;
    total_insured_value: string;
    coverage_requested: Record<string, unknown>;
    submitted_carriers: string[];
  };
  acord_fields: {
    acord_125: Record<string, unknown>;
    acord_140: Record<string, unknown>;
    confidence: Record<string, number>;
  };
  documents: Array<{
    id: string;
    document_type: string;
    file_name: string;
    uploaded_at: string;
  }>;
  quotes_summary: Array<{
    id: string;
    carrier_name: string;
    annual_premium: string;
    status: string;
  }>;
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
  acord_field_sources: Record<string, string>;
  sent_at: string | null;
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

  // Business Overview
  business_description: string;
  headquarters: string;
  year_founded: number | null;
  employee_count: number | null;
  ownership_type: string;
  key_operations: string[];

  // Financial Summary
  annual_revenue: string;
  revenue_trend: string; // "Growing" | "Stable" | "Declining"
  credit_rating: string;
  financial_highlights: string[];

  // Industry Risk Profile
  naics_code: string;
  industry_sector: string;
  common_perils: string[];
  loss_frequency: string; // "Low" | "Moderate" | "High"
  risk_factors: string[];

  // Insurance Needs
  insurance_needs: Array<{
    line: string;
    priority: string; // "Primary" | "Required" | "Recommended" | "Optional"
    estimated_premium: string;
    rationale: string;
  }>;

  // Carrier Matches
  carrier_matches: Array<{
    carrier: string;
    rating: string;
    appetite: string; // "Strong" | "Good" | "Moderate" | "Limited"
    rationale: string;
    fsr?: string;
    icr?: string;
    outlook?: string;
    balance_sheet_strength?: string;
    operating_performance?: string;
    combined_ratio?: string;
    nwp_to_surplus_ratio?: string;
  }>;

  // Recent News
  recent_news: Array<{
    date: string;
    headline: string;
    source: string;
  }>;

  // Metadata
  citations: string[];
  citation_types?: Record<string, string>;
  confidence_level: string; // "High" | "Medium" | "Low"
  field_confidence?: Record<string, string>;
  data_sources: string[];
  generated_at: string;

  // Legacy field for backward compatibility
  brief?: string;
  sources?: string[];
}

// Compare response from POST /api/broker/submissions/{id}/compare
export interface CompareResponse {
  comparison_table: Array<{
    quote_id: string;
    carrier_name: string;
    annual_premium: string;
    total_insured_value: string;
    deductible: string;
    rating: string;
    coverage_adequacy: string;
    placement_score: number;
  }>;
  recommendation: string;
  placement_scores: Array<{
    quote_id: string;
    carrier_name: string;
    placement_score: number;
    placement_rank: number;
    recommendation_rationale: string;
    coverage_gaps: string[];
    premium_percentile: string;
  }>;
}
