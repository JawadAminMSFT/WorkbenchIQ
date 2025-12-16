'use client';

import { useState, useRef, useEffect } from 'react';
import { Info, AlertTriangle, Shield, FileText } from 'lucide-react';
import type { PolicyCitation } from '@/lib/types';

interface RiskRatingPopoverProps {
  rating: string;
  rationale?: string;
  citations?: PolicyCitation[];
  onPolicyClick?: (policyId: string) => void;
}

function getRatingColor(rating: string): { bg: string; text: string; border: string } {
  const lowerRating = rating.toLowerCase();
  if (lowerRating.includes('high')) {
    return { bg: 'bg-rose-100', text: 'text-rose-700', border: 'border-rose-200' };
  }
  if (lowerRating.includes('moderate')) {
    return { bg: 'bg-amber-100', text: 'text-amber-700', border: 'border-amber-200' };
  }
  return { bg: 'bg-emerald-100', text: 'text-emerald-700', border: 'border-emerald-200' };
}

function getRatingIcon(rating: string) {
  const lowerRating = rating.toLowerCase();
  if (lowerRating.includes('high')) {
    return <AlertTriangle className="w-4 h-4" />;
  }
  return <Shield className="w-4 h-4" />;
}

export default function RiskRatingPopover({
  rating,
  rationale,
  citations = [],
  onPolicyClick,
}: RiskRatingPopoverProps) {
  const [isOpen, setIsOpen] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLDivElement>(null);
  const colors = getRatingColor(rating);

  // Close popover when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        popoverRef.current &&
        !popoverRef.current.contains(event.target as Node) &&
        triggerRef.current &&
        !triggerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Close on escape key
  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen]);

  return (
    <div className="relative inline-block">
      {/* Trigger Badge */}
      <div
        ref={triggerRef}
        onClick={() => setIsOpen(!isOpen)}
        onMouseEnter={() => setIsOpen(true)}
        className={`
          inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium cursor-pointer
          transition-all hover:shadow-md
          ${colors.bg} ${colors.text} ${colors.border} border
        `}
        role="button"
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        {getRatingIcon(rating)}
        {rating}
        {(rationale || citations.length > 0) && (
          <Info className="w-3 h-3 opacity-60" />
        )}
      </div>

      {/* Popover Content */}
      {isOpen && (rationale || citations.length > 0) && (
        <div
          ref={popoverRef}
          className="absolute z-50 mt-2 w-80 bg-white rounded-lg shadow-xl border border-slate-200 overflow-hidden"
          style={{ left: '50%', transform: 'translateX(-50%)' }}
        >
          {/* Header */}
          <div className={`px-4 py-3 border-b ${colors.bg}`}>
            <div className="flex items-center gap-2">
              {getRatingIcon(rating)}
              <span className={`font-semibold ${colors.text}`}>
                Risk Rating: {rating}
              </span>
            </div>
          </div>

          {/* Rationale */}
          {rationale && (
            <div className="px-4 py-3 border-b border-slate-100">
              <h4 className="text-xs font-semibold text-slate-500 uppercase mb-1">
                Rationale
              </h4>
              <p className="text-sm text-slate-700 leading-relaxed">
                {rationale}
              </p>
            </div>
          )}

          {/* Policy Citations */}
          {citations.length > 0 && (
            <div className="px-4 py-3">
              <h4 className="text-xs font-semibold text-slate-500 uppercase mb-2">
                Policy Citations
              </h4>
              <div className="space-y-2">
                {citations.map((citation, idx) => (
                  <div
                    key={idx}
                    className="p-2 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
                    onClick={() => onPolicyClick?.(citation.policy_id)}
                  >
                    <div className="flex items-start gap-2">
                      <FileText className="w-4 h-4 text-indigo-500 mt-0.5 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded">
                            {citation.policy_id}
                          </span>
                          <span className="text-xs font-medium text-slate-700 truncate">
                            {citation.policy_name}
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 mt-1">
                          {citation.criteria_applied}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs text-slate-500">
                            Finding: {citation.finding}
                          </span>
                          <span className={`text-xs font-medium ${
                            citation.rating_impact.toLowerCase().includes('increase') ||
                            citation.rating_impact.toLowerCase().includes('high')
                              ? 'text-rose-600'
                              : citation.rating_impact.toLowerCase().includes('moderate')
                              ? 'text-amber-600'
                              : 'text-emerald-600'
                          }`}>
                            {citation.rating_impact}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Empty state if no details */}
          {!rationale && citations.length === 0 && (
            <div className="px-4 py-3 text-sm text-slate-500 italic">
              No additional details available.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
