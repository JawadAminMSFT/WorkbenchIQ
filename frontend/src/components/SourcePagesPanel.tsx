'use client';

import { useState, useEffect } from 'react';
import { FileStack, Copy, Check } from 'lucide-react';
import type { MarkdownPage } from '@/lib/types';

interface SourcePagesPanelProps {
  pages: MarkdownPage[];
  selectedPageNumber?: number; // 1-indexed page number to navigate to
}

export default function SourcePagesPanel({ pages, selectedPageNumber }: SourcePagesPanelProps) {
  const [selectedPage, setSelectedPage] = useState<number>(0);
  const [copied, setCopied] = useState(false);

  // Navigate to page when selectedPageNumber changes
  useEffect(() => {
    if (selectedPageNumber && pages.length > 0) {
      // Find the index of the page with this page_number
      const pageIndex = pages.findIndex(p => p.page_number === selectedPageNumber);
      if (pageIndex >= 0) {
        setSelectedPage(pageIndex);
      }
    }
  }, [selectedPageNumber, pages]);

  if (!pages || pages.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Source Pages</h2>
        <div className="text-center py-8 text-gray-500">
          <FileStack className="w-12 h-12 mx-auto mb-2 text-gray-400" />
          <p>No extracted content available.</p>
          <p className="text-sm mt-2">
            Run document extraction from the Admin page to extract text content.
          </p>
        </div>
      </div>
    );
  }

  const currentPage = pages[selectedPage];

  const handleCopy = async () => {
    if (currentPage?.markdown) {
      await navigator.clipboard.writeText(currentPage.markdown);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Group pages by file
  const pagesByFile: Record<string, MarkdownPage[]> = {};
  pages.forEach((page) => {
    const key = page.file || 'Unknown';
    if (!pagesByFile[key]) {
      pagesByFile[key] = [];
    }
    pagesByFile[key].push(page);
  });

  return (
    <div className="bg-white rounded-xl border border-gray-200 h-full flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">
            Source Pages ({pages.length})
          </h2>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4 text-green-600" />
                <span className="text-green-600">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Page Navigator */}
        <div className="w-48 border-r border-gray-200 overflow-y-auto bg-gray-50">
          {Object.entries(pagesByFile).map(([fileName, filePages]) => (
            <div key={fileName} className="p-2">
              <h3 className="text-xs font-semibold text-gray-500 uppercase px-2 mb-1 truncate" title={fileName}>
                {fileName.split('/').pop() || fileName}
              </h3>
              <ul className="space-y-0.5">
                {filePages.map((page, idx) => {
                  const globalIdx = pages.indexOf(page);
                  return (
                    <li key={globalIdx}>
                      <button
                        onClick={() => setSelectedPage(globalIdx)}
                        className={`w-full text-left px-2 py-1.5 text-sm rounded transition-colors ${
                          selectedPage === globalIdx
                            ? 'bg-blue-100 text-blue-700 font-medium'
                            : 'text-gray-700 hover:bg-gray-100'
                        }`}
                      >
                        Page {page.page_number}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>

        {/* Content Viewer */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="mb-4 flex items-center justify-between">
            <div className="text-sm text-gray-500">
              <span className="font-medium text-gray-700">
                {currentPage?.file?.split('/').pop() || 'Document'}
              </span>
              {' — '}
              Page {currentPage?.page_number}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setSelectedPage(Math.max(0, selectedPage - 1))}
                disabled={selectedPage === 0}
                className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ← Prev
              </button>
              <span className="text-sm text-gray-500">
                {selectedPage + 1} of {pages.length}
              </span>
              <button
                onClick={() =>
                  setSelectedPage(Math.min(pages.length - 1, selectedPage + 1))
                }
                disabled={selectedPage === pages.length - 1}
                className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next →
              </button>
            </div>
          </div>

          <div className="prose prose-sm max-w-none">
            <pre className="whitespace-pre-wrap text-sm text-gray-800 bg-gray-50 p-4 rounded-lg border border-gray-200 font-mono">
              {currentPage?.markdown || 'No content available for this page.'}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
