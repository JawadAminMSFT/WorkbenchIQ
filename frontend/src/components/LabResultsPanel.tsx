'use client';

import { Activity } from 'lucide-react';
import type { ApplicationMetadata, ExtractedField } from '@/lib/types';
import ConfidenceIndicator from './ConfidenceIndicator';
import CitationTooltip from './CitationTooltip';

interface LabResultsPanelProps {
  application: ApplicationMetadata;
}

interface ParsedLabResult {
  name: string;
  value: string;
  unit?: string;
  date?: string;
  confidence?: number;
  citation?: ExtractedField;
}

interface LabResultsData {
  results: ParsedLabResult[];
  summary?: string;
  riskAssessment?: string;
}

function parseLabResults(application: ApplicationMetadata): LabResultsData {
  const results: ParsedLabResult[] = [];
  let summary: string | undefined;
  let riskAssessment: string | undefined;
  
  // Get confidence from underlying extracted fields
  const fields = application.extracted_fields || {};
  const bpField = Object.values(fields).find(f => f.field_name === 'BloodPressureReadings');
  const lipidField = Object.values(fields).find(f => f.field_name === 'LipidPanelResults');
  const bpConfidence = bpField?.confidence;
  const lipidConfidence = lipidField?.confidence;
  
  // First, try LLM outputs for blood pressure
  const llmHypertension = application.llm_outputs?.medical_summary?.hypertension?.parsed as any;
  if (llmHypertension?.bp_readings && Array.isArray(llmHypertension.bp_readings)) {
    llmHypertension.bp_readings.forEach((reading: any, idx: number) => {
      if (reading.systolic && reading.diastolic) {
        results.push({
          name: llmHypertension.bp_readings.length > 1 ? `Blood Pressure #${idx + 1}` : 'Blood Pressure',
          value: `${reading.systolic}/${reading.diastolic}`,
          unit: 'mmHg',
          date: reading.date,
          confidence: bpConfidence,
          citation: bpField,
        });
      }
    });
    summary = llmHypertension.summary;
    riskAssessment = llmHypertension.risk_assessment;
  }
  
  // Try LLM outputs for cholesterol
  const llmCholesterol = application.llm_outputs?.medical_summary?.high_cholesterol?.parsed as any;
  if (llmCholesterol?.lipid_panels && Array.isArray(llmCholesterol.lipid_panels)) {
    llmCholesterol.lipid_panels.forEach((panel: any) => {
      if (panel.total_cholesterol) results.push({ name: 'Total Cholesterol', value: panel.total_cholesterol, date: panel.date, confidence: lipidConfidence, citation: lipidField });
      if (panel.ldl) results.push({ name: 'LDL Cholesterol', value: panel.ldl, date: panel.date, confidence: lipidConfidence, citation: lipidField });
      if (panel.hdl) results.push({ name: 'HDL Cholesterol', value: panel.hdl, date: panel.date, confidence: lipidConfidence, citation: lipidField });
      if (panel.triglycerides) results.push({ name: 'Triglycerides', value: panel.triglycerides, date: panel.date, confidence: lipidConfidence, citation: lipidField });
    });
  }
  
  // If no LLM data, fall back to extracted fields
  if (results.length === 0) {
    // Parse Blood Pressure Readings from extraction
    if (bpField?.value) {
    // Handle new format: array of objects
    if (Array.isArray(bpField.value)) {
      const bpArray = bpField.value as any[];
      bpArray.forEach((reading: any, idx: number) => {
        if (reading.systolic && reading.diastolic) {
          const dateInfo = reading.date ? ` (${reading.date})` : '';
          results.push({
            name: bpArray.length > 1 ? `Blood Pressure #${idx + 1}` : 'Blood Pressure',
            value: `${reading.systolic}/${reading.diastolic}`,
            unit: 'mmHg',
            date: reading.date,
            confidence: bpField.confidence,
            citation: bpField,
          });
        }
      });
    } else {
      // Handle old format: semicolon-separated string
      const bpStr = String(bpField.value);
      const readings = bpStr.split(';').map(s => s.trim()).filter(Boolean);
      readings.forEach((reading, idx) => {
        const match = reading.match(/(\d+\/\d+)\s*(mmHg)?/i);
        if (match) {
          results.push({
            name: readings.length > 1 ? `Blood Pressure #${idx + 1}` : 'Blood Pressure',
            value: match[1],
            unit: 'mmHg',
            confidence: bpField.confidence,
            citation: bpField,
          });
        }
      });
    }
  }

  // Parse Lipid Panel Results
  const lipidField = Object.values(fields).find(f => f.field_name === 'LipidPanelResults');
  if (lipidField?.value) {
    const confidence = lipidField.confidence;
    
    // Handle new format: object with properties
    if (typeof lipidField.value === 'object' && !Array.isArray(lipidField.value)) {
      const lipid = lipidField.value as any;
      // Only add if the nested value has an actual valueString, not just confidence
      if (lipid.totalCholesterol?.valueString) results.push({ name: 'Total Cholesterol', value: String(lipid.totalCholesterol.valueString).replace(/[^\d.]/g, ''), unit: 'mg/dL', date: lipid.testDate?.valueString, confidence, citation: lipidField });
      else if (lipid.totalCholesterol && typeof lipid.totalCholesterol === 'string') results.push({ name: 'Total Cholesterol', value: String(lipid.totalCholesterol).replace(/[^\d.]/g, ''), unit: 'mg/dL', date: lipid.testDate, confidence, citation: lipidField });
      
      if (lipid.hdl?.valueString) results.push({ name: 'HDL Cholesterol', value: String(lipid.hdl.valueString).replace(/[^\d.]/g, ''), unit: 'mg/dL', date: lipid.testDate?.valueString, confidence, citation: lipidField });
      else if (lipid.hdl && typeof lipid.hdl === 'string') results.push({ name: 'HDL Cholesterol', value: String(lipid.hdl).replace(/[^\d.]/g, ''), unit: 'mg/dL', date: lipid.testDate, confidence, citation: lipidField });
      
      if (lipid.ldl?.valueString) results.push({ name: 'LDL Cholesterol', value: String(lipid.ldl.valueString).replace(/[^\d.]/g, ''), unit: 'mg/dL', date: lipid.testDate?.valueString, confidence, citation: lipidField });
      else if (lipid.ldl && typeof lipid.ldl === 'string') results.push({ name: 'LDL Cholesterol', value: String(lipid.ldl).replace(/[^\d.]/g, ''), unit: 'mg/dL', date: lipid.testDate, confidence, citation: lipidField });
      
      if (lipid.triglycerides?.valueString) results.push({ name: 'Triglycerides', value: String(lipid.triglycerides.valueString).replace(/[^\d.]/g, ''), unit: 'mg/dL', date: lipid.testDate?.valueString, confidence, citation: lipidField });
      else if (lipid.triglycerides && typeof lipid.triglycerides === 'string') results.push({ name: 'Triglycerides', value: String(lipid.triglycerides).replace(/[^\d.]/g, ''), unit: 'mg/dL', date: lipid.testDate, confidence, citation: lipidField });
    } else {
      // Handle old format: string with embedded values
      const lipidStr = String(lipidField.value);
      const cholMatch = lipidStr.match(/total[:\s]+(\d+)/i);
      const hdlMatch = lipidStr.match(/hdl[:\s]+(\d+)/i);
      const ldlMatch = lipidStr.match(/ldl[:\s]+(\d+)/i);
      const trigMatch = lipidStr.match(/triglycerides?[:\s]+(\d+)/i);
      
      if (cholMatch) results.push({ name: 'Total Cholesterol', value: cholMatch[1], unit: 'mg/dL', confidence, citation: lipidField });
      if (hdlMatch) results.push({ name: 'HDL Cholesterol', value: hdlMatch[1], unit: 'mg/dL', confidence, citation: lipidField });
      if (ldlMatch) results.push({ name: 'LDL Cholesterol', value: ldlMatch[1], unit: 'mg/dL', confidence, citation: lipidField });
      if (trigMatch) results.push({ name: 'Triglycerides', value: trigMatch[1], unit: 'mg/dL', confidence, citation: lipidField });
    }
  }

  // Parse Pulse Rate
  const pulseField = Object.values(fields).find(f => f.field_name === 'PulseRate');
  if (pulseField?.value) {
    results.push({
      name: 'Pulse Rate',
      value: String(pulseField.value),
      unit: 'bpm',
      confidence: pulseField.confidence,
      citation: pulseField,
    });
  }

    // Parse Urinalysis Results
    const urineField = Object.values(fields).find(f => f.field_name === 'UrinalysisResults');
    if (urineField?.value) {
      // Handle new format: object with properties
      if (typeof urineField.value === 'object' && !Array.isArray(urineField.value)) {
        const urine = urineField.value as any;
        const parts: string[] = [];
        // Check for valueString (nested format) or direct string value
        const proteinVal = urine.protein?.valueString || (typeof urine.protein === 'string' ? urine.protein : null);
        const glucoseVal = urine.glucose?.valueString || (typeof urine.glucose === 'string' ? urine.glucose : null);
        const bloodVal = urine.blood?.valueString || (typeof urine.blood === 'string' ? urine.blood : null);
        const otherVal = urine.other?.valueString || (typeof urine.other === 'string' ? urine.other : null);
        
        if (proteinVal) parts.push(`Protein: ${proteinVal}`);
        if (glucoseVal) parts.push(`Glucose: ${glucoseVal}`);
        if (bloodVal) parts.push(`Blood: ${bloodVal}`);
        if (otherVal) parts.push(otherVal);
        
        // Only add if we have actual values
        if (parts.length > 0) {
          results.push({
            name: 'Urinalysis',
            value: parts.join(', '),
            confidence: urineField.confidence,
            citation: urineField,
          });
        }
      } else if (urineField.value) {
        // Handle old format: string
        const valueStr = String(urineField.value).trim();
        if (valueStr) {
          results.push({
            name: 'Urinalysis',
            value: valueStr.substring(0, 50) + (valueStr.length > 50 ? '...' : ''),
            confidence: urineField.confidence,
            citation: urineField,
          });
        }
      }
    }
  }

  return { results, summary, riskAssessment };
}

export default function LabResultsPanel({ application }: LabResultsPanelProps) {
  const { results, summary, riskAssessment } = parseLabResults(application);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 max-h-[400px] overflow-y-auto">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4 sticky top-0 bg-white pb-2 -mt-2 pt-2 z-10">
        <div className="w-8 h-8 bg-violet-100 rounded-lg flex items-center justify-center">
          <Activity className="w-5 h-5 text-violet-600" />
        </div>
        <h2 className="text-lg font-semibold text-slate-900">
          Lab Results and Measurements
        </h2>
      </div>

      {/* Summary from LLM if available */}
      {summary && (
        <div className="mb-4 p-3 bg-slate-50 rounded-lg">
          <p className="text-sm text-slate-700">{summary}</p>
        </div>
      )}

      {/* Risk Assessment if available */}
      {riskAssessment && (
        <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <p className="text-sm font-medium text-amber-800">Risk Assessment</p>
          <p className="text-sm text-amber-700">{riskAssessment}</p>
        </div>
      )}

      {/* Lab Results List */}
      {results.length > 0 ? (
        <div className="space-y-4">
          {results.map((result: ParsedLabResult, idx: number) => (
            <div key={idx} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="text-sm font-medium text-slate-900">{result.name}</div>
                {/* Confidence indicator (colored dot) */}
                {result.confidence !== undefined && (
                  <ConfidenceIndicator 
                    confidence={result.confidence} 
                    fieldName={result.name}
                  />
                )}
                {/* Citation tooltip */}
                {result.citation && (
                  <CitationTooltip citation={{
                    sourceFile: result.citation.source_file,
                    pageNumber: result.citation.page_number,
                    sourceText: result.citation.source_text,
                  }} appId={application.id}>
                    <span></span>
                  </CitationTooltip>
                )}
              </div>
              <div className="text-right">
                <span className="text-lg font-semibold text-slate-900">{result.value}</span>
                {result.unit && (
                  <span className="text-sm text-slate-500 ml-1">{result.unit}</span>
                )}
                {result.date && (
                  <span className="text-xs text-slate-400 ml-2">({result.date})</span>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-slate-500 italic">No lab results extracted</p>
      )}
    </div>
  );
}
