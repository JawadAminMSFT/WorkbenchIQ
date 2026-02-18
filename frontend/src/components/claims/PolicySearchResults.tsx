'use client';

import { Shield, FileText, Tag, ExternalLink, Percent, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import type { ClaimsPolicySearchResult } from '@/lib/api';

interface PolicySearchResultsProps {
  results: ClaimsPolicySearchResult[];
  onPolicySelect?: (result: ClaimsPolicySearchResult) => void;
}

// Category styling configuration
const categoryConfig: Record<string, { bg: string; text: string; border: string }> = {
  'fraud_detection': {
    bg: 'bg-rose-50',
    text: 'text-rose-700',
    border: 'border-rose-200',
  },
  'liability_determination': {
    bg: 'bg-blue-50',
    text: 'text-blue-700',
    border: 'border-blue-200',
  },
  'damage_assessment': {
    bg: 'bg-amber-50',
    text: 'text-amber-700',
    border: 'border-amber-200',
  },
  'payout_calculation': {
    bg: 'bg-emerald-50',
    text: 'text-emerald-700',
    border: 'border-emerald-200',
  },
  'default': {
    bg: 'bg-slate-50',
    text: 'text-slate-700',
    border: 'border-slate-200',
  },
};

function getCategoryConfig(category: string) {
  return categoryConfig[category] || categoryConfig.default;
}

function formatCategoryLabel(category: string): string {
  return category
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function getMatchColor(score: number): string {
  if (score >= 0.7) return 'text-emerald-600';
  if (score >= 0.5) return 'text-amber-600';
  if (score >= 0.3) return 'text-orange-600';
  return 'text-slate-500';
}

function getMatchBg(score: number): string {
  if (score >= 0.7) return 'bg-emerald-100';
  if (score >= 0.5) return 'bg-amber-100';
  if (score >= 0.3) return 'bg-orange-100';
  return 'bg-slate-100';
}

// Parse structured content from policy text
function parseContent(content: string): { 
  condition?: string; 
  riskLevel?: string; 
  action?: string; 
  rationale?: string;
  modifyingFactors?: string[];
  description?: string;
} {
  const result: ReturnType<typeof parseContent> = {};
  
  // Try to extract structured parts
  const conditionMatch = content.match(/Condition:\s*([^R]+?)(?=Risk Level:|Action:|Rationale:|$)/i);
  const riskMatch = content.match(/Risk Level:\s*(\w+)/i);
  const actionMatch = content.match(/Action:\s*([^R]+?)(?=Rationale:|$)/i);
  const rationaleMatch = content.match(/Rationale:\s*(.+?)(?=$)/i);
  const descriptionMatch = content.match(/Description:\s*([^C]+?)(?=Condition:|$)/i);
  
  // Check for modifying factors format
  const modifyingMatch = content.match(/Modifying Factors:\s*(.+)/i);
  if (modifyingMatch) {
    // Parse bullet-style factors
    const factors = modifyingMatch[1].split(/\s*-\s*/).filter(f => f.trim());
    result.modifyingFactors = factors;
  }
  
  if (conditionMatch) result.condition = conditionMatch[1].trim();
  if (riskMatch) result.riskLevel = riskMatch[1].trim();
  if (actionMatch) result.action = actionMatch[1].trim();
  if (rationaleMatch) result.rationale = rationaleMatch[1].trim();
  if (descriptionMatch) result.description = descriptionMatch[1].trim();
  
  return result;
}

function getRiskLevelStyle(level: string): { bg: string; text: string } {
  const lowerLevel = level.toLowerCase();
  if (lowerLevel.includes('high') || lowerLevel.includes('critical')) {
    return { bg: 'bg-rose-100', text: 'text-rose-700' };
  }
  if (lowerLevel.includes('moderate') || lowerLevel.includes('medium')) {
    return { bg: 'bg-amber-100', text: 'text-amber-700' };
  }
  return { bg: 'bg-emerald-100', text: 'text-emerald-700' };
}

export function PolicySearchResultCard({ 
  result, 
  onSelect 
}: { 
  result: ClaimsPolicySearchResult;
  onSelect?: () => void;
}) {
  const config = getCategoryConfig(result.category);
  // Use similarity (from backend) or score (legacy) 
  const score = result.similarity ?? result.score ?? 0;
  const matchPercent = Math.round(score * 100);
  const parsed = parseContent(result.content);
  const hasStructuredContent = parsed.condition || parsed.riskLevel || parsed.action;
  
  return (
    <button
      onClick={onSelect}
      disabled={!onSelect}
      className={`w-full text-left ${config.bg} border ${config.border} rounded-lg p-4 hover:shadow-md transition-all ${onSelect ? 'cursor-pointer hover:scale-[1.01]' : ''}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <Shield className={`w-4 h-4 ${config.text}`} />
          <span className="font-semibold text-slate-900">{result.policy_name}</span>
        </div>
        {!isNaN(matchPercent) && (
          <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getMatchBg(score)} ${getMatchColor(score)}`}>
            <Percent className="w-3 h-3" />
            {matchPercent}% match
          </div>
        )}
      </div>
      
      {/* Policy ID and Category */}
      <div className="flex items-center gap-2 mb-3 flex-wrap">
        <span className="inline-flex items-center gap-1 text-xs font-mono bg-indigo-100 text-indigo-700 px-2 py-1 rounded">
          <FileText className="w-3 h-3" />
          {result.policy_id}
        </span>
        <span className={`inline-flex items-center gap-1 text-xs px-2 py-1 rounded ${config.bg} ${config.text} border ${config.border}`}>
          <Tag className="w-3 h-3" />
          {formatCategoryLabel(result.category)}
        </span>
        {parsed.riskLevel && (
          <span className={`inline-flex items-center gap-1 text-xs px-2 py-1 rounded ${getRiskLevelStyle(parsed.riskLevel).bg} ${getRiskLevelStyle(parsed.riskLevel).text}`}>
            <AlertTriangle className="w-3 h-3" />
            {parsed.riskLevel} Risk
          </span>
        )}
      </div>
      
      {/* Structured Content Display */}
      {hasStructuredContent ? (
        <div className="space-y-2 text-sm">
          {parsed.condition && (
            <div className="flex items-start gap-2">
              <Info className="w-4 h-4 text-slate-500 mt-0.5 flex-shrink-0" />
              <div>
                <span className="font-medium text-slate-800">When: </span>
                <span className="text-slate-700">{parsed.condition}</span>
              </div>
            </div>
          )}
          {parsed.action && (
            <div className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
              <div>
                <span className="font-medium text-slate-800">Action: </span>
                <span className="text-slate-700">{parsed.action}</span>
              </div>
            </div>
          )}
          {parsed.rationale && (
            <p className="text-xs text-slate-500 italic mt-1 pl-6">
              {parsed.rationale}
            </p>
          )}
        </div>
      ) : (
        // Fallback to original content if not parseable
        <p className="text-sm text-slate-700 leading-relaxed line-clamp-3">
          {result.content}
        </p>
      )}
      
      {/* View Details hint */}
      {onSelect && (
        <div className="flex items-center justify-end gap-1 mt-3 text-xs text-indigo-600">
          <span>View details</span>
          <ExternalLink className="w-3 h-3" />
        </div>
      )}
    </button>
  );
}

export default function PolicySearchResults({ 
  results, 
  onPolicySelect 
}: PolicySearchResultsProps) {
  if (results.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500">
        <Shield className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>No policies found. Try a different search term.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="text-xs text-slate-500 mb-2">
        Found {results.length} matching {results.length === 1 ? 'policy' : 'policies'}
      </div>
      {results.map((result) => (
        <PolicySearchResultCard
          key={result.chunk_id}
          result={result}
          onSelect={onPolicySelect ? () => onPolicySelect(result) : undefined}
        />
      ))}
    </div>
  );
}
