'use client';

import React, { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle, Loader2 } from 'lucide-react';
import { uploadDocument } from '../../lib/broker-api';
import type { SubmissionDocument } from '../../lib/broker-types';

const DOCUMENT_TYPES = [
  { value: 'sov', label: 'SOV', color: 'bg-blue-100 text-blue-700' },
  { value: 'loss_runs', label: 'Loss Runs', color: 'bg-purple-100 text-purple-700' },
  { value: 'prior_declaration', label: 'Prior Declaration', color: 'bg-green-100 text-green-700' },
  { value: 'acord_125', label: 'ACORD 125', color: 'bg-amber-100 text-amber-700' },
  { value: 'acord_140', label: 'ACORD 140', color: 'bg-orange-100 text-orange-700' },
  { value: 'other', label: 'Other', color: 'bg-slate-100 text-slate-700' },
] as const;

interface DocumentUploadPanelProps {
  submissionId: string;
  documents: SubmissionDocument[];
  onDocumentUploaded: () => void;
  onExtractAcord: () => void;
  extracting: boolean;
}

function docTypeBadge(docType: string) {
  const dt = DOCUMENT_TYPES.find((d) => d.value === docType);
  if (!dt) {
    return (
      <span className="text-xs px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
        {docType}
      </span>
    );
  }
  return (
    <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${dt.color}`}>
      {dt.label}
    </span>
  );
}

export default function DocumentUploadPanel({
  submissionId,
  documents,
  onDocumentUploaded,
  onExtractAcord,
  extracting,
}: DocumentUploadPanelProps) {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedDocType, setSelectedDocType] = useState('sov');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      await uploadDocument(submissionId, file, selectedDocType);
      onDocumentUploaded();
    } catch (err) {
      console.error('Failed to upload document:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleUpload(file);
  };

  return (
    <div className="space-y-4">
      {/* Document Type Selector */}
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-slate-700">
          Document type:
        </label>
        <select
          value={selectedDocType}
          onChange={(e) => setSelectedDocType(e.target.value)}
          className="px-3 py-1.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
        >
          {DOCUMENT_TYPES.map((dt) => (
            <option key={dt.value} value={dt.value}>
              {dt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Drop Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive
            ? 'border-amber-400 bg-amber-50'
            : 'border-slate-200 hover:border-slate-300'
        }`}
      >
        {uploading ? (
          <Loader2 className="w-8 h-8 text-amber-500 mx-auto mb-2 animate-spin" />
        ) : (
          <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
        )}
        <p className="text-sm text-slate-500">
          Drop SOV, loss runs, prior declarations here or{' '}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="text-amber-600 hover:text-amber-700 font-medium"
            disabled={uploading}
          >
            Browse Files
          </button>
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.xlsx,.xls,.csv,.doc,.docx"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleUpload(file);
            if (e.target) e.target.value = '';
          }}
        />
        {uploading && (
          <p className="text-xs text-amber-600 mt-2">Uploading…</p>
        )}
      </div>

      {/* Uploaded Documents List */}
      {(documents?.length ?? 0) > 0 && (
        <div>
          <p className="text-sm font-medium text-slate-700 mb-2">Uploaded:</p>
          <div className="space-y-2">
            {documents?.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center gap-3 p-2.5 bg-slate-50 rounded-lg"
              >
                <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                <FileText className="w-4 h-4 text-slate-400 flex-shrink-0" />
                <span className="text-sm text-slate-700 flex-1 truncate">
                  {doc.file_name}
                </span>
                {docTypeBadge(doc.document_type)}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Extract ACORD Fields Button */}
      {(documents?.length ?? 0) > 0 && (
        <button
          onClick={onExtractAcord}
          disabled={extracting}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 disabled:opacity-50 rounded-lg transition-colors"
        >
          {extracting && <Loader2 className="w-4 h-4 animate-spin" />}
          {extracting ? 'Extracting…' : 'Extract ACORD Fields'}
        </button>
      )}
    </div>
  );
}
