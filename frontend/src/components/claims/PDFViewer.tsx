'use client';

import React, { useState } from 'react';
import { X, ZoomIn, ZoomOut, Download, ExternalLink, FileText, AlertTriangle } from 'lucide-react';

interface PDFViewerProps {
  url: string;
  filename: string;
  onClose: () => void;
}

/**
 * PDFViewer - Modal component for viewing PDF documents inline
 * Uses object tag with embed fallback for better browser compatibility
 */
const PDFViewer: React.FC<PDFViewerProps> = ({ url, filename, onClose }) => {
  const [zoom, setZoom] = useState(100);
  const [loadError, setLoadError] = useState(false);

  const handleZoomIn = () => setZoom(Math.min(zoom + 25, 200));
  const handleZoomOut = () => setZoom(Math.max(zoom - 25, 50));

  // Construct a full URL if it's a relative path
  const fullUrl = url.startsWith('http') ? url : `${window.location.origin}${url}`;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3 bg-slate-900 border-b border-slate-700">
        <div className="flex items-center gap-4">
          <FileText className="w-5 h-5 text-rose-400" />
          <h3 className="text-white font-medium">{filename}</h3>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Zoom Controls */}
          <button
            onClick={handleZoomOut}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
            title="Zoom out"
          >
            <ZoomOut className="w-5 h-5" />
          </button>
          <span className="text-slate-400 text-sm min-w-[3rem] text-center">{zoom}%</span>
          <button
            onClick={handleZoomIn}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
            title="Zoom in"
          >
            <ZoomIn className="w-5 h-5" />
          </button>
          
          <div className="w-px h-6 bg-slate-700 mx-2" />
          
          {/* Open in new tab */}
          <a
            href={fullUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
            title="Open in new tab"
          >
            <ExternalLink className="w-5 h-5" />
          </a>
          
          {/* Download */}
          <a
            href={fullUrl}
            download={filename}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
            title="Download"
          >
            <Download className="w-5 h-5" />
          </a>
          
          <div className="w-px h-6 bg-slate-700 mx-2" />
          
          {/* Close */}
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* PDF Content */}
      <div className="flex-1 overflow-auto bg-slate-800 flex items-start justify-center p-6">
        {loadError ? (
          <div className="bg-white rounded-xl shadow-2xl p-12 text-center max-w-md">
            <AlertTriangle className="w-16 h-16 text-amber-500 mx-auto mb-4" />
            <h4 className="text-lg font-semibold text-slate-900 mb-2">Unable to display PDF</h4>
            <p className="text-slate-600 mb-6">The PDF cannot be displayed inline. You can open it in a new tab or download it.</p>
            <div className="flex gap-3 justify-center">
              <a
                href={fullUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                <ExternalLink className="w-4 h-4" />
                Open in New Tab
              </a>
              <a
                href={fullUrl}
                download={filename}
                className="inline-flex items-center gap-2 px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors"
              >
                <Download className="w-4 h-4" />
                Download
              </a>
            </div>
          </div>
        ) : (
          <div 
            className="bg-white shadow-2xl rounded-lg overflow-hidden"
            style={{ transform: `scale(${zoom / 100})`, transformOrigin: 'top center' }}
          >
            {/* Use object tag with embed fallback for better PDF rendering */}
            <object
              data={`${fullUrl}#toolbar=1&navpanes=1&view=FitH`}
              type="application/pdf"
              className="w-[900px] h-[calc(100vh-120px)] min-h-[800px]"
              onError={() => setLoadError(true)}
            >
              {/* Fallback: embed tag */}
              <embed
                src={`${fullUrl}#toolbar=1&navpanes=1&view=FitH`}
                type="application/pdf"
                className="w-[900px] h-[calc(100vh-120px)] min-h-[800px]"
              />
              {/* Ultimate fallback message */}
              <div className="p-8 text-center">
                <p className="text-slate-600">Unable to display PDF.</p>
                <a href={fullUrl} target="_blank" className="text-red-600 underline">
                  Click here to open in a new tab
                </a>
              </div>
            </object>
          </div>
        )}
      </div>
    </div>
  );
};

export default PDFViewer;
