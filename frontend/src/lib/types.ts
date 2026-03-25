// API types matching the Python backend data structures

// ============================================================================
// Persona Types
// ============================================================================

/**
 * Persona definition from the backend
 */
export interface Persona {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  enabled: boolean;
}

// ============================================================================
// Application Types
// ============================================================================

export interface StoredFile {
  filename: string;
  path: string;
  url: string | null;
}

export interface ConfidenceSummary {
  total_fields: number;
  average_confidence: number;
  high_confidence_count: number;
  medium_confidence_count: number;
  low_confidence_count: number;
  high_confidence_fields: Record<string, unknown>[];
  medium_confidence_fields: Record<string, unknown>[];
  low_confidence_fields: Record<string, unknown>[];
}

export interface ExtractedField {
  field_name: string;
  value: unknown;
  confidence: number;
  page_number?: number;
  bounding_box?: number[];
  source_text?: string;
  source_file?: string;
}

export interface MarkdownPage {
  file: string;
  page_number: number;
  markdown: string;
}

// LLM Output structures
export interface ParsedOutput {
  summary?: string;
  key_fields?: { label: string; value: string }[];
  risk_assessment?: string;
  underwriting_action?: string;
  [key: string]: unknown;
}

export interface SubsectionOutput {
  section: string;
  subsection: string;
  raw: string;
  parsed: ParsedOutput;
  usage?: {
    prompt_tokens?: number;
    completion_tokens?: number;
    total_tokens?: number;
  };
}

export interface LLMOutputs {
  application_summary?: {
    customer_profile?: SubsectionOutput;
    existing_policies?: SubsectionOutput;
    [key: string]: SubsectionOutput | undefined;
  };
  medical_summary?: {
    family_history?: SubsectionOutput;
    hypertension?: SubsectionOutput;
    high_cholesterol?: SubsectionOutput;
    other_medical_findings?: SubsectionOutput;
    other_risks?: SubsectionOutput;
    // Deep dive subsections (populated by /analyze)
    body_system_review?: SubsectionOutput;
    pending_investigations?: SubsectionOutput;
    last_office_visit?: SubsectionOutput;
    abnormal_labs?: SubsectionOutput;
    latest_vitals?: SubsectionOutput;
    [key: string]: SubsectionOutput | undefined;
  };
  requirements?: {
    requirements_summary?: SubsectionOutput;
    [key: string]: SubsectionOutput | undefined;
  };
  [key: string]: Record<string, SubsectionOutput | undefined> | undefined;
}

// ============================================================================
// Body System Deep Dive Types
// ============================================================================

export type BodyRegion = 'head' | 'chest' | 'abdomen' | 'pelvis' | 'joints_spine' | 'extremities' | 'skin' | 'systemic';
export type Severity = 'high' | 'moderate' | 'low' | 'normal';
export type DiagnosisStatus = 'active' | 'resolved' | 'monitoring' | 'unknown';
export type InvestigationType = 'test' | 'referral' | 'consult' | 'imaging' | 'procedure';
export type Urgency = 'high' | 'medium' | 'low';

export interface TreatmentEntry {
  description: string;
  date: string;
  page_references: number[];
}

export interface ConsultEntry {
  specialist: string;
  date: string;
  summary: string;
  page_references: number[];
}

export interface ImagingEntry {
  type: string;
  date: string;
  result: string;
  page_references: number[];
}

export interface DiagnosisEntry {
  name: string;
  date_diagnosed: string;
  status: DiagnosisStatus;
  page_references: number[];
  treatments: TreatmentEntry[];
  consults: ConsultEntry[];
  imaging: ImagingEntry[];
}

export interface BodySystemEntry {
  system_code: string;
  system_name: string;
  body_region: BodyRegion;
  severity: Severity;
  diagnoses: DiagnosisEntry[];
}

export interface BodySystemReviewParsed {
  body_systems: BodySystemEntry[];
}

export interface PendingInvestigation {
  date: string;
  description: string;
  type: InvestigationType;
  urgency: Urgency;
  page_references: number[];
}

export interface PendingInvestigationsParsed {
  pending_investigations: PendingInvestigation[];
  summary: string;
}

export interface LastOfficeVisitData {
  date: string;
  summary: string;
  follow_up_plans: string[];
  page_references: number[];
}

export interface LastLabsData {
  date: string;
  summary: string;
  page_references: number[];
}

export interface LastOfficeVisitParsed {
  last_office_visit: LastOfficeVisitData;
  last_labs: LastLabsData;
}

export interface AbnormalLabEntry {
  date: string;
  test_name: string;
  value: string;
  unit: string;
  reference_range: string;
  interpretation: string;
  page_references: number[];
}

export interface AbnormalLabsParsed {
  abnormal_labs: AbnormalLabEntry[];
}

export interface LatestVitalsData {
  date: string;
  blood_pressure: { systolic: number; diastolic: number } | null;
  heart_rate: number | null;
  weight: { value: number; unit: string } | null;
  height: { value: string; unit: string } | null;
  bmi: number | null;
  temperature: number | null;
  respiratory_rate: number | null;
  oxygen_saturation: number | null;
  page_references: number[];
}

export interface LatestVitalsParsed {
  latest_vitals: LatestVitalsData;
}

/** Aggregation of all deep dive data extracted from llm_outputs */
export interface DeepDiveData {
  bodySystemReview: BodySystemReviewParsed | null;
  pendingInvestigations: PendingInvestigationsParsed | null;
  lastOfficeVisit: LastOfficeVisitParsed | null;
  abnormalLabs: AbnormalLabsParsed | null;
  latestVitals: LatestVitalsParsed | null;
  familyHistory: ParsedOutput | null;
  hasData: boolean;
}

// Risk Analysis types (separate from standard LLM outputs)
export interface PolicyCitation {
  policy_id: string;
  criteria_id?: string;
  policy_name: string;
  matched_condition: string;
  applied_action?: string;
  rationale?: string;
}

export interface RiskFinding {
  category: string;
  finding: string;
  policy_id: string;
  criteria_id?: string;
  policy_name: string;
  matched_condition?: string;
  risk_level: string;
  action: string;
  rationale?: string;
}

export interface PremiumRecommendation {
  base_decision: string;
  loading_percentage: string;
  exclusions?: string[];
  conditions?: string[];
}

export interface RiskAnalysisResult {
  overall_risk_level: string;
  overall_rationale: string;
  findings: RiskFinding[];
  premium_recommendation: PremiumRecommendation;
  underwriting_action: string;
  confidence?: string;
  data_gaps?: string[];
}

export interface RiskAnalysis {
  timestamp?: string;
  raw?: string;
  parsed?: RiskAnalysisResult;
  usage?: {
    prompt_tokens?: number;
    completion_tokens?: number;
    total_tokens?: number;
  };
}

export interface BatchSummary {
  batch_num: number;
  page_start: number;
  page_end: number;
  page_count: number;
  summary: string;
}

export interface ApplicationMetadata {
  id: string;
  created_at: string;
  external_reference: string | null;
  status: 'pending' | 'extracted' | 'completed' | 'error';
  persona?: string;
  files: StoredFile[];
  document_markdown?: string;
  markdown_pages?: MarkdownPage[];
  cu_raw_result_path?: string;
  llm_outputs?: LLMOutputs;
  extracted_fields?: Record<string, ExtractedField>;
  confidence_summary?: ConfidenceSummary;
  analyzer_id_used?: string;
  risk_analysis?: RiskAnalysis;
  // Background processing status
  processing_status?: 'extracting' | 'analyzing' | 'error' | null;
  processing_error?: string | null;
  // Large document processing
  processing_mode?: 'standard' | 'large_document';
  condensed_context?: string;
  document_stats?: {
    size_bytes?: number;
    size_kb?: number;
    size_mb?: number;
    page_count?: number;
    estimated_tokens?: number;
  };
  batch_summaries?: BatchSummary[];
}

export interface ApplicationListItem {
  id: string;
  created_at: string;
  external_reference: string | null;
  status: string;
  persona?: string;
  summary_title?: string;
  processing_status?: 'extracting' | 'analyzing' | 'error' | null;
}

// Patient/Applicant structured data derived from extracted fields
export interface PatientInfo {
  name: string;
  gender: string;
  dateOfBirth: string;
  age: number | string;
  occupation: string;
  height: string;
  weight: string;
  bmi: number | string;
}

export interface LabResult {
  name: string;
  value: string;
  unit: string;
  date?: string;
}

export interface MedicalCondition {
  name: string;
  status: string;
  date?: string;
  details?: string;
}

export interface TimelineItem {
  date: string;
  type: 'condition' | 'medication' | 'test' | 'visit';
  title: string;
  description?: string;
  icon?: string;
  color?: string;
}

// Substance use tracking (tobacco, alcohol, drugs)
export interface SubstanceUse {
  tobacco: {
    date?: string;
    status: string;
    history?: string[];
  };
  alcohol: {
    found: boolean;
    details?: string;
  };
  marijuana: {
    found: boolean;
    details?: string;
  };
  substance_abuse: {
    date?: string;
    found: boolean;
    details?: string;
  };
}

export interface FamilyHistory {
  conditions: string[];
}

export interface Allergies {
  found: boolean;
  items?: string[];
}

export interface OccupationAvocation {
  occupation?: string;
  activities?: string[];
}

// ============================================================================
// Prompt Catalog Types
// ============================================================================

/**
 * Prompts organized by section and subsection
 */
export interface PromptsData {
  prompts: Record<string, Record<string, string>>;
}

/**
 * Single prompt response
 */
export interface PromptDetail {
  section: string;
  subsection: string;
  text: string;
}

/**
 * Response when updating/creating a prompt
 */
export interface PromptUpdateResponse {
  section: string;
  subsection: string;
  text: string;
  message: string;
}

// ============================================================================
// Content Understanding Analyzer Types
// ============================================================================

/**
 * Status of the custom analyzer
 */
export interface AnalyzerStatus {
  analyzer_id: string;
  exists: boolean;
  analyzer: Record<string, unknown> | null;
  confidence_scoring_enabled: boolean;
  default_analyzer_id: string;
}

/**
 * Information about an analyzer
 */
export interface AnalyzerInfo {
  id: string;
  type: 'prebuilt' | 'custom';
  media_type?: 'document' | 'image' | 'video';
  description: string;
  exists: boolean;
  persona?: string;
  persona_name?: string;
}

/**
 * List of available analyzers
 */
export interface AnalyzerList {
  analyzers: AnalyzerInfo[];
}

/**
 * Response when creating an analyzer
 */
export interface AnalyzerCreateResponse {
  message: string;
  analyzer_id: string;
  result: Record<string, unknown>;
}

/**
 * Field definition in the schema
 */
export interface FieldDefinition {
  type: string;
  description: string;
  method: string;
  estimateSourceAndConfidence: boolean;
}

/**
 * Schema for the custom analyzer fields
 */
export interface FieldSchema {
  schema: {
    name: string;
    fields: Record<string, FieldDefinition>;
  };
  field_count: number;
}

// ============================================================================
// Underwriting Policy Types
// ============================================================================

/**
 * Criteria within an underwriting policy
 */
export interface PolicyCriteriaItem {
  id: string;
  condition: string;
  risk_level: string;
  action: string;
  rationale: string;
}

/**
 * Modifying factor for a policy
 */
export interface ModifyingFactor {
  factor: string;
  impact: string;
}

/**
 * Underwriting policy definition
 */
export interface UnderwritingPolicy {
  id: string;
  category: string;
  subcategory: string;
  name: string;
  description: string;
  criteria: PolicyCriteriaItem[];
  modifying_factors?: ModifyingFactor[];
  references?: string[];
}

/**
 * Request to create a new policy
 */
export interface PolicyCreateRequest {
  id: string;
  category: string;
  subcategory: string;
  name: string;
  description: string;
  criteria?: PolicyCriteriaItem[];
  modifying_factors?: ModifyingFactor[];
  references?: string[];
}

/**
 * Request to update an existing policy
 */
export interface PolicyUpdateRequest {
  category?: string;
  subcategory?: string;
  name?: string;
  description?: string;
  criteria?: PolicyCriteriaItem[];
  modifying_factors?: ModifyingFactor[];
  references?: string[];
}

/**
 * Policy citation from LLM analysis
 */
export interface PolicyCitation {
  policy_id: string;
  policy_name: string;
  criteria_applied: string;
  finding: string;
  rating_impact: string;
}

/**
 * Extended parsed output with policy citations
 */
export interface ParsedOutputWithCitations extends ParsedOutput {
  policy_citations?: PolicyCitation[];
}

/**
 * Response from policy API endpoints
 */
export interface PoliciesResponse {
  policies: UnderwritingPolicy[];
  total: number;
}

export interface PolicyResponse {
  policy: UnderwritingPolicy;
  message?: string;
}

// ============================================================================
// Property Deep Dive Types (Mortgage)
// ============================================================================

export interface PropertyDeepDiveComparable {
  address: string;
  sold_price: number;
  sold_date: string;
  distance_km: number;
  bedrooms: number;
  bathrooms: number;
  living_area: number;
  price_psf: number;
  similarity_score: number;
}

export interface PropertyPriceTrend {
  area_name: string;
  avg_price_current: number;
  avg_price_1yr_ago: number;
  avg_price_3yr_ago: number;
  yoy_change_pct: number;
  cagr_3yr_pct: number;
  trend_direction: 'up' | 'down' | 'stable';
}

export interface PropertyFeature {
  category: string;
  feature: string;
  value: string;
  data_point_source?: string;
}

export interface PropertyPhoto {
  url: string;
  caption?: string;
  category: 'exterior' | 'interior' | 'aerial' | 'floorplan';
}

export interface PropertyDeepDiveData {
  property_summary: {
    address: string;
    property_type: string;
    purchase_price: number;
    appraised_value?: number;
    year_built?: number;
    lot_size?: string;
    living_area?: number;
    bedrooms?: number;
    bathrooms?: number;
    garages?: number;
    parking?: string;
  };
  risk_classification: 'low' | 'medium' | 'high';
  risk_rationale?: string;
  auto_appraisal_eligible: boolean;
  auto_appraisal_recommendation: string;
  comparable_sales: PropertyDeepDiveComparable[];
  price_trend: PropertyPriceTrend;
  property_features: PropertyFeature[];
  appraisal_data_points?: Record<string, string>;
  mls_listing_url?: string;
  mls_number?: string;
  photos: PropertyPhoto[];
  needs_physical_appraisal: boolean;
  physical_appraisal_reason?: string;
  warning?: string;
}
