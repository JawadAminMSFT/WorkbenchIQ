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
    [key: string]: SubsectionOutput | undefined;
  };
  requirements?: {
    requirements_summary?: SubsectionOutput;
    [key: string]: SubsectionOutput | undefined;
  };
  [key: string]: Record<string, SubsectionOutput | undefined> | undefined;
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
}

export interface ApplicationListItem {
  id: string;
  created_at: string;
  external_reference: string | null;
  status: string;
  persona?: string;
  summary_title?: string;
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
  description: string;
  exists: boolean;
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
