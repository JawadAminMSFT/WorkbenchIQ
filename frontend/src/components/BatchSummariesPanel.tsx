'use client';

import { useState } from 'react';
import { FileStack, ChevronDown, ChevronUp, FileText, AlertTriangle } from 'lucide-react';
import type { BatchSummary } from '@/lib/types';
import clsx from 'clsx';

interface BatchSummariesPanelProps {
  batchSummaries: BatchSummary[];
  onPageClick?: (pageNumber: number) => void;
}

export default function BatchSummariesPanel({ batchSummaries, onPageClick }: BatchSummariesPanelProps) {
  const [expandedBatches, setExpandedBatches] = useState<Set<number>>(new Set([1])); // First batch expanded by default

  if (!batchSummaries || batchSummaries.length === 0) {
    return null;
  }

  const toggleBatch = (batchNum: number) => {
    const newExpanded = new Set(expandedBatches);
    if (newExpanded.has(batchNum)) {
      newExpanded.delete(batchNum);
    } else {
      newExpanded.add(batchNum);
    }
    setExpandedBatches(newExpanded);
  };

  const expandAll = () => {
    setExpandedBatches(new Set(batchSummaries.map(b => b.batch_num)));
  };

  const collapseAll = () => {
    setExpandedBatches(new Set());
  };

  // Parse summary to extract key sections
  const parseSummary = (summary: string) => {
    const sections: { title: string; content: string; isHighRisk?: boolean }[] = [];
    const lines = summary.split('\n');
    let currentSection = '';
    let currentContent: string[] = [];

    for (const line of lines) {
      // Detect section headers (numbered items or bold headers)
      const sectionMatch = line.match(/^\d+\.\s*\*\*([^*]+)\*\*:?/) || 
                          line.match(/^###?\s*(.+)/) ||
                          line.match(/^\*\*([^*]+)\*\*:?/);
      
      if (sectionMatch) {
        // Save previous section
        if (currentSection && currentContent.length > 0) {
          const isHighRisk = currentSection.toLowerCase().includes('risk') || 
                            currentSection.toLowerCase().includes('finding') ||
                            currentSection.toLowerCase().includes('abnormal');
          sections.push({
            title: currentSection,
            content: currentContent.join('\n').trim(),
            isHighRisk
          });
        }
        currentSection = sectionMatch[1].trim();
        currentContent = [];
      } else if (line.trim()) {
        currentContent.push(line);
      }
    }

    // Save last section
    if (currentSection && currentContent.length > 0) {
      const isHighRisk = currentSection.toLowerCase().includes('risk') || 
                        currentSection.toLowerCase().includes('finding') ||
                        currentSection.toLowerCase().includes('abnormal');
      sections.push({
        title: currentSection,
        content: currentContent.join('\n').trim(),
        isHighRisk
      });
    }

    return sections.length > 0 ? sections : [{ title: 'Summary', content: summary, isHighRisk: false }];
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileStack className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">
              Document Insights by Section
            </h2>
            <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-700 rounded-full">
              {batchSummaries.length} batches
            </span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={expandAll}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              Expand All
            </button>
            <span className="text-gray-300">|</span>
            <button
              onClick={collapseAll}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              Collapse All
            </button>
          </div>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          AI-generated summaries from progressive document analysis
        </p>
      </div>

      {/* Batch List */}
      <div className="divide-y divide-gray-100 max-h-[600px] overflow-y-auto">
        {batchSummaries.map((batch) => {
          const isExpanded = expandedBatches.has(batch.batch_num);
          const sections = parseSummary(batch.summary);
          const hasHighRisk = sections.some(s => s.isHighRisk && s.content.trim().length > 0);

          return (
            <div key={batch.batch_num} className="bg-white">
              {/* Batch Header */}
              <button
                onClick={() => toggleBatch(batch.batch_num)}
                className={clsx(
                  "w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors",
                  hasHighRisk && "bg-amber-50 hover:bg-amber-100"
                )}
              >
                <div className="flex items-center gap-3">
                  <div className={clsx(
                    "flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium",
                    hasHighRisk ? "bg-amber-200 text-amber-800" : "bg-blue-100 text-blue-700"
                  )}>
                    {batch.batch_num}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">
                        Pages {batch.page_start} - {batch.page_end}
                      </span>
                      {hasHighRisk && (
                        <span className="flex items-center gap-1 px-1.5 py-0.5 text-xs font-medium bg-amber-100 text-amber-800 rounded">
                          <AlertTriangle className="w-3 h-3" />
                          Notable Findings
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-gray-500">
                      {batch.page_count} pages analyzed
                    </span>
                  </div>
                </div>
                {isExpanded ? (
                  <ChevronUp className="w-5 h-5 text-gray-400" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-400" />
                )}
              </button>

              {/* Expanded Content */}
              {isExpanded && (
                <div className="px-4 pb-4 pt-2 bg-gray-50 border-t border-gray-100">
                  <div className="space-y-3">
                    {sections.map((section, idx) => (
                      <div key={idx} className={clsx(
                        "p-3 rounded-lg",
                        section.isHighRisk ? "bg-amber-50 border border-amber-200" : "bg-white border border-gray-200"
                      )}>
                        <div className="flex items-center gap-2 mb-2">
                          {section.isHighRisk ? (
                            <AlertTriangle className="w-4 h-4 text-amber-600" />
                          ) : (
                            <FileText className="w-4 h-4 text-gray-400" />
                          )}
                          <h4 className={clsx(
                            "text-sm font-medium",
                            section.isHighRisk ? "text-amber-800" : "text-gray-700"
                          )}>
                            {section.title}
                          </h4>
                        </div>
                        <div className="text-sm text-gray-600 whitespace-pre-wrap pl-6">
                          {section.content || <span className="text-gray-400 italic">No information in this section</span>}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Page Links */}
                  {onPageClick && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs text-gray-500">View pages:</span>
                        {Array.from({ length: batch.page_end - batch.page_start + 1 }, (_, i) => batch.page_start + i).map((pageNum) => (
                          <button
                            key={pageNum}
                            onClick={() => onPageClick(pageNum)}
                            className="px-2 py-0.5 text-xs bg-gray-100 hover:bg-blue-100 hover:text-blue-700 rounded transition-colors"
                          >
                            {pageNum}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
