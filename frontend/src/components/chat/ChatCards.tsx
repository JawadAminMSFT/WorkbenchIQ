'use client';

import { 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  FileText, 
  TrendingUp, 
  TrendingDown,
  Minus,
  ThumbsUp,
  ThumbsDown,
  AlertCircle,
  ArrowRight,
  Shield,
  Activity,
  ExternalLink
} from 'lucide-react';

// Type definitions for structured chat responses
export interface RiskFactor {
  title: string;
  description: string;
  risk_level: 'low' | 'moderate' | 'high';
  policy_id?: string;
}

export interface RiskFactorsResponse {
  type: 'risk_factors';
  summary: string;
  factors: RiskFactor[];
  overall_risk: 'low' | 'low-moderate' | 'moderate' | 'moderate-high' | 'high';
}

export interface PolicyItem {
  policy_id: string;
  name: string;
  relevance: string;
  finding: string;
}

export interface PolicyListResponse {
  type: 'policy_list';
  summary: string;
  policies: PolicyItem[];
}

export interface RecommendationResponse {
  type: 'recommendation';
  decision: 'approve' | 'approve_with_conditions' | 'defer' | 'decline';
  confidence: 'high' | 'medium' | 'low';
  summary: string;
  conditions?: string[];
  rationale: string;
  next_steps?: string[];
}

export interface ComparisonResponse {
  type: 'comparison';
  title: string;
  columns: string[];
  rows: { label: string; values: string[] }[];
}

export type StructuredResponse = 
  | RiskFactorsResponse 
  | PolicyListResponse 
  | RecommendationResponse 
  | ComparisonResponse;

// Risk level styling
const riskLevelConfig = {
  low: {
    bg: 'bg-emerald-50',
    border: 'border-emerald-200',
    text: 'text-emerald-700',
    badge: 'bg-emerald-100 text-emerald-700',
    icon: CheckCircle2,
  },
  'low-moderate': {
    bg: 'bg-lime-50',
    border: 'border-lime-200',
    text: 'text-lime-700',
    badge: 'bg-lime-100 text-lime-700',
    icon: TrendingUp,
  },
  moderate: {
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    text: 'text-amber-700',
    badge: 'bg-amber-100 text-amber-700',
    icon: AlertCircle,
  },
  'moderate-high': {
    bg: 'bg-orange-50',
    border: 'border-orange-200',
    text: 'text-orange-700',
    badge: 'bg-orange-100 text-orange-700',
    icon: AlertTriangle,
  },
  high: {
    bg: 'bg-rose-50',
    border: 'border-rose-200',
    text: 'text-rose-700',
    badge: 'bg-rose-100 text-rose-700',
    icon: XCircle,
  },
};

// Decision styling
const decisionConfig = {
  approve: {
    bg: 'bg-emerald-50',
    border: 'border-emerald-300',
    text: 'text-emerald-800',
    icon: ThumbsUp,
    label: 'Approve',
  },
  approve_with_conditions: {
    bg: 'bg-amber-50',
    border: 'border-amber-300',
    text: 'text-amber-800',
    icon: AlertCircle,
    label: 'Approve with Conditions',
  },
  defer: {
    bg: 'bg-slate-50',
    border: 'border-slate-300',
    text: 'text-slate-800',
    icon: Clock,
    label: 'Defer',
  },
  decline: {
    bg: 'bg-rose-50',
    border: 'border-rose-300',
    text: 'text-rose-800',
    icon: ThumbsDown,
    label: 'Decline',
  },
};

// Risk Factors Card
export function RiskFactorsCard({ 
  data, 
  onPolicyClick 
}: { 
  data: RiskFactorsResponse;
  onPolicyClick?: (policyId: string) => void;
}) {
  const overallConfig = riskLevelConfig[data.overall_risk] || riskLevelConfig.moderate;
  const OverallIcon = overallConfig.icon;

  return (
    <div className="space-y-3">
      {/* Summary Header */}
      <div className={`${overallConfig.bg} ${overallConfig.border} border rounded-lg p-3`}>
        <div className="flex items-center gap-2 mb-1">
          <OverallIcon className={`w-5 h-5 ${overallConfig.text}`} />
          <span className={`text-sm font-semibold ${overallConfig.text}`}>
            Overall Risk: {data.overall_risk.replace('-', ' ').toUpperCase()}
          </span>
        </div>
        <p className="text-sm text-slate-600">{data.summary}</p>
      </div>

      {/* Factor Cards */}
      <div className="space-y-2">
        {data.factors.map((factor, idx) => {
          const config = riskLevelConfig[factor.risk_level] || riskLevelConfig.moderate;
          const Icon = config.icon;
          
          return (
            <div 
              key={idx} 
              className={`${config.bg} border ${config.border} rounded-lg p-3`}
            >
              <div className="flex items-start gap-3">
                <div className={`p-1.5 rounded-full ${config.badge}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-sm text-slate-800">{factor.title}</span>
                    {factor.policy_id && (
                      onPolicyClick ? (
                        <button
                          onClick={() => onPolicyClick(factor.policy_id!)}
                          className="flex items-center gap-1 text-xs font-mono bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded hover:bg-indigo-200 transition-colors cursor-pointer"
                          title="Click to view policy details"
                        >
                          {factor.policy_id}
                          <ExternalLink className="w-3 h-3" />
                        </button>
                      ) : (
                        <span className="text-xs font-mono bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded">
                          {factor.policy_id}
                        </span>
                      )
                    )}
                  </div>
                  <p className="text-xs text-slate-600 mt-1">{factor.description}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Policy List Card
export function PolicyListCard({ 
  data, 
  onPolicyClick 
}: { 
  data: PolicyListResponse;
  onPolicyClick?: (policyId: string) => void;
}) {
  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-600">{data.summary}</p>
      
      <div className="space-y-2">
        {data.policies.map((policy, idx) => (
          onPolicyClick ? (
            <button
              key={idx}
              onClick={() => onPolicyClick(policy.policy_id)}
              className="w-full text-left bg-slate-50 border border-slate-200 rounded-lg p-3 hover:bg-indigo-50 hover:border-indigo-200 transition-colors cursor-pointer group"
              title="Click to view full policy details"
            >
              <div className="flex items-center gap-2 mb-2">
                <Shield className="w-4 h-4 text-indigo-600" />
                <span className="font-mono text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded">
                  {policy.policy_id}
                </span>
                <span className="font-medium text-sm text-slate-800 flex-1">{policy.name}</span>
                <ExternalLink className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 transition-colors" />
              </div>
              <div className="pl-6 space-y-1">
                <p className="text-xs text-slate-500">
                  <span className="font-medium">Relevance:</span> {policy.relevance}
                </p>
                <p className="text-xs text-slate-700">
                  <span className="font-medium">Finding:</span> {policy.finding}
                </p>
              </div>
            </button>
          ) : (
            <div 
              key={idx}
              className="bg-slate-50 border border-slate-200 rounded-lg p-3"
            >
              <div className="flex items-center gap-2 mb-2">
                <Shield className="w-4 h-4 text-indigo-600" />
                <span className="font-mono text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded">
                  {policy.policy_id}
                </span>
                <span className="font-medium text-sm text-slate-800">{policy.name}</span>
              </div>
              <div className="pl-6 space-y-1">
                <p className="text-xs text-slate-500">
                  <span className="font-medium">Relevance:</span> {policy.relevance}
                </p>
                <p className="text-xs text-slate-700">
                  <span className="font-medium">Finding:</span> {policy.finding}
                </p>
              </div>
            </div>
          )
        ))}
      </div>
    </div>
  );
}

// Recommendation Card
export function RecommendationCard({ data }: { data: RecommendationResponse }) {
  const config = decisionConfig[data.decision] || decisionConfig.defer;
  const DecisionIcon = config.icon;

  return (
    <div className="space-y-3">
      {/* Decision Banner */}
      <div className={`${config.bg} border-2 ${config.border} rounded-lg p-4`}>
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-full ${config.bg}`}>
            <DecisionIcon className={`w-6 h-6 ${config.text}`} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className={`text-lg font-bold ${config.text}`}>
                {config.label}
              </span>
              <span className={`text-xs px-2 py-0.5 rounded-full ${
                data.confidence === 'high' ? 'bg-emerald-100 text-emerald-700' :
                data.confidence === 'medium' ? 'bg-amber-100 text-amber-700' :
                'bg-slate-100 text-slate-600'
              }`}>
                {data.confidence} confidence
              </span>
            </div>
            <p className="text-sm text-slate-600 mt-1">{data.summary}</p>
          </div>
        </div>
      </div>

      {/* Conditions */}
      {data.conditions && data.conditions.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="w-4 h-4 text-amber-600" />
            <span className="text-sm font-medium text-amber-800">Conditions</span>
          </div>
          <ul className="space-y-1 pl-6">
            {data.conditions.map((condition, idx) => (
              <li key={idx} className="text-sm text-amber-700 list-disc">{condition}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Rationale */}
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
        <div className="flex items-center gap-2 mb-2">
          <FileText className="w-4 h-4 text-slate-600" />
          <span className="text-sm font-medium text-slate-700">Rationale</span>
        </div>
        <p className="text-sm text-slate-600 pl-6">{data.rationale}</p>
      </div>

      {/* Next Steps */}
      {data.next_steps && data.next_steps.length > 0 && (
        <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-2">
            <ArrowRight className="w-4 h-4 text-indigo-600" />
            <span className="text-sm font-medium text-indigo-700">Next Steps</span>
          </div>
          <ul className="space-y-1 pl-6">
            {data.next_steps.map((step, idx) => (
              <li key={idx} className="text-sm text-indigo-600 list-disc">{step}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// Comparison Table Card
export function ComparisonCard({ data }: { data: ComparisonResponse }) {
  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium text-slate-800">{data.title}</h4>
      <div className="overflow-x-auto">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="bg-slate-100">
              <th className="text-left p-2 border border-slate-200 font-medium text-slate-700"></th>
              {data.columns.map((col, idx) => (
                <th key={idx} className="text-left p-2 border border-slate-200 font-medium text-slate-700">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.rows.map((row, idx) => (
              <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-slate-50'}>
                <td className="p-2 border border-slate-200 font-medium text-slate-700">{row.label}</td>
                {row.values.map((val, vidx) => (
                  <td key={vidx} className="p-2 border border-slate-200 text-slate-600">{val}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Parse JSON from content (handles ```json blocks)
export function parseStructuredContent(content: string): { structured: StructuredResponse | null; plainText: string } {
  // Look for JSON code blocks
  const jsonMatch = content.match(/```json\s*([\s\S]*?)```/);
  
  if (jsonMatch) {
    try {
      const parsed = JSON.parse(jsonMatch[1].trim());
      if (parsed.type && ['risk_factors', 'policy_list', 'recommendation', 'comparison'].includes(parsed.type)) {
        // Extract any text before/after the JSON block
        const beforeJson = content.slice(0, jsonMatch.index).trim();
        const afterJson = content.slice((jsonMatch.index || 0) + jsonMatch[0].length).trim();
        const plainText = [beforeJson, afterJson].filter(Boolean).join('\n\n');
        
        return { structured: parsed as StructuredResponse, plainText };
      }
    } catch (e) {
      // JSON parse failed, return as plain text
      console.debug('Failed to parse JSON in chat response:', e);
    }
  }
  
  return { structured: null, plainText: content };
}

// Format plain text with policy IDs and basic styling
function formatPlainText(text: string): React.ReactNode {
  // Handle policy IDs and bold text
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  
  // Regex to match policy IDs or bold text
  const combinedRegex = /(\b[A-Z]+-[A-Z]+-\d+\b|\*\*.*?\*\*)/g;
  let match;
  
  while ((match = combinedRegex.exec(text)) !== null) {
    // Add text before the match
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    
    const matchedText = match[0];
    if (matchedText.startsWith('**') && matchedText.endsWith('**')) {
      // Bold text
      parts.push(
        <strong key={match.index}>{matchedText.slice(2, -2)}</strong>
      );
    } else {
      // Policy ID
      parts.push(
        <span 
          key={match.index}
          className="font-mono text-xs bg-indigo-100 text-indigo-700 px-1 py-0.5 rounded"
        >
          {matchedText}
        </span>
      );
    }
    
    lastIndex = match.index + matchedText.length;
  }
  
  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }
  
  return parts.length > 0 ? parts : text;
}

// Main renderer component
export function StructuredContentRenderer({ 
  content, 
  onPolicyClick 
}: { 
  content: string;
  onPolicyClick?: (policyId: string) => void;
}) {
  const { structured, plainText } = parseStructuredContent(content);
  
  return (
    <div className="space-y-3">
      {/* Render plain text if present */}
      {plainText && (
        <div className="text-sm whitespace-pre-wrap">{formatPlainText(plainText)}</div>
      )}
      
      {/* Render structured content */}
      {structured && (
        <div className="mt-2">
          {structured.type === 'risk_factors' && <RiskFactorsCard data={structured} onPolicyClick={onPolicyClick} />}
          {structured.type === 'policy_list' && <PolicyListCard data={structured} onPolicyClick={onPolicyClick} />}
          {structured.type === 'recommendation' && <RecommendationCard data={structured} />}
          {structured.type === 'comparison' && <ComparisonCard data={structured} />}
        </div>
      )}
    </div>
  );
}
