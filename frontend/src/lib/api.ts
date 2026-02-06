/**
 * API client for communicating with the Python backend.
 * This module provides functions to interact with the WorkbenchIQ backend.
 */

import type {
  ApplicationMetadata,
  ApplicationListItem,
  PatientInfo,
  LabResult,
  MedicalCondition,
  TimelineItem,
  SubstanceUse,
  FamilyHistory,
  ExtractedField,
  PromptsData,
  AnalyzerStatus,
  AnalyzerInfo,
  FieldSchema,
  Persona,
  UnderwritingPolicy,
  PolicyCreateRequest,
  PolicyUpdateRequest,
  PoliciesResponse,
  PolicyResponse,
} from './types';

// Backend API base URL - can be configured via environment variable
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Custom error class for API errors
 */
export class APIError extends Error {
  constructor(
    public status: number,
    message: string,
    public details?: unknown
  ) {
    super(message);
    this.name = 'APIError';
  }
}

/**
 * Generic fetch wrapper with error handling
 */
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
    throw new APIError(response.status, response.statusText, errorData);
  }

  return response.json();
}

// ============================================================================
// Application Management APIs
// ============================================================================

/**
 * List all personas available in the system
 */
export async function listPersonas(): Promise<{ personas: Persona[] }> {
  return apiFetch<{ personas: Persona[] }>('/api/personas');
}

/**
 * Get a specific persona configuration
 */
export async function getPersona(personaId: string): Promise<Persona> {
  return apiFetch<Persona>(`/api/personas/${personaId}`);
}

/**
 * List all applications from the backend storage, optionally filtered by persona
 */
export async function listApplications(persona?: string): Promise<ApplicationListItem[]> {
  const params = persona ? `?persona=${persona}` : '';
  return apiFetch<ApplicationListItem[]>(`/api/applications${params}`);
}

/**
 * Get detailed metadata for a specific application
 */
export async function getApplication(appId: string): Promise<ApplicationMetadata> {
  return apiFetch<ApplicationMetadata>(`/api/applications/${appId}`);
}

/**
 * Create a new application with uploaded files
 */
export async function createApplication(
  files: File[],
  externalReference?: string,
  persona?: string
): Promise<ApplicationMetadata> {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  if (externalReference) {
    formData.append('external_reference', externalReference);
  }
  if (persona) {
    formData.append('persona', persona);
  }

  const response = await fetch(`${API_BASE_URL}/api/applications`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new APIError(response.status, response.statusText, errorData);
  }

  return response.json();
}

/**
 * Run content understanding extraction on an application
 * @param background If true, starts in background and returns immediately
 */
export async function runContentUnderstanding(
  appId: string,
  background: boolean = false
): Promise<ApplicationMetadata> {
  const params = background ? '?background=true' : '';
  return apiFetch<ApplicationMetadata>(`/api/applications/${appId}/extract${params}`, {
    method: 'POST',
  });
}

/**
 * Run underwriting prompts analysis on an application
 * @param background If true, starts in background and returns immediately
 */
export async function runUnderwritingAnalysis(
  appId: string,
  sections?: string[],
  background: boolean = false
): Promise<ApplicationMetadata> {
  const params = background ? '?background=true' : '';
  return apiFetch<ApplicationMetadata>(`/api/applications/${appId}/analyze${params}`, {
    method: 'POST',
    body: JSON.stringify({ sections }),
  });
}

/**
 * Start full processing (extraction + analysis) in background.
 * Returns immediately. Client should poll getApplication() for status updates.
 * @param processingMode - 'auto', 'large_document', or 'standard'
 */
export async function startProcessing(appId: string, processingMode?: string): Promise<ApplicationMetadata> {
  const url = processingMode 
    ? `/api/applications/${appId}/process?processing_mode=${processingMode}`
    : `/api/applications/${appId}/process`;
  return apiFetch<ApplicationMetadata>(url, {
    method: 'POST',
  });
}

// ============================================================================
// Data Transformation Helpers - Convert raw backend data to UI-friendly format
// ============================================================================

/**
 * Extract patient info from application metadata
 */
export function extractPatientInfo(app: ApplicationMetadata): PatientInfo {
  const fields = app.extracted_fields || {};
  
  const getValue = (key: string): string => {
    const field = Object.values(fields).find(
      (f) => f.field_name === key || f.field_name.includes(key)
    );
    return field?.value?.toString() || 'N/A';
  };

  const getNumericValue = (key: string): number | string => {
    const field = Object.values(fields).find(
      (f) => f.field_name === key || f.field_name.includes(key)
    );
    const val = field?.value;
    return typeof val === 'number' ? val : val?.toString() || 'N/A';
  };

  // Try to extract from extracted_fields first, then fall back to llm_outputs
  let name = getValue('ApplicantName');
  let dateOfBirth = getValue('DateOfBirth');
  
  // Parse from LLM outputs if not found
  const customerProfile = app.llm_outputs?.application_summary?.customer_profile?.parsed;
  if (customerProfile) {
    const keyFields = customerProfile.key_fields || [];
    for (const kf of keyFields) {
      if (kf.label.toLowerCase().includes('name') && name === 'N/A') {
        name = kf.value;
      }
      if (kf.label.toLowerCase().includes('birth') && dateOfBirth === 'N/A') {
        dateOfBirth = kf.value;
      }
    }
  }

  return {
    name,
    gender: getValue('Gender'),
    dateOfBirth,
    age: getNumericValue('Age'),
    occupation: getValue('Occupation'),
    height: getValue('Height'),
    weight: getValue('Weight'),
    bmi: getNumericValue('BMI'),
  };
}

/**
 * Extract lab results from application data
 */
export function extractLabResults(app: ApplicationMetadata): LabResult[] {
  const results: LabResult[] = [];
  const fields = app.extracted_fields || {};

  // Map extracted fields to lab results
  const labFieldMappings: Record<string, { name: string; unit: string }> = {
    LipidPanelResults: { name: 'Lipid Panel', unit: '' },
    BloodPressureReadings: { name: 'Blood Pressure', unit: 'mmHg' },
    PulseRate: { name: 'Pulse Rate', unit: 'bpm' },
    UrinalysisResults: { name: 'Urinalysis', unit: '' },
  };

  for (const [key, info] of Object.entries(labFieldMappings)) {
    const field = Object.values(fields).find((f) => f.field_name === key);
    if (field?.value) {
      results.push({
        name: info.name,
        value: field.value.toString(),
        unit: info.unit,
      });
    }
  }

  // Also extract from medical_summary LLM outputs
  const medicalSummary = app.llm_outputs?.medical_summary;
  
  // Hypertension - BP readings
  const hypertension = medicalSummary?.hypertension?.parsed;
  if (hypertension?.bp_readings && Array.isArray(hypertension.bp_readings)) {
    for (const bp of hypertension.bp_readings as Array<{ systolic?: string; diastolic?: string; date?: string }>) {
      results.push({
        name: 'Blood Pressure',
        value: `${bp.systolic || '?'}/${bp.diastolic || '?'}`,
        unit: 'mmHg',
        date: bp.date,
      });
    }
  }

  // Cholesterol - lipid panels
  const cholesterol = medicalSummary?.high_cholesterol?.parsed;
  if (cholesterol?.lipid_panels && Array.isArray(cholesterol.lipid_panels)) {
    for (const lp of cholesterol.lipid_panels as Array<{ total_cholesterol?: number; hdl?: number; ldl?: number; date?: string }>) {
      if (lp.total_cholesterol) {
        results.push({
          name: 'Total Cholesterol',
          value: lp.total_cholesterol.toString(),
          unit: 'mg/dL',
          date: lp.date,
        });
      }
      if (lp.hdl) {
        results.push({
          name: 'HDL Cholesterol',
          value: lp.hdl.toString(),
          unit: 'mg/dL',
          date: lp.date,
        });
      }
      if (lp.ldl) {
        results.push({
          name: 'LDL Cholesterol',
          value: lp.ldl.toString(),
          unit: 'mg/dL',
          date: lp.date,
        });
      }
    }
  }

  return results;
}

/**
 * Extract medical conditions from application data
 */
export function extractMedicalConditions(app: ApplicationMetadata): MedicalCondition[] {
  const conditions: MedicalCondition[] = [];
  
  const medicalSummary = app.llm_outputs?.medical_summary;
  if (!medicalSummary) return conditions;

  // Iterate through all medical summary sections
  for (const [sectionKey, section] of Object.entries(medicalSummary)) {
    if (!section?.parsed?.conditions || !Array.isArray(section.parsed.conditions)) continue;
    
    for (const cond of section.parsed.conditions as Array<{ name?: string; status?: string; date?: string; details?: string }>) {
      conditions.push({
        name: cond.name || sectionKey,
        status: cond.status || 'Unknown',
        date: cond.date,
        details: cond.details,
      });
    }
  }

  // Also check extracted fields
  const fields = app.extracted_fields || {};
  const medicalField = Object.values(fields).find(
    (f) => f.field_name === 'MedicalConditionsSummary'
  );
  if (medicalField?.value) {
    // Parse semicolon-separated conditions
    const condText = medicalField.value.toString();
    const items = condText.split(';').map((s) => s.trim()).filter(Boolean);
    for (const item of items) {
      // Check if not already added
      if (!conditions.some((c) => c.details?.includes(item))) {
        conditions.push({
          name: 'Medical Condition',
          status: 'Documented',
          details: item,
        });
      }
    }
  }

  return conditions;
}

/**
 * Build chronological timeline from application data
 */
export function buildTimeline(app: ApplicationMetadata): TimelineItem[] {
  const items: TimelineItem[] = [];
  
  // Add conditions from medical summary
  const conditions = extractMedicalConditions(app);
  for (const cond of conditions) {
    if (cond.date) {
      items.push({
        date: cond.date,
        type: 'condition',
        title: cond.name,
        description: cond.details,
        color: 'orange',
      });
    }
  }

  // Add medications
  const fields = app.extracted_fields || {};
  const medsField = Object.values(fields).find(
    (f) => f.field_name === 'CurrentMedicationsList'
  );
  if (medsField?.value) {
    items.push({
      date: 'Current',
      type: 'medication',
      title: 'Medications',
      description: medsField.value.toString(),
      color: 'blue',
    });
  }

  // Sort by date (most recent first)
  items.sort((a, b) => {
    if (a.date === 'Current') return -1;
    if (b.date === 'Current') return 1;
    return new Date(b.date).getTime() - new Date(a.date).getTime();
  });

  return items;
}

/**
 * Extract substance use information
 */
export function extractSubstanceUse(app: ApplicationMetadata): SubstanceUse {
  const fields = app.extracted_fields || {};
  
  const smokingField = Object.values(fields).find(
    (f) => f.field_name === 'SmokingStatus'
  );
  const alcoholField = Object.values(fields).find(
    (f) => f.field_name === 'AlcoholUse'
  );
  const drugField = Object.values(fields).find(
    (f) => f.field_name === 'DrugUse'
  );

  return {
    tobacco: {
      status: smokingField?.value?.toString() || 'Not found',
    },
    alcohol: {
      found: !!alcoholField?.value,
      details: alcoholField?.value?.toString(),
    },
    marijuana: {
      found: false, // Would need specific field
      details: undefined,
    },
    substance_abuse: {
      found: !!drugField?.value && drugField.value.toString().toLowerCase() !== 'no',
      details: drugField?.value?.toString(),
    },
  };
}

/**
 * Extract family history
 */
export function extractFamilyHistory(app: ApplicationMetadata): FamilyHistory {
  const conditions: string[] = [];
  
  // Check extracted fields
  const fields = app.extracted_fields || {};
  const familyField = Object.values(fields).find(
    (f) => f.field_name === 'FamilyHistorySummary'
  );
  if (familyField?.value) {
    const items = familyField.value.toString().split(';').map((s) => s.trim()).filter(Boolean);
    conditions.push(...items);
  }

  // Also check LLM outputs
  const familyHistory = app.llm_outputs?.medical_summary?.family_history?.parsed;
  if (familyHistory?.conditions && Array.isArray(familyHistory.conditions)) {
    for (const cond of familyHistory.conditions as Array<string | { name?: string }>) {
      const text = typeof cond === 'string' ? cond : cond.name || JSON.stringify(cond);
      if (!conditions.includes(text)) {
        conditions.push(text);
      }
    }
  }

  return { conditions };
}

/**
 * Get extracted fields with confidence scores
 */
export function getFieldsWithConfidence(app: ApplicationMetadata): ExtractedField[] {
  const fields = app.extracted_fields || {};
  return Object.values(fields).sort((a, b) => b.confidence - a.confidence);
}

/**
 * Convert PascalCase to snake_case
 */
function toSnakeCase(str: string): string {
  return str.replace(/([A-Z])/g, '_$1').toLowerCase().replace(/^_/, '');
}

/**
 * Get citation data for a specific field by name
 * Searches extracted_fields for matching field name
 * Also tries case-insensitive and snake_case matching
 */
export function getCitation(
  app: ApplicationMetadata,
  fieldName: string
): ExtractedField | undefined {
  const fields = app.extracted_fields || {};
  
  // Direct lookup by field_name property
  const direct = Object.values(fields).find(
    (f) => f.field_name === fieldName
  );
  if (direct && direct.source_file) return direct;
  
  // Try snake_case version (e.g., ApplicantName -> applicant_name)
  const snakeCase = toSnakeCase(fieldName);
  const snakeMatch = Object.values(fields).find(
    (f) => f.field_name === snakeCase
  );
  if (snakeMatch && snakeMatch.source_file) return snakeMatch;
  
  // Try case-insensitive match
  const lowerFieldName = fieldName.toLowerCase();
  const caseInsensitive = Object.values(fields).find(
    (f) => f.field_name.toLowerCase() === lowerFieldName
  );
  if (caseInsensitive && caseInsensitive.source_file) return caseInsensitive;
  
  // Try partial match (for fields prefixed with filename)
  for (const field of Object.values(fields)) {
    if ((field.field_name.endsWith(fieldName) || field.field_name.includes(fieldName)) && field.source_file) {
      return field;
    }
  }
  
  // Final fallback: return direct match even if no source_file (for confidence display)
  if (direct) return direct;
  if (snakeMatch) return snakeMatch;
  if (caseInsensitive) return caseInsensitive;
  
  return undefined;
}

/**
 * Get multiple citations by field names
 * Returns a map of fieldName -> ExtractedField
 */
export function getCitations(
  app: ApplicationMetadata,
  fieldNames: string[]
): Record<string, ExtractedField | undefined> {
  const result: Record<string, ExtractedField | undefined> = {};
  for (const name of fieldNames) {
    result[name] = getCitation(app, name);
  }
  return result;
}

/**
 * Calculate BMI from height and weight if not provided
 */
export function calculateBMI(height: string, weight: string): number | null {
  // Parse height (supports formats like "5'10\"" or "178 cm")
  let heightInMeters: number | null = null;
  
  const ftInMatch = height.match(/(\d+)'?\s*(\d+)?"/);
  if (ftInMatch) {
    const feet = parseInt(ftInMatch[1]);
    const inches = parseInt(ftInMatch[2] || '0');
    heightInMeters = (feet * 12 + inches) * 0.0254;
  } else {
    const cmMatch = height.match(/(\d+)\s*cm/i);
    if (cmMatch) {
      heightInMeters = parseInt(cmMatch[1]) / 100;
    }
  }

  // Parse weight (supports "165 lb" or "75 kg")
  let weightInKg: number | null = null;
  
  const lbMatch = weight.match(/(\d+)\s*lb/i);
  if (lbMatch) {
    weightInKg = parseInt(lbMatch[1]) * 0.453592;
  } else {
    const kgMatch = weight.match(/(\d+)\s*kg/i);
    if (kgMatch) {
      weightInKg = parseInt(kgMatch[1]);
    }
  }

  if (heightInMeters && weightInKg) {
    return Math.round((weightInKg / (heightInMeters * heightInMeters)) * 10) / 10;
  }

  return null;
}

// ============================================================================
// Prompt Catalog APIs
// ============================================================================

/**
 * Get all prompts organized by section and subsection
 */
export async function getPrompts(persona?: string): Promise<PromptsData> {
  const params = persona ? `?persona=${persona}` : '';
  return apiFetch<PromptsData>(`/api/prompts${params}`);
}

/**
 * Get a specific prompt by section and subsection
 */
export async function getPrompt(
  section: string,
  subsection: string,
  persona?: string
): Promise<{ section: string; subsection: string; text: string }> {
  const params = persona ? `?persona=${persona}` : '';
  return apiFetch(`/api/prompts/${section}/${subsection}${params}`);
}

/**
 * Update a specific prompt
 */
export async function updatePrompt(
  section: string,
  subsection: string,
  text: string,
  persona?: string
): Promise<{ section: string; subsection: string; text: string; message: string }> {
  const params = persona ? `?persona=${persona}` : '';
  return apiFetch(`/api/prompts/${section}/${subsection}${params}`, {
    method: 'PUT',
    body: JSON.stringify({ text }),
  });
}

/**
 * Create a new prompt
 */
export async function createPrompt(
  section: string,
  subsection: string,
  text: string,
  persona?: string
): Promise<{ section: string; subsection: string; text: string; message: string }> {
  const params = persona ? `?persona=${persona}` : '';
  return apiFetch(`/api/prompts/${section}/${subsection}${params}`, {
    method: 'POST',
    body: JSON.stringify({ text }),
  });
}

/**
 * Delete a prompt (resets to default)
 */
export async function deletePrompt(
  section: string,
  subsection: string,
  persona?: string
): Promise<{ message: string }> {
  const params = persona ? `?persona=${persona}` : '';
  return apiFetch(`/api/prompts/${section}/${subsection}${params}`, {
    method: 'DELETE',
  });
}

// ============================================================================
// Content Understanding Analyzer APIs
// ============================================================================

/**
 * Get the status of the custom analyzer
 */
export async function getAnalyzerStatus(persona?: string): Promise<AnalyzerStatus> {
  const params = persona ? `?persona=${persona}` : '';
  return apiFetch<AnalyzerStatus>(`/api/analyzer/status${params}`);
}

/**
 * Get the field schema for the custom analyzer
 */
export async function getAnalyzerSchema(persona?: string): Promise<FieldSchema> {
  const params = persona ? `?persona=${persona}` : '';
  return apiFetch<FieldSchema>(`/api/analyzer/schema${params}`);
}

/**
 * List all available analyzers
 */
export async function listAnalyzers(): Promise<{ analyzers: AnalyzerInfo[] }> {
  return apiFetch<{ analyzers: AnalyzerInfo[] }>('/api/analyzer/list');
}

/**
 * Create or update the custom analyzer
 */
export async function createAnalyzer(
  analyzerId?: string,
  persona?: string,
  description?: string,
  mediaType?: string
): Promise<{ message: string; analyzer_id: string; result: Record<string, unknown> }> {
  return apiFetch('/api/analyzer/create', {
    method: 'POST',
    body: JSON.stringify({
      analyzer_id: analyzerId,
      persona,
      description,
      media_type: mediaType,
    }),
  });
}

/**
 * Delete a custom analyzer
 */
export async function deleteAnalyzer(
  analyzerId: string
): Promise<{ message: string }> {
  return apiFetch(`/api/analyzer/${analyzerId}`, {
    method: 'DELETE',
  });
}

// ============================================================================
// Underwriting Policy APIs
// ============================================================================

/**
 * Get all policies for a persona (underwriting or claims)
 */
export async function getPolicies(persona?: string): Promise<PoliciesResponse> {
  const params = persona ? `?persona=${encodeURIComponent(persona)}` : '';
  return apiFetch<PoliciesResponse>(`/api/policies${params}`);
}

/**
 * Get a specific policy by ID
 */
export async function getPolicy(policyId: string, persona?: string): Promise<UnderwritingPolicy> {
  const params = persona ? `?persona=${encodeURIComponent(persona)}` : '';
  return apiFetch<UnderwritingPolicy>(`/api/policies/${policyId}${params}`);
}

/**
 * Get policies by category
 */
export async function getPoliciesByCategory(category: string): Promise<PoliciesResponse & { category: string }> {
  return apiFetch<PoliciesResponse & { category: string }>(`/api/policies/category/${category}`);
}

/**
 * Create a new policy
 */
export async function createPolicy(policy: PolicyCreateRequest): Promise<PolicyResponse> {
  return apiFetch<PolicyResponse>('/api/policies', {
    method: 'POST',
    body: JSON.stringify(policy),
  });
}

/**
 * Update an existing policy
 */
export async function updatePolicy(policyId: string, update: PolicyUpdateRequest): Promise<PolicyResponse> {
  return apiFetch<PolicyResponse>(`/api/policies/${policyId}`, {
    method: 'PUT',
    body: JSON.stringify(update),
  });
}

/**
 * Delete a policy
 */
export async function deletePolicy(policyId: string): Promise<{ success: boolean; message: string }> {
  return apiFetch<{ success: boolean; message: string }>(`/api/policies/${policyId}`, {
    method: 'DELETE',
  });
}

// ============================================================================
// RAG Index Management APIs
// ============================================================================

export interface ReindexResponse {
  status: string;
  policies_indexed?: number;
  chunks_stored?: number;
  total_time_seconds?: number;
  error?: string;
}

export interface IndexStats {
  status: string;
  total_chunks?: number;
  chunk_count?: number;  // Alternative field name used by some endpoints
  policy_count?: number;
  chunks_by_type?: Record<string, number>;
  chunks_by_category?: Record<string, number>;
  table?: string;
  last_updated?: string;
  message?: string;
  error?: string;
}

/**
 * Reindex all policies for RAG search (persona-aware)
 * @param persona - The persona to reindex policies for (underwriting, life_health_claims, automotive_claims, property_casualty_claims)
 * @param force - Whether to force delete existing chunks before reindexing
 */
export async function reindexAllPolicies(force: boolean = true, persona: string = 'underwriting'): Promise<ReindexResponse> {
  return apiFetch<ReindexResponse>(`/api/admin/policies/reindex?persona=${encodeURIComponent(persona)}`, {
    method: 'POST',
    body: JSON.stringify({ force }),
  });
}

/**
 * Reindex a single policy
 */
export async function reindexPolicy(policyId: string): Promise<ReindexResponse> {
  return apiFetch<ReindexResponse>(`/api/admin/policies/${policyId}/reindex`, {
    method: 'POST',
  });
}

/**
 * Get RAG index statistics (persona-aware)
 * @param persona - The persona to get index stats for
 */
export async function getIndexStats(persona: string = 'underwriting'): Promise<IndexStats> {
  return apiFetch<IndexStats>(`/api/admin/policies/index-stats?persona=${encodeURIComponent(persona)}`);
}

// ============================================================================
// Claims Policy Admin APIs (Deprecated - use reindexAllPolicies/getIndexStats with persona param)
// ============================================================================

/**
 * @deprecated Use reindexAllPolicies(force, 'automotive_claims') instead
 */
export async function reindexClaimsPolicies(force: boolean = true): Promise<ReindexResponse> {
  return reindexAllPolicies(force, 'automotive_claims');
}

/**
 * @deprecated Use getIndexStats('automotive_claims') instead
 */
export async function getClaimsIndexStats(): Promise<IndexStats> {
  return getIndexStats('automotive_claims');
}

// ============================================================================
// Glossary APIs
// ============================================================================

/**
 * Glossary term structure
 */
export interface GlossaryTerm {
  abbreviation: string;
  meaning: string;
  context?: string;
  examples?: string[];
  category?: string;
  category_id?: string;
}

/**
 * Glossary category structure
 */
export interface GlossaryCategory {
  id: string;
  name: string;
  terms: GlossaryTerm[];
}

/**
 * Persona glossary structure
 */
export interface PersonaGlossary {
  persona: string;
  name: string;
  description: string;
  categories: GlossaryCategory[];
  total_terms: number;
}

/**
 * Glossary summary for listing
 */
export interface GlossarySummary {
  persona: string;
  name: string;
  description: string;
  term_count: number;
  category_count: number;
}

/**
 * List all available glossaries
 */
export async function listGlossaries(): Promise<{ glossaries: GlossarySummary[] }> {
  return apiFetch<{ glossaries: GlossarySummary[] }>('/api/glossary');
}

/**
 * Get the full glossary for a specific persona
 */
export async function getGlossary(persona: string): Promise<PersonaGlossary> {
  return apiFetch<PersonaGlossary>(`/api/glossary/${persona}`);
}

/**
 * Search for terms in a glossary
 */
export async function searchGlossary(
  persona: string,
  query: string,
  category?: string
): Promise<{ results: GlossaryTerm[]; count: number }> {
  const params = new URLSearchParams({ q: query });
  if (category) params.append('category', category);
  return apiFetch<{ results: GlossaryTerm[]; count: number }>(
    `/api/glossary/${persona}/search?${params.toString()}`
  );
}

/**
 * Create a new glossary category
 */
export async function createGlossaryCategory(
  persona: string,
  id: string,
  name: string
): Promise<{ category: GlossaryCategory; message: string }> {
  return apiFetch<{ category: GlossaryCategory; message: string }>(
    `/api/glossary/${persona}/categories`,
    {
      method: 'POST',
      body: JSON.stringify({ id, name }),
    }
  );
}

/**
 * Update a glossary category
 */
export async function updateGlossaryCategory(
  persona: string,
  categoryId: string,
  name: string
): Promise<{ category: GlossaryCategory; message: string }> {
  return apiFetch<{ category: GlossaryCategory; message: string }>(
    `/api/glossary/${persona}/categories/${categoryId}`,
    {
      method: 'PUT',
      body: JSON.stringify({ name }),
    }
  );
}

/**
 * Delete a glossary category (must be empty)
 */
export async function deleteGlossaryCategory(
  persona: string,
  categoryId: string
): Promise<{ message: string }> {
  return apiFetch<{ message: string }>(
    `/api/glossary/${persona}/categories/${categoryId}`,
    { method: 'DELETE' }
  );
}

/**
 * Create a new glossary term
 */
export async function createGlossaryTerm(
  persona: string,
  categoryId: string,
  term: Omit<GlossaryTerm, 'category' | 'category_id'>
): Promise<{ term: GlossaryTerm; message: string }> {
  return apiFetch<{ term: GlossaryTerm; message: string }>(
    `/api/glossary/${persona}/terms/${categoryId}`,
    {
      method: 'POST',
      body: JSON.stringify(term),
    }
  );
}

/**
 * Update an existing glossary term
 */
export async function updateGlossaryTerm(
  persona: string,
  abbreviation: string,
  updates: Partial<GlossaryTerm>
): Promise<{ term: GlossaryTerm; message: string }> {
  return apiFetch<{ term: GlossaryTerm; message: string }>(
    `/api/glossary/${persona}/terms/${encodeURIComponent(abbreviation)}`,
    {
      method: 'PUT',
      body: JSON.stringify(updates),
    }
  );
}

/**
 * Delete a glossary term
 */
export async function deleteGlossaryTerm(
  persona: string,
  abbreviation: string
): Promise<{ message: string }> {
  return apiFetch<{ message: string }>(
    `/api/glossary/${persona}/terms/${encodeURIComponent(abbreviation)}`,
    { method: 'DELETE' }
  );
}

/**
 * Get formatted glossary for prompt injection
 */
export async function getFormattedGlossary(
  persona: string,
  options?: {
    maxTerms?: number;
    categories?: string[];
    formatType?: 'markdown' | 'list';
    includeHeaders?: boolean;
  }
): Promise<{ formatted: string }> {
  const params = new URLSearchParams();
  if (options?.maxTerms) params.append('max_terms', options.maxTerms.toString());
  if (options?.categories) params.append('categories', options.categories.join(','));
  if (options?.formatType) params.append('format_type', options.formatType);
  if (options?.includeHeaders !== undefined) params.append('include_headers', options.includeHeaders.toString());
  
  const queryString = params.toString();
  return apiFetch<{ formatted: string }>(
    `/api/glossary/${persona}/formatted${queryString ? `?${queryString}` : ''}`
  );
}

// ============================================================================
// Automotive Claims API
// ============================================================================

/**
 * Submit a new automotive claim
 */
export interface ClaimSubmitRequest {
  claimant_name: string;
  policy_number: string;
  incident_date: string;
  incident_description: string;
  vehicle_info?: {
    make?: string;
    model?: string;
    year?: number;
    vin?: string;
  };
}

export interface ClaimSubmitResponse {
  claim_id: string;
  status: string;
  message: string;
  created_at: string;
}

export async function submitClaim(data: ClaimSubmitRequest): Promise<ClaimSubmitResponse> {
  return apiFetch<ClaimSubmitResponse>('/api/claims/submit', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Upload files to a claim
 */
export interface FileUploadResponse {
  claim_id: string;
  uploaded_files: Array<{
    file_id: string;
    filename: string;
    content_type: string;
    size: number;
    status: string;
  }>;
  processing_status: string;
}

export async function uploadClaimFiles(claimId: string, files: File[]): Promise<FileUploadResponse> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });

  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const response = await fetch(`${baseUrl}/api/claims/${claimId}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new APIError(
      response.status,
      errorData.detail || `Upload failed: ${response.status}`,
      errorData
    );
  }

  return response.json();
}

/**
 * Get claim processing status
 */
export interface ProcessingStatusResponse {
  claim_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  current_step?: string;
  steps_completed: string[];
  error?: string;
}

export async function getClaimProcessingStatus(claimId: string): Promise<ProcessingStatusResponse> {
  return apiFetch<ProcessingStatusResponse>(`/api/claims/${claimId}/status`);
}

/**
 * Get full claim assessment
 */
export interface DamageArea {
  area_id: string;
  location: string;
  severity: 'minor' | 'moderate' | 'severe' | 'total_loss';
  confidence: number;
  estimated_cost: number;
  description: string;
  bounding_box?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  source_media_id?: string;
}

export interface LiabilityAssessment {
  fault_determination: string;
  fault_percentage: number;
  contributing_factors: string[];
  liability_notes: string;
}

export interface FraudIndicator {
  indicator_type: string;
  severity: 'low' | 'medium' | 'high';
  description: string;
  confidence: number;
}

export interface PolicyCitationClaim {
  policy_id: string;
  policy_name: string;
  section: string;
  citation_text: string;
  relevance_score: number;
  supports_coverage: boolean;
}

export interface PayoutRecommendation {
  recommended_amount: number;
  min_amount: number;
  max_amount: number;
  breakdown: Record<string, number>;
  adjustments: Array<{
    reason: string;
    amount: number;
  }>;
}

export interface ClaimAssessmentResponse {
  claim_id: string;
  status: string;
  overall_severity: 'minor' | 'moderate' | 'severe' | 'total_loss';
  total_estimated_damage: number;
  damage_areas: DamageArea[];
  liability: LiabilityAssessment;
  fraud_indicators: FraudIndicator[];
  policy_citations: PolicyCitationClaim[];
  payout_recommendation: PayoutRecommendation;
  adjuster_decision?: {
    decision: 'approve' | 'adjust' | 'deny' | 'investigate';
    adjusted_amount?: number;
    notes?: string;
    decided_at?: string;
    decided_by?: string;
  };
  created_at: string;
  updated_at: string;
}

export async function getClaimAssessment(claimId: string): Promise<ClaimAssessmentResponse> {
  return apiFetch<ClaimAssessmentResponse>(`/api/claims/${claimId}/assessment`);
}

/**
 * Update adjuster decision
 */
export interface AdjusterDecisionRequest {
  decision: 'approve' | 'adjust' | 'deny' | 'investigate';
  adjusted_amount?: number;
  notes?: string;
}

export interface AdjusterDecisionResponse {
  claim_id: string;
  decision: string;
  adjusted_amount?: number;
  notes?: string;
  decided_at: string;
  message: string;
}

export async function updateAdjusterDecision(
  claimId: string,
  decision: AdjusterDecisionRequest
): Promise<AdjusterDecisionResponse> {
  return apiFetch<AdjusterDecisionResponse>(`/api/claims/${claimId}/assessment/decision`, {
    method: 'PUT',
    body: JSON.stringify(decision),
  });
}

/**
 * Search claims policies
 */
export interface ClaimsPolicySearchRequest {
  query: string;
  category?: string;
  limit?: number;
}

export interface ClaimsPolicySearchResult {
  chunk_id: string;
  policy_id: string;
  policy_name: string;
  category: string;
  content: string;
  similarity?: number;  // From backend
  score?: number;       // Legacy/alias
  severity?: string;
  criteria_id?: string;
}

export interface ClaimsPolicySearchResponse {
  query: string;
  results: ClaimsPolicySearchResult[];
  total_results: number;
}

export async function searchClaimsPolicies(
  request: ClaimsPolicySearchRequest
): Promise<ClaimsPolicySearchResponse> {
  return apiFetch<ClaimsPolicySearchResponse>('/api/claims/policies/search', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Get claim media list
 */
export interface MediaItem {
  media_id: string;
  filename: string;
  content_type: string;
  media_type: 'image' | 'video' | 'document';
  size: number;
  thumbnail_url?: string;
  url: string;
  processed: boolean;
  analysis_summary?: string;
  uploaded_at: string;
}

export interface ClaimMediaListResponse {
  claim_id: string;
  media_items: MediaItem[];
  total_count: number;
}

export async function getClaimMedia(claimId: string): Promise<ClaimMediaListResponse> {
  return apiFetch<ClaimMediaListResponse>(`/api/claims/${claimId}/media`);
}

/**
 * Get video keyframes
 */
export interface Keyframe {
  keyframe_id: string;
  timestamp: number;
  timestamp_formatted: string;
  thumbnail_url: string;
  description?: string;
  damage_detected: boolean;
  damage_areas?: DamageArea[];
  confidence: number;
}

export interface KeyframesResponse {
  media_id: string;
  duration: number;
  keyframes: Keyframe[];
  total_keyframes: number;
}

export async function getVideoKeyframes(claimId: string, mediaId: string): Promise<KeyframesResponse> {
  return apiFetch<KeyframesResponse>(`/api/claims/${claimId}/media/${mediaId}/keyframes`);
}

/**
 * Get damage areas for specific media
 */
export interface MediaDamageAreasResponse {
  media_id: string;
  damage_areas: DamageArea[];
  total_estimated_cost: number;
}

export async function getMediaDamageAreas(
  claimId: string,
  mediaId: string
): Promise<MediaDamageAreasResponse> {
  return apiFetch<MediaDamageAreasResponse>(`/api/claims/${claimId}/media/${mediaId}/damage-areas`);
}
