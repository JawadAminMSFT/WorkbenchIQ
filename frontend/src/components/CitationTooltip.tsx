'use client';

import { useState, useRef, useEffect } from 'react';
import { FileText, MapPin, Quote, ExternalLink } from 'lucide-react';

export interface CitationData {
  sourceFile?: string;
  pageNumber?: number;
  sourceText?: string;
  boundingBox?: number[];
  fieldName?: string;
}

interface CitationTooltipProps {
  citation: CitationData;
  appId?: string;  // Application ID for building PDF URLs
  onViewDocument?: (pageNumber: number, sourceFile?: string) => void;
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
}

/**
 * Truncate text to a maximum length with ellipsis
 */
function truncateText(text: string, maxLength: number = 150): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).trim() + '...';
}

/**
 * CitationTooltip - Shows source information for extracted facts
 * 
 * Displays:
 * - Source document filename
 * - Page number
 * - Original quoted text
 * - Confidence score
 * - Link to view in document
 */
export default function CitationTooltip({
  citation,
  appId,
  onViewDocument,
  children,
  position = 'top',
}: CitationTooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 });
  const triggerRef = useRef<HTMLSpanElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const hideTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const { sourceFile, pageNumber, sourceText, fieldName } = citation;

  // Handle showing tooltip
  const showTooltip = () => {
    if (hideTimeoutRef.current) {
      clearTimeout(hideTimeoutRef.current);
      hideTimeoutRef.current = null;
    }
    setIsVisible(true);
  };

  // Handle hiding tooltip with delay
  const hideTooltip = () => {
    hideTimeoutRef.current = setTimeout(() => {
      setIsVisible(false);
    }, 150); // Small delay to allow moving to tooltip
  };

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (hideTimeoutRef.current) {
        clearTimeout(hideTimeoutRef.current);
      }
    };
  }, []);

  // Calculate tooltip position
  useEffect(() => {
    if (isVisible && triggerRef.current && tooltipRef.current) {
      const triggerRect = triggerRef.current.getBoundingClientRect();
      const tooltipRect = tooltipRef.current.getBoundingClientRect();
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;

      let top = 0;
      let left = 0;

      switch (position) {
        case 'top':
          top = -tooltipRect.height - 8;
          left = (triggerRect.width - tooltipRect.width) / 2;
          break;
        case 'bottom':
          top = triggerRect.height + 8;
          left = (triggerRect.width - tooltipRect.width) / 2;
          break;
        case 'left':
          top = (triggerRect.height - tooltipRect.height) / 2;
          left = -tooltipRect.width - 8;
          break;
        case 'right':
          top = (triggerRect.height - tooltipRect.height) / 2;
          left = triggerRect.width + 8;
          break;
      }

      // Adjust if tooltip would go off screen
      const absoluteLeft = triggerRect.left + left;
      const absoluteTop = triggerRect.top + top;

      if (absoluteLeft < 10) {
        left = -triggerRect.left + 10;
      } else if (absoluteLeft + tooltipRect.width > viewportWidth - 10) {
        left = viewportWidth - triggerRect.left - tooltipRect.width - 10;
      }

      if (absoluteTop < 10) {
        // Flip to bottom
        top = triggerRect.height + 8;
      } else if (absoluteTop + tooltipRect.height > viewportHeight - 10) {
        // Flip to top
        top = -tooltipRect.height - 8;
      }

      setTooltipPosition({ top, left });
    }
  }, [isVisible, position]);

  // Don't render tooltip if no citation data
  const hasCitation = sourceFile || pageNumber || sourceText;
  if (!hasCitation) {
    return <>{children}</>;
  }

  return (
    <span
      ref={triggerRef}
      className="relative inline-flex items-center gap-1 cursor-help group"
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
    >
      {children}
      
      {/* Citation indicator */}
      <span className="inline-flex items-center justify-center w-4 h-4 text-[10px] font-medium text-indigo-600 bg-indigo-50 rounded border border-indigo-200 hover:bg-indigo-100 transition-colors">
        <FileText className="w-2.5 h-2.5" />
      </span>

      {/* Tooltip */}
      {isVisible && (
        <div
          ref={tooltipRef}
          onMouseEnter={showTooltip}
          onMouseLeave={hideTooltip}
          className="absolute z-50 w-72 bg-white rounded-lg shadow-xl border border-slate-200 overflow-hidden animate-in fade-in-0 zoom-in-95 duration-150"
          style={{
            top: tooltipPosition.top,
            left: tooltipPosition.left,
          }}
        >
          {/* Header */}
          <div className="bg-slate-50 px-3 py-2 border-b border-slate-200">
            <div className="flex items-center gap-2 text-xs font-medium text-slate-700">
              <Quote className="w-3.5 h-3.5 text-slate-400" />
              <span>Source Citation</span>
              {fieldName && (
                <span className="ml-auto text-slate-400 font-normal truncate max-w-[120px]">
                  {fieldName}
                </span>
              )}
            </div>
          </div>

          {/* Content */}
          <div className="p-3 space-y-3">
            {/* Source file and page */}
            <div className="flex items-start gap-2">
              <FileText className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
              <div className="text-sm">
                <div className="font-medium text-slate-700">
                  {sourceFile || 'Document'}
                </div>
                {pageNumber && (
                  <div className="flex items-center gap-1 text-slate-500 text-xs mt-0.5">
                    <MapPin className="w-3 h-3" />
                    Page {pageNumber}
                  </div>
                )}
              </div>
            </div>

            {/* Source text quote */}
            {sourceText && (
              <div className="bg-slate-50 rounded-md p-2 border-l-2 border-indigo-300">
                <p className="text-xs text-slate-600 italic leading-relaxed">
                  "{truncateText(sourceText, 200)}"
                </p>
              </div>
            )}

            {/* View in document link */}
            {onViewDocument && pageNumber && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onViewDocument(pageNumber, sourceFile);
                }}
                className="w-full flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-md transition-colors"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                View in Document
              </button>
            )}

            {/* Open PDF in new tab */}
            {appId && sourceFile && sourceFile.toLowerCase().endsWith('.pdf') && (
              <a
                href={`/api/applications/${appId}/files/${encodeURIComponent(sourceFile)}${pageNumber ? `#page=${pageNumber}` : ''}`}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="w-full flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-medium text-emerald-600 bg-emerald-50 hover:bg-emerald-100 rounded-md transition-colors"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                Open PDF
              </a>
            )}
          </div>

          {/* Arrow */}
          <div
            className="absolute w-2 h-2 bg-white border-slate-200 transform rotate-45"
            style={{
              ...(position === 'top' && {
                bottom: -5,
                left: '50%',
                marginLeft: -4,
                borderRight: '1px solid',
                borderBottom: '1px solid',
                borderColor: 'inherit',
              }),
              ...(position === 'bottom' && {
                top: -5,
                left: '50%',
                marginLeft: -4,
                borderLeft: '1px solid',
                borderTop: '1px solid',
                borderColor: 'inherit',
              }),
            }}
          />
        </div>
      )}
    </span>
  );
}

/**
 * Simple citation badge without tooltip (for compact displays)
 */
export function CitationBadge({
  pageNumber,
  sourceFile,
  className = '',
}: {
  pageNumber?: number;
  sourceFile?: string;
  className?: string;
}) {
  if (!pageNumber && !sourceFile) return null;

  return (
    <span
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-medium text-slate-500 bg-slate-100 rounded ${className}`}
      title={`Source: ${sourceFile || 'Document'}${pageNumber ? `, Page ${pageNumber}` : ''}`}
    >
      <FileText className="w-2.5 h-2.5" />
      {pageNumber && <span>p.{pageNumber}</span>}
    </span>
  );
}
