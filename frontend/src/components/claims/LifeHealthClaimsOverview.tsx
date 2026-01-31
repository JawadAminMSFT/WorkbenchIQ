'use client';

import { useState } from 'react';
import {
  Stethoscope,
  FileText,
  ExternalLink,
  ListChecks,
  Activity,
  Shield,
  ClipboardList,
  CheckCircle,
  ChevronDown,
  ChevronRight,
  ChevronUp,
} from 'lucide-react';
import type { ApplicationMetadata, ExtractedField } from '@/lib/types';
import clsx from 'clsx';
import CitableValue from '../CitableValue';
import ConfidenceIndicator, { ConfidenceValue } from '../ConfidenceIndicator';
import { FinalDecisionModal, LineItemOverrideModal } from './Modals';

interface LifeHealthClaimsOverviewProps {
  application: ApplicationMetadata | null;
}

interface TimelineEntry {
  date: string;
  year: string;
  title: string;
  description?: string;
  color: 'orange' | 'yellow' | 'blue' | 'green' | 'purple' | 'red';
  details?: string;
  sortDate?: number;
}

function parseDate(text: string): Date | null {
  if (!text) return null;
  // Try to match YYYY-MM-DD format
  let match = text.match(/(\d{4})-(\d{2})-(\d{2})/);
  if (match) {
    return new Date(parseInt(match[1]), parseInt(match[2]) - 1, parseInt(match[3]));
  }
  // Try to match MM/DD/YYYY format
  match = text.match(/(\d{1,2})\/(\d{1,2})\/(\d{4})/);
  if (match) {
    return new Date(parseInt(match[3]), parseInt(match[1]) - 1, parseInt(match[2]));
  }
  return null;
}

function formatDateDisplay(date: Date | null): { date: string; year: string } {
  if (!date) {
    return { date: 'N/A', year: '' };
  }
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const month = months[date.getMonth()];
  const day = date.getDate().toString().padStart(2, '0');
  const year = date.getFullYear().toString();
  return {
    date: `${month}-${day}`,
    year: year,
  };
}

function getFieldValue(field: unknown, defaultValue: string = ''): string {
  if (field && typeof field === 'object' && 'value' in field) {
    const val = (field as { value: unknown }).value;
    return val != null && val !== '' ? String(val) : defaultValue;
  }
  return defaultValue;
}

// Helper to get field data with fallback
function getFieldData(
  extractedFields: Record<string, ExtractedField> | undefined, 
  keys: string[], 
  fallbackValue: string = ''
): { value: string; field?: ExtractedField } {
  if (extractedFields) {
    for (const key of keys) {
      // 1. Try exact match
      if (extractedFields[key]?.value != null && extractedFields[key]?.value !== '') {
        return { value: String(extractedFields[key].value), field: extractedFields[key] };
      }
      
      // 2. Try suffix match (for "filename:FieldName" pattern)
      for (const extractedKey of Object.keys(extractedFields)) {
        if (extractedKey.endsWith(`:${key}`) && extractedFields[extractedKey].value != null && extractedFields[extractedKey].value !== '') {
          return { value: String(extractedFields[extractedKey].value), field: extractedFields[extractedKey] };
        }
      }
    }
  }
  return { value: fallbackValue };
}

// Component to display value with confidence and citation
// Helper to truncate and clean monetary values for display
function formatMonetaryValue(value: string): string {
  if (!value || value === 'N/A') return 'N/A';
  
  // If it starts with $ and contains only number/punctuation, it's a proper amount
  if (/^\$[\d,]+\.?\d*$/.test(value.trim())) {
    return value.trim();
  }
  
  // Extract dollar amount if embedded in text
  const dollarMatch = value.match(/\$[\d,]+\.?\d*/);
  if (dollarMatch) {
    return dollarMatch[0];
  }
  
  // If it contains "Unknown" or verbose explanation, return "Pending"
  if (value.toLowerCase().includes('unknown') || value.length > 20) {
    return 'Pending';
  }
  
  return value;
}

function FieldWithConfidence({ 
  data, 
  className,
  formatAsMoney = false,
}: { 
  data: { value: string; field?: ExtractedField }; 
  className?: string;
  formatAsMoney?: boolean;
}) {
  const displayValue = formatAsMoney ? formatMonetaryValue(data.value) : data.value;
  
  return (
    <div className="flex items-center gap-1.5">
      <CitableValue 
        value={displayValue} 
        citation={data.field} 
        className={className} 
      />
      {data.field && <ConfidenceIndicator confidence={data.field.confidence} />}
    </div>
  );
}

// Compact Header Strip
function HeaderStrip({ application }: { application: ApplicationMetadata | null }) {
  const extractedFields = application?.extracted_fields || {};
  const llmOutputs = (application?.llm_outputs || {}) as Record<string, any>;
  
  // Helper to get deep values safely
  const getLlmValue = (path: string[], defaultVal: string = '') => {
    let current: any = llmOutputs;
    for (const key of path) {
      if (current && typeof current === 'object' && key in current) {
        current = current[key];
      } else {
        return defaultVal;
      }
    }
    return current !== null && current !== undefined ? String(current) : defaultVal;
  };

  // Benefits & Policy info from LLM
  const eligibility = (llmOutputs.benefits_policy?.eligibility_verification?.parsed || {}) as Record<string, any>;
  const planDetails = eligibility.plan_details || {};
  const coverageDatesObj = eligibility.coverage_dates || {};
  const llmPlanName = planDetails.plan_name;
  const llmCoverageDates = coverageDatesObj.effective_date && coverageDatesObj.termination_date 
    ? `${coverageDatesObj.effective_date} - ${coverageDatesObj.termination_date}` 
    : '';

  // Financials from LLM
  const finalDecision = (llmOutputs.tasks_decisions?.final_decision?.parsed || {}) as Record<string, any>;
  const paymentSummary = finalDecision.payment_summary || {};

  // Provider info from LLM
  const timelineEvents = (llmOutputs.clinical_timeline?.treatment_timeline?.parsed?.timeline_events || []) as any[];
  const officeVisit = timelineEvents.find((e: any) => e.event_type === 'Office Visit' || e.event_type === 'Visit');
  const llmProviderName = officeVisit?.provider || '';

  // Try different possible field name variations and only show defaults if truly no data
  const planNameData = getFieldData(extractedFields, ['PlanName', 'plan_name', 'policy_number'], llmPlanName || 'N/A');
                   
  const coverageDatesData = getFieldData(extractedFields, ['CoverageDates', 'coverage_dates', 'date_of_service'], llmCoverageDates || 'N/A');
                        
  const providerNameData = getFieldData(extractedFields, ['ProviderName', 'provider_name'], llmProviderName || 'N/A');
                       
  const billedAmountData = getFieldData(extractedFields, ['BilledAmount', 'total_charges', 'billed_amount'], paymentSummary.total_billed || 'N/A');
                       
  const allowedAmountData = getFieldData(extractedFields, ['AllowedAmount', 'allowed_amount'], paymentSummary.total_allowed || 'N/A');
                        
  const planLiabilityData = getFieldData(extractedFields, ['PlanLiability', 'plan_liability', 'plan_pays'], paymentSummary.plan_pays || 'N/A');
                        
  const memberOOPData = getFieldData(extractedFields, ['MemberOOP', 'member_oop', 'member_responsibility'], paymentSummary.member_pays || 'N/A');

  return (
    <div className="bg-gradient-to-r from-indigo-600 to-indigo-700 text-white px-5 py-2.5 flex-shrink-0">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-indigo-200 text-xs">Policy:</span> 
            <FieldWithConfidence data={planNameData} className="font-medium" />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-indigo-200 text-xs">Coverage:</span> 
            <FieldWithConfidence data={coverageDatesData} className="font-medium" />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-indigo-200 text-xs">Provider:</span> 
            <FieldWithConfidence data={providerNameData} className="font-medium" />
          </div>
        </div>
        <div className="flex items-center gap-5">
          <div className="text-center">
            <div className="text-xs text-indigo-200">Billed</div>
            <div className="flex justify-center">
              <FieldWithConfidence data={billedAmountData} className="font-semibold" formatAsMoney />
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-indigo-200">Allowed</div>
            <div className="flex justify-center">
              <FieldWithConfidence data={allowedAmountData} className="font-semibold" formatAsMoney />
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-indigo-200">Plan Pays</div>
            <div className="flex justify-center">
              <FieldWithConfidence data={planLiabilityData} className="font-semibold text-emerald-300" formatAsMoney />
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-indigo-200">Member OOP</div>
            <div className="flex justify-center">
              <FieldWithConfidence data={memberOOPData} className="font-semibold" formatAsMoney />
            </div>
          </div>
          <span className="px-2.5 py-1 bg-rose-500 rounded-full text-xs font-medium">High</span>
        </div>
      </div>
    </div>
  );
}

// Main Component with Horizontal 2-Row Layout
export default function LifeHealthClaimsOverview({ application }: LifeHealthClaimsOverviewProps) {
  const [checkedTasks, setCheckedTasks] = useState<number[]>([]);
  const [expandedSection, setExpandedSection] = useState<string>('reason');
  const [activeTab, setActiveTab] = useState<'timeline' | 'documents'>('timeline');
  const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set());
  
  // Modal State
  const [isFinalDecisionModalOpen, setIsFinalDecisionModalOpen] = useState(false);
  const [overrideLineItem, setOverrideLineItem] = useState<any>(null);
  
  // Local state for overrides and decisions
  const [lineItemOverrides, setLineItemOverrides] = useState<Record<number, any>>({});
  const [finalDecisionStatus, setFinalDecisionStatus] = useState<string | null>(null);

  const llmOutputs = (application?.llm_outputs || {}) as Record<string, any>;
  const clinicalNotes = (llmOutputs.clinical_case_notes || {}) as Record<string, any>;
  const reasonForVisit = (clinicalNotes.reason_for_visit || {}) as Record<string, any>;
  const keyDiagnoses = (clinicalNotes.key_diagnoses || {}) as Record<string, any>;
  
  const files = application?.files || [];
  const documents = files.length > 0 ? files.map(f => ({ name: f.filename, type: 'Document' })) : [];

  // Handlers
  const handleFinalDecisionConfirm = (decision: any) => {
    setFinalDecisionStatus(decision.decision);
    // In a real app, you would save this to the backend
    console.log('Final Decision Submitted:', decision);
  };

  const handleOverrideConfirm = (override: any) => {
    setLineItemOverrides(prev => ({
      ...prev,
      [override.line]: override
    }));
    // In a real app, you would save this to the backend
    console.log('Line Item Override:', override);
  };


  // Extract timeline from actual data if available
  const extractedFields = application?.extracted_fields || {};
  let timelineEvents: TimelineEntry[] = [];
  
  // Try to get timeline from LLM first
  const llmTimeline = (llmOutputs.clinical_timeline?.treatment_timeline?.parsed?.timeline_events || []) as any[];
  
  if (llmTimeline.length > 0) {
    timelineEvents = llmTimeline.map((e: any) => {
      const parsedDate = parseDate(e.date);
      const displayDate = formatDateDisplay(parsedDate);
      
      // Determine color based on event type
      let color: TimelineEntry['color'] = 'blue';
      const type = (e.event_type || '').toLowerCase();
      if (type.includes('diagnosis') || type.includes('condition')) color = 'red';
      else if (type.includes('procedure') || type.includes('surgery')) color = 'orange';
      else if (type.includes('visit') || type.includes('encounter')) color = 'green';
      else if (type.includes('lab') || type.includes('test')) color = 'purple';
      else if (type.includes('medication') || type.includes('rx')) color = 'yellow';

      return {
        date: displayDate.date,
        year: displayDate.year,
        title: e.event_type || 'Event',
        description: e.description,
        color: color,
        details: e.description, // Use description as details for now
        sortDate: parsedDate?.getTime() || 0
      };
    });
  } else {
    // Fallback to extracted fields
    const serviceDateData = getFieldData(extractedFields, ['date_of_service', 'DateOfService']);
    const serviceDateStr = serviceDateData.value;
    const serviceDate = parseDate(serviceDateStr);
    const displayDate = formatDateDisplay(serviceDate);
    
    if (serviceDate) {
      const diagnosisData = getFieldData(extractedFields, ['primary_diagnosis', 'PrimaryDiagnosis']);
      const diagnosis = diagnosisData.value;
      
      const procedureData = getFieldData(extractedFields, ['procedure_name', 'ProcedureName']);
      const procedure = procedureData.value;
      
      if (diagnosis) {
        timelineEvents.push({
          date: displayDate.date,
          year: displayDate.year,
          title: 'Diagnosis',
          description: diagnosis,
          color: 'red',
          details: diagnosis,
          sortDate: serviceDate.getTime()
        });
      }
      if (procedure) {
        timelineEvents.push({
          date: displayDate.date,
          year: displayDate.year,
          title: 'Procedure',
          description: procedure,
          color: 'orange',
          details: procedure,
          sortDate: serviceDate.getTime()
        });
      }
    }
  }
  
  // Sort timeline events
  timelineEvents.sort((a, b) => (b.sortDate || 0) - (a.sortDate || 0));

  const colorClasses: Record<string, string> = {
    orange: 'bg-orange-500',
    yellow: 'bg-yellow-500',
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
    red: 'bg-red-500',
  };

  const toggleExpand = (idx: number) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(idx)) {
      newExpanded.delete(idx);
    } else {
      newExpanded.add(idx);
    }
    setExpandedItems(newExpanded);
  };

  // Extract benefit info from LLM outputs if available
  const eligibility = (llmOutputs.eligibility || {}) as Record<string, any>;
  const coverageVerification = (eligibility.coverage_verification?.parsed || {}) as Record<string, any>;
  const benefitItems = [];
  if (coverageVerification.eligibility_status) {
    benefitItems.push({ label: 'Eligibility', value: coverageVerification.eligibility_status, ok: coverageVerification.eligibility_status === 'Eligible' });
  }
  if (coverageVerification.network_status) {
    benefitItems.push({ label: 'Network', value: coverageVerification.network_status, ok: coverageVerification.network_status === 'In-Network' });
  }
  if (coverageVerification.deductible_status?.remaining) {
    const remaining = coverageVerification.deductible_status.remaining;
    benefitItems.push({ label: 'Deductible', value: remaining === '$0' ? 'Met' : `${remaining} remaining`, ok: remaining === '$0' });
  }

  // Extract claim line items from payment calculation if available
  const claimAssessment = (llmOutputs.claim_assessment || llmOutputs.payment_calculation || {}) as Record<string, any>;
  const paymentDetermination = (claimAssessment.payment_determination?.parsed || claimAssessment.benefit_determination?.parsed || {}) as Record<string, any>;
  const paymentCalc = paymentDetermination.payment_calculation || {};
  
  // Also check for claim_line_evaluation (new format)
  const claimLineEval = (llmOutputs.claim_line_evaluation?.line_item_review?.parsed || {}) as Record<string, any>;
  
  const lineItems = paymentCalc.line_items || paymentDetermination.charge_breakdown || claimLineEval.claim_lines || [];
  
  // Get extracted procedure codes for confidence matching - aggregate from all files
  const allExtractedProcedures: any[] = [];
  if (extractedFields) {
    Object.keys(extractedFields).forEach(key => {
      if (key.endsWith(':ProcedureCodes') || key.endsWith(':procedure_codes') || key === 'ProcedureCodes' || key === 'procedure_codes') {
        const field = extractedFields[key];
        if (field && Array.isArray(field.value)) {
          // Attach source info to items
          const items = field.value.map((item: any) => ({
            ...item,
            _sourceFile: field.source_file,
            _pageNumber: field.page_number
          }));
          allExtractedProcedures.push(...items);
        }
      }
    });
  }

  const claimLines = lineItems.map((item: any) => {
    const code = item.cpt || item.code || 'N/A';
    
    // Find matching extracted procedure to get confidence
    // The structure is typically valueArray -> valueObject -> code -> valueString/confidence
    const extracted = allExtractedProcedures.find((p: any) => {
      const pCode = p.valueObject?.code?.valueString || p.valueObject?.code?.value;
      return pCode === code;
    });
    
    const confidence = extracted?.valueObject?.code?.confidence;
    
    // Construct citation if extracted data found
    const citation = extracted ? {
      sourceFile: extracted._sourceFile,
      pageNumber: extracted._pageNumber,
      fieldName: 'ProcedureCodes',
      confidence: confidence
    } : undefined;

    // Check for local override
    const override = lineItemOverrides[item.line_number || item.line || 0];
    const decision = override ? override.action : (item.ai_opinion || item.status || (paymentDetermination.claim_decision === 'Approve' ? 'Approve' : 'Pending'));
    const allowed = override ? override.allowed : (item.allowed || 'N/A');

    return {
      line: item.line_number || item.line || 0,
      code: code,
      desc: item.description || item.service || item.desc || 'N/A',
      billed: item.billed || 'N/A',
      allowed: allowed,
      decision: decision,
      confidence: confidence,
      citation: citation,
      isOverridden: !!override
    };
  });

  // Extract tasks from multiple possible sources
  const tasks = [];
  const medicalReview = (llmOutputs.medical_review || llmOutputs.claim_assessment || {}) as Record<string, any>;
  const clinicalAssessment = (medicalReview.clinical_assessment?.parsed || medicalReview.medical_necessity_review?.parsed || {}) as Record<string, any>;
  
  if (clinicalAssessment.processing_action) {
    tasks.push({ task: clinicalAssessment.processing_action, due: 'Pending' });
  }
  
  // Check for service reviews that might need attention
  const serviceReviews = clinicalAssessment.service_reviews || [];
  serviceReviews.forEach((review: any) => {
    if (review.medical_necessity === 'Review Required' || review.medical_necessity === 'Pending') {
      tasks.push({ task: `Review: ${review.service}`, due: 'Today' });
    }
  });

  // Check for tasks in tasks_decisions (New structure)
  const taskDecisions = (llmOutputs.tasks_decisions?.final_decision?.parsed || {}) as Record<string, any>;
  if (taskDecisions.next_steps && Array.isArray(taskDecisions.next_steps)) {
    taskDecisions.next_steps.forEach((step: string) => {
      tasks.push({ task: step, due: 'Pending' });
    });
  }

  // Check for medical necessity reviews (New structure)
  const medicalNecessity = (llmOutputs.clinical_case_notes?.medical_necessity?.parsed || {}) as Record<string, any>;
  if (medicalNecessity.services_reviewed && Array.isArray(medicalNecessity.services_reviewed)) {
    medicalNecessity.services_reviewed.forEach((review: any) => {
       if (review.necessity_status === 'Questionable' || review.necessity_status === 'Review Required') {
         tasks.push({ task: `Review: ${review.service} (${review.necessity_status})`, due: 'Today' });
       }
    });
  }

  // Get extracted fields for Clinical Notes
  const reasonForVisitData = getFieldData(extractedFields, ['ReasonForVisit', 'reason_for_visit'], reasonForVisit.summary || 'Emergency room visit for acute chest pain with shortness of breath.');
  
  // Get extracted diagnoses for confidence matching
  const allExtractedDiagnoses: any[] = [];
  if (extractedFields) {
    Object.keys(extractedFields).forEach(key => {
      if (key.endsWith(':PrimaryDiagnosis') || key.endsWith(':primary_diagnosis') || key === 'PrimaryDiagnosis' || key === 'primary_diagnosis') {
        const field = extractedFields[key];
        if (field && field.value) {
          allExtractedDiagnoses.push({ ...field, type: 'Primary' });
        }
      }
      if (key.endsWith(':SecondaryDiagnoses') || key.endsWith(':secondary_diagnoses') || key === 'SecondaryDiagnoses' || key === 'secondary_diagnoses') {
        const field = extractedFields[key];
        if (field && Array.isArray(field.value)) {
          const items = field.value.map((item: any) => ({
            ...item,
            _sourceFile: field.source_file,
            _pageNumber: field.page_number,
            type: 'Secondary'
          }));
          allExtractedDiagnoses.push(...items);
        }
      }
    });
  }

  // Helper to find diagnosis confidence/citation
  const getDiagnosisCitation = (code: string) => {
    // Try to find in extracted diagnoses
    // Structure: valueObject -> code -> valueString/confidence
    const extracted = allExtractedDiagnoses.find((d: any) => {
      // Handle both direct object (Primary) and array item (Secondary) structures
      const dCode = d.value?.code?.valueString || d.value?.code?.value || 
                   d.valueObject?.code?.valueString || d.valueObject?.code?.value;
      return dCode === code;
    });

    if (!extracted) return undefined;

    const confidence = extracted.value?.code?.confidence || extracted.valueObject?.code?.confidence;
    
    return {
      citation: {
        sourceFile: extracted.source_file || extracted._sourceFile,
        pageNumber: extracted.page_number || extracted._pageNumber,
        fieldName: extracted.type === 'Primary' ? 'PrimaryDiagnosis' : 'SecondaryDiagnoses',
        confidence: confidence
      },
      confidence
    };
  };

  // Get extracted fields for Benefits
  const eligibilityData = getFieldData(extractedFields, ['Eligibility', 'eligibility_status'], coverageVerification.eligibility_status || 'Active');
  const networkData = getFieldData(extractedFields, ['Network', 'network_status'], coverageVerification.network_status || 'In-Network');
  const deductibleData = getFieldData(extractedFields, ['Deductible', 'deductible_remaining'], coverageVerification.deductible_status?.remaining || '$500 met');
  const oopMaxData = getFieldData(extractedFields, ['OOPMax', 'oop_max'], '$2,100 / $6,500');
  const limitsData = getFieldData(extractedFields, ['BenefitLimits', 'limits'], 'Within Limits');

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-slate-100">
      <HeaderStrip application={application} />
      
      {/* Main Content - 3 Horizontal Rows */}
      <div className="flex-1 overflow-auto p-4">
        <div className="h-full flex flex-col gap-4">
          
          {/* ROW 1: Clinical Notes | Benefits | Tasks */}
          <div className="grid grid-cols-12 gap-4 min-h-0" style={{ flex: '1 1 35%' }}>
            
            {/* Clinical Notes - 4 cols */}
            <div className="col-span-4 bg-white rounded-lg shadow-sm border border-slate-200 flex flex-col overflow-hidden">
              <div className="px-3 py-2 border-b border-slate-100 flex items-center gap-2 bg-slate-50 flex-shrink-0">
                <Stethoscope className="w-4 h-4 text-indigo-600" />
                <span className="font-semibold text-slate-900 text-sm">Clinical Notes</span>
                <span className="ml-auto text-xs text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded">AI</span>
              </div>
              <div className="flex-1 overflow-auto p-3 text-sm">
                <div className="space-y-3">
                  <div 
                    className="border border-slate-200 rounded cursor-pointer"
                    onClick={() => setExpandedSection(expandedSection === 'reason' ? '' : 'reason')}
                  >
                    <div className="px-3 py-2 flex items-center justify-between hover:bg-slate-50">
                      <span className="font-medium text-slate-900">Reason for Visit</span>
                      {expandedSection === 'reason' ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
                    </div>
                    {expandedSection === 'reason' && (
                      <div className="px-3 pb-2 text-slate-600 text-xs">
                        <FieldWithConfidence data={reasonForVisitData} />
                      </div>
                    )}
                  </div>
                  <div 
                    className="border border-slate-200 rounded cursor-pointer"
                    onClick={() => setExpandedSection(expandedSection === 'diagnoses' ? '' : 'diagnoses')}
                  >
                    <div className="px-3 py-2 flex items-center justify-between hover:bg-slate-50">
                      <span className="font-medium text-slate-900">Key Diagnoses</span>
                      {expandedSection === 'diagnoses' ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
                    </div>
                    {expandedSection === 'diagnoses' && (
                      <div className="px-3 pb-2 space-y-1">
                        {/* Dynamic Primary Diagnosis */}
                        {keyDiagnoses.parsed?.primary_diagnosis && (
                          <div className="flex items-center gap-2">
                            {(() => {
                              const code = keyDiagnoses.parsed.primary_diagnosis.code;
                              const data = getDiagnosisCitation(code);
                              return (
                                <div className="flex items-center gap-1.5">
                                  <span className="px-1.5 py-0.5 bg-indigo-100 text-indigo-700 text-xs rounded font-mono">
                                    <CitableValue value={code} citation={data?.citation} />
                                  </span>
                                  {data?.confidence !== undefined && <ConfidenceIndicator confidence={data.confidence} />}
                                </div>
                              );
                            })()}
                            <span className="text-slate-600 text-xs">{keyDiagnoses.parsed.primary_diagnosis.description}</span>
                          </div>
                        )}
                        {/* Dynamic Secondary Diagnoses */}
                        {keyDiagnoses.parsed?.secondary_diagnoses?.map((d: any, idx: number) => (
                          <div key={idx} className="flex items-center gap-2">
                            {(() => {
                              const code = d.code;
                              const data = getDiagnosisCitation(code);
                              return (
                                <div className="flex items-center gap-1.5">
                                  <span className="px-1.5 py-0.5 bg-slate-100 text-slate-600 text-xs rounded font-mono">
                                    <CitableValue value={code} citation={data?.citation} />
                                  </span>
                                  {data?.confidence !== undefined && <ConfidenceIndicator confidence={data.confidence} />}
                                </div>
                              );
                            })()}
                            <span className="text-slate-600 text-xs">{d.description}</span>
                          </div>
                        ))}
                        {/* Fallback if no parsed diagnoses */}
                        {!keyDiagnoses.parsed?.primary_diagnosis && !keyDiagnoses.parsed?.secondary_diagnoses && (
                          <div className="text-slate-400 text-xs italic">No diagnoses found</div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
            
            {/* Benefits & Policy - 4 cols */}
            <div className="col-span-4 bg-white rounded-lg shadow-sm border border-slate-200 flex flex-col overflow-hidden">
              <div className="px-3 py-2 border-b border-slate-100 flex items-center gap-2 bg-slate-50 flex-shrink-0">
                <FileText className="w-4 h-4 text-indigo-600" />
                <span className="font-semibold text-slate-900 text-sm">Benefits & Policy</span>
              </div>
              <div className="flex-1 overflow-auto p-3 text-xs">
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-600">Eligibility</span>
                    <FieldWithConfidence data={eligibilityData} className="font-medium text-emerald-600" />
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-600">Network</span>
                    <FieldWithConfidence data={networkData} className="font-medium" />
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-600">Deductible</span>
                    <FieldWithConfidence data={deductibleData} className="font-medium" />
                  </div>
                  <div className="flex justify-between items-center border-t pt-2 mt-2">
                    <span className="text-slate-600">OOP Max</span>
                    <FieldWithConfidence data={oopMaxData} className="font-medium" />
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-600">Benefit Limits</span>
                    <FieldWithConfidence data={limitsData} className="font-medium text-emerald-600" />
                  </div>
                </div>
              </div>
            </div>
            
            {/* Tasks - 4 cols */}
            <div className="col-span-4 bg-white rounded-lg shadow-sm border border-slate-200 flex flex-col overflow-hidden">
              <div className="px-3 py-2 border-b border-slate-100 flex items-center gap-2 bg-slate-50 flex-shrink-0">
                <ListChecks className="w-4 h-4 text-indigo-600" />
                <span className="font-semibold text-slate-900 text-sm">Tasks</span>
                <span className="ml-auto text-xs text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded">{tasks.length - checkedTasks.length} pending</span>
              </div>
              <div className="flex-1 overflow-auto p-3">
                <div className="space-y-2">
                  {tasks.map((t, i) => (
                    <label key={i} className="flex items-center gap-2 cursor-pointer text-sm">
                      <input 
                        type="checkbox" 
                        checked={checkedTasks.includes(i)} 
                        onChange={() => setCheckedTasks(prev => prev.includes(i) ? prev.filter(x => x !== i) : [...prev, i])}
                        className="w-3.5 h-3.5 rounded border-slate-300 text-indigo-600" 
                      />
                      <span className={clsx('flex-1', checkedTasks.includes(i) ? 'text-slate-400 line-through' : 'text-slate-900')}>{t.task}</span>
                      <span className="text-xs text-slate-400">{t.due}</span>
                    </label>
                  ))}
                </div>
                <button 
                  onClick={() => setIsFinalDecisionModalOpen(true)}
                  className={clsx(
                    "mt-3 w-full py-2 text-sm font-medium rounded-lg transition-colors",
                    finalDecisionStatus 
                      ? "bg-emerald-600 hover:bg-emerald-700 text-white"
                      : "bg-indigo-600 hover:bg-indigo-700 text-white"
                  )}
                >
                  {finalDecisionStatus ? `Decision: ${finalDecisionStatus}` : "Propose Final Decision"}
                </button>
              </div>
            </div>
          </div>
          
          {/* ROW 2: Timeline & Documents (Combined) */}
          <div className="bg-white rounded-lg shadow-sm border border-slate-200 flex flex-col overflow-hidden" style={{ flex: '1 1 30%' }}>
            {/* Header with Tabs */}
            <div className="px-4 py-2 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-indigo-600" />
                <span className="font-semibold text-slate-900 text-sm">Chronological Overview</span>
              </div>
              <div className="flex gap-1 bg-slate-200 p-0.5 rounded-lg">
                <button
                  onClick={() => setActiveTab('timeline')}
                  className={clsx(
                    'px-3 py-1 text-xs font-medium rounded-md transition-all',
                    activeTab === 'timeline'
                      ? 'bg-white text-indigo-700 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  )}
                >
                  Timeline ({timelineEvents.length})
                </button>
                <button
                  onClick={() => setActiveTab('documents')}
                  className={clsx(
                    'px-3 py-1 text-xs font-medium rounded-md transition-all',
                    activeTab === 'documents'
                      ? 'bg-white text-indigo-700 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  )}
                >
                  Documents ({documents.length})
                </button>
              </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-auto p-4">
              {activeTab === 'timeline' ? (
                timelineEvents.length > 0 ? (
                  <div className="relative">
                    {/* Timeline line */}
                    <div className="absolute left-12 top-0 bottom-0 w-px bg-slate-200" />

                    {/* Timeline items */}
                    <div className="space-y-4">
                      {timelineEvents.map((item, idx) => (
                        <div key={idx} className="relative flex gap-4">
                          {/* Date column */}
                          <div className="w-16 text-right flex-shrink-0 pt-0.5">
                            <div className="text-xs font-medium text-slate-500">{item.date}</div>
                            <div className="text-[10px] text-slate-400">{item.year}</div>
                          </div>

                          {/* Timeline dot */}
                          <div
                            className={clsx(
                              'w-3 h-3 rounded-full flex-shrink-0 mt-1.5 z-10 ring-2 ring-white',
                              colorClasses[item.color]
                            )}
                          />

                          {/* Content */}
                          <div className="flex-1 min-w-0">
                            <button
                              onClick={() => toggleExpand(idx)}
                              className="flex items-start justify-between w-full text-left group"
                            >
                              <div className="min-w-0">
                                <div className="text-sm font-medium text-slate-900 group-hover:text-indigo-700 transition-colors">
                                  {item.title}
                                </div>
                                <div className="text-xs text-slate-500 truncate pr-2">
                                  {item.description}
                                </div>
                              </div>
                              {item.details && (
                                expandedItems.has(idx) ? (
                                  <ChevronUp className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
                                ) : (
                                  <ChevronDown className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
                                )
                              )}
                            </button>

                            {/* Expanded content */}
                            {expandedItems.has(idx) && item.details && (
                              <div className="mt-2 p-3 bg-slate-50 rounded-lg text-xs text-slate-600 border border-slate-100">
                                <p className="whitespace-pre-wrap">{item.details}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-full text-slate-400">
                    <Activity className="w-8 h-8 mb-2 opacity-20" />
                    <p className="text-sm">No timeline events found</p>
                  </div>
                )
              ) : (
                // Documents Tab
                <div className="space-y-2">
                  {documents.map((doc, i) => (
                    <div key={i} className="flex items-center gap-3 p-2.5 hover:bg-slate-50 rounded-lg border border-transparent hover:border-slate-200 transition-all group cursor-pointer">
                      <div className="p-2 bg-indigo-50 rounded-lg text-indigo-600">
                        <FileText className="w-4 h-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-slate-900 truncate">{doc.name}</div>
                        <div className="text-xs text-slate-500">{doc.type}</div>
                      </div>
                      <ExternalLink className="w-4 h-4 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                  ))}
                  {documents.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-slate-400 py-8">
                      <FileText className="w-8 h-8 mb-2 opacity-20" />
                      <p className="text-sm">No documents available</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
          
          {/* ROW 3: Claim Line Evaluation - Full Width */}
          <div className="bg-white rounded-lg shadow-sm border border-slate-200 flex flex-col overflow-hidden" style={{ flex: '1 1 45%' }}>
            <div className="px-4 py-2.5 border-b border-slate-100 flex items-center gap-2 bg-slate-50 flex-shrink-0">
              <ListChecks className="w-4 h-4 text-indigo-600" />
              <span className="font-semibold text-slate-900 text-sm">Claim Line Evaluation</span>
              <span className="ml-auto text-xs text-slate-500">{claimLines.length} lines • Total: $1,755</span>
            </div>
            <div className="flex-1 overflow-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 sticky top-0">
                  <tr className="text-xs text-slate-500">
                    <th className="px-4 py-2 text-left w-12">#</th>
                    <th className="px-4 py-2 text-left w-20">Code</th>
                    <th className="px-4 py-2 text-left">Description</th>
                    <th className="px-4 py-2 text-right w-24">Billed</th>
                    <th className="px-4 py-2 text-right w-24">Allowed</th>
                    <th className="px-4 py-2 text-center w-24">AI Decision</th>
                    <th className="px-4 py-2 text-center w-24">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {claimLines.map((l: any) => (
                    <tr key={l.line} className="hover:bg-slate-50">
                      <td className="px-4 py-2.5 text-slate-600">{l.line}</td>
                      <td className="px-4 py-2.5 font-mono text-slate-700">
                        <div className="flex items-center gap-1.5">
                          <CitableValue value={l.code} citation={l.citation} />
                          {l.confidence !== undefined && <ConfidenceIndicator confidence={l.confidence} />}
                        </div>
                      </td>
                      <td className="px-4 py-2.5 text-slate-900">{l.desc}</td>
                      <td className="px-4 py-2.5 text-right text-slate-600">{l.billed}</td>
                      <td className="px-4 py-2.5 text-right text-slate-900 font-medium">{l.allowed}</td>
                      <td className="px-4 py-2.5 text-center">
                        <span className={clsx('px-2 py-0.5 rounded text-xs font-medium',
                          l.decision === 'Approve' ? 'bg-emerald-100 text-emerald-700' : 
                          l.decision === 'Deny' ? 'bg-rose-100 text-rose-700' :
                          'bg-amber-100 text-amber-700'
                        )}>{l.decision}</span>
                      </td>
                      <td className="px-4 py-2.5 text-center">
                        <button 
                          onClick={() => setOverrideLineItem(l)}
                          className={clsx(
                            "px-2 py-1 text-xs rounded hover:bg-opacity-80",
                            l.isOverridden 
                              ? "bg-indigo-100 text-indigo-700 font-medium" 
                              : "text-indigo-600 hover:bg-indigo-50"
                          )}
                        >
                          {l.isOverridden ? 'Edit' : 'Override'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          
        </div>
      </div>

      {/* Modals */}
      <FinalDecisionModal
        isOpen={isFinalDecisionModalOpen}
        onClose={() => setIsFinalDecisionModalOpen(false)}
        initialData={llmOutputs.tasks_decisions?.final_decision?.parsed}
        onConfirm={handleFinalDecisionConfirm}
      />

      <LineItemOverrideModal
        isOpen={!!overrideLineItem}
        onClose={() => setOverrideLineItem(null)}
        lineItem={overrideLineItem}
        onConfirm={handleOverrideConfirm}
      />
    </div>
  );
}
