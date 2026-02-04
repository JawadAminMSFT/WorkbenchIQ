'use client';

import { useState, useMemo } from 'react';
import { 
  Upload, 
  Plus, 
  FileText, 
  Clock, 
  AlertCircle,
  Loader2,
  ChevronRight,
  Search,
  LayoutGrid,
  List as ListIcon,
  CheckCircle2,
  AlertTriangle,
  Activity,
  TrendingUp,
  Calendar,
  Hash
} from 'lucide-react';
import { usePersona } from '@/lib/PersonaContext';
import { ApplicationListItem } from '@/lib/types';
import { createApplication, startProcessing } from '@/lib/api';
import clsx from 'clsx';

interface LandingPageProps {
  applications: ApplicationListItem[];
  onSelectApp: (appId: string) => void;
  onRefreshApps: () => void;
  loading: boolean;
}

export default function LandingPage({ 
  applications, 
  onSelectApp, 
  onRefreshApps,
  loading 
}: LandingPageProps) {
  const { currentPersona, personaConfig } = usePersona();
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list');
  const [largeDocumentMode, setLargeDocumentMode] = useState(false);

  // Helper to check conditions
  const isAutomotiveClaims = currentPersona === 'automotive_claims';
  const isUnderwritingPersona = currentPersona === 'underwriting';
  
  const getAcceptedFileTypes = () => {
    if (isAutomotiveClaims) {
      return '.pdf,.png,.jpg,.jpeg,.gif,.webp,.mp4,.mov,.avi,.webm';
    }
    return '.pdf';
  };
  
  const getAcceptedMimeTypes = () => {
    if (isAutomotiveClaims) {
      return ['application/pdf', 'image/png', 'image/jpeg', 'image/gif', 'image/webp', 'video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm'];
    }
    return ['application/pdf'];
  };

  // Dashboard Stats
  const stats = useMemo(() => {
    const total = applications.length;
    const completed = applications.filter(a => a.status === 'completed').length;
    const processing = applications.filter(a => ['extracting', 'analyzing', 'pending'].includes(a.status) || a.processing_status).length;
    const errors = applications.filter(a => a.status === 'error').length;
    
    // Get today's applications
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const todayCount = applications.filter(a => new Date(a.created_at) >= today).length;
    
    return { total, completed, processing, errors, todayCount };
  }, [applications]);

  // Priority Queues - Ready for Review vs In Progress
  const queues = useMemo(() => {
    // Ready for review: completed status, sorted by most recent
    const readyForReview = applications
      .filter(a => a.status === 'completed' && !a.processing_status)
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 5);
    
    // Needs AI analysis: pending, extracting, analyzing
    const needsAnalysis = applications
      .filter(a => a.status !== 'completed' && a.status !== 'error')
      .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
    
    // Errors requiring attention
    const hasErrors = applications.filter(a => a.status === 'error');
    
    return { readyForReview, needsAnalysis, hasErrors };
  }, [applications]);

  // Get time-based greeting
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 17) return 'Good Afternoon';
    return 'Good Evening';
  };

  // Generate display title for application
  const getAppDisplayTitle = (app: ApplicationListItem) => {
    if (app.summary_title) return app.summary_title;
    if (app.external_reference) return app.external_reference;
    // Format: Case {shortId}
    const shortId = app.id.substring(0, 8).toUpperCase();
    return `Case ${shortId}`;
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const acceptedTypes = getAcceptedMimeTypes();
    const files = Array.from(e.dataTransfer.files).filter(
      (f) => acceptedTypes.includes(f.type)
    );
    
    if (files.length > 0) {
      handleFiles(files);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const acceptedTypes = getAcceptedMimeTypes();
      const files = Array.from(e.target.files).filter(
        (f) => acceptedTypes.includes(f.type)
      );
      if (files.length > 0) {
        handleFiles(files);
      }
    }
  };

  const handleFiles = async (files: File[]) => {
    setUploading(true);
    setError(null);

    try {
      // 1. Create Application
      const app = await createApplication(
        files,
        undefined, // No external reference for quick start
        currentPersona
      );

      // 2. Start Processing with appropriate mode
      const processingMode = largeDocumentMode ? 'large_document' : 'standard';
      await startProcessing(app.id, processingMode);

      // 3. Refresh list and navigate
      onRefreshApps();
      onSelectApp(app.id);

    } catch (err) {
      console.error('Failed to create application:', err);
      setError(err instanceof Error ? err.message : 'Failed to create application');
      setUploading(false);
    }
  };

  // Filter applications
  const filteredApps = applications.filter(app => {
    const search = searchQuery.toLowerCase();
    return (
      app.id.toLowerCase().includes(search) || 
      app.external_reference?.toLowerCase().includes(search) ||
      app.summary_title?.toLowerCase().includes(search)
    );
  });

  const getStatusConfig = (status: string, processingStatus?: string | null) => {
    // Check for active processing first
    if (processingStatus === 'extracting') {
      return { 
        label: 'Data Agent Running', 
        bg: 'bg-sky-50', 
        text: 'text-sky-700', 
        border: 'border-sky-200',
        icon: Loader2,
        animate: true
      };
    }
    if (processingStatus === 'analyzing') {
      return { 
        label: 'Risk Agent Working', 
        bg: 'bg-violet-50', 
        text: 'text-violet-700', 
        border: 'border-violet-200',
        icon: Activity,
        animate: true
      };
    }
    
    const configs: Record<string, any> = {
      pending: { 
        label: 'Pending', 
        bg: 'bg-amber-50', 
        text: 'text-amber-700', 
        border: 'border-amber-200',
        icon: Clock
      },
      extracting: { 
        label: 'Data Agent Running', 
        bg: 'bg-sky-50', 
        text: 'text-sky-700', 
        border: 'border-sky-200',
        icon: Loader2,
        animate: true
      },
      analyzing: { 
        label: 'Risk Agent Working', 
        bg: 'bg-violet-50', 
        text: 'text-violet-700', 
        border: 'border-violet-200',
        icon: Activity,
        animate: true
      },
      completed: { 
        label: 'Ready for Review', 
        bg: 'bg-emerald-50', 
        text: 'text-emerald-700', 
        border: 'border-emerald-200',
        icon: CheckCircle2
      },
      error: { 
        label: 'Error', 
        bg: 'bg-rose-50', 
        text: 'text-rose-700', 
        border: 'border-rose-200',
        icon: AlertTriangle
      },
    };
    return configs[status] || configs.pending;
  };

  const StatusBadge = ({ status, processingStatus }: { status: string; processingStatus?: string | null }) => {
    const config = getStatusConfig(status, processingStatus);
    const Icon = config.icon;
    return (
      <span className={clsx(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border',
        config.bg, config.text, config.border
      )}>
        <Icon className={clsx('w-3 h-3', config.animate && 'animate-spin')} />
        {config.label}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-slate-50">
      
      {/* Dashboard Header */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 py-8">
          {/* Greeting Row */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                {getGreeting()}, Jawad!
              </h1>
              <p className="text-slate-500 mt-1 flex items-center gap-2">
                <span 
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: personaConfig.primaryColor }}
                />
                {personaConfig.name} Dashboard
              </p>
            </div>

            {/* New Application Button with Large Doc Toggle */}
            <div className="flex items-center gap-3">
              {/* Condense Context Toggle - Only for underwriting persona */}
              {isUnderwritingPersona && (
                <button
                  type="button"
                  onClick={() => setLargeDocumentMode(!largeDocumentMode)}
                  className={clsx(
                    "flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all border",
                    largeDocumentMode 
                      ? "bg-indigo-50 border-indigo-200 text-indigo-700" 
                      : "bg-white border-slate-200 text-slate-500 hover:border-slate-300 hover:text-slate-700"
                  )}
                  title="Enable for large documents (50+ pages). Summarizes content to fit within AI context limits."
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                  Condense
                  <span className={clsx(
                    "w-2 h-2 rounded-full transition-colors",
                    largeDocumentMode ? "bg-indigo-500" : "bg-slate-300"
                  )} />
                </button>
              )}
              
              <label 
                className={clsx(
                  "inline-flex items-center justify-center px-5 py-2.5 text-sm font-medium rounded-lg cursor-pointer shadow-sm transition-all",
                  "text-white hover:shadow-md",
                  uploading && "opacity-50 cursor-not-allowed"
                )}
                style={{ backgroundColor: personaConfig.primaryColor }}
              >
                {uploading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4 mr-2" />
                    New Application
                  </>
                )}
                <input
                  type="file"
                  className="hidden"
                  multiple
                  accept={getAcceptedFileTypes()}
                  onChange={handleFileInput}
                  disabled={uploading}
                />
              </label>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-500">Total Cases</span>
                <FileText className="w-4 h-4 text-slate-400" />
              </div>
              <p className="text-2xl font-bold text-slate-900 mt-1">{stats.total}</p>
            </div>
            <div className="bg-emerald-50 rounded-xl p-4 border border-emerald-100">
              <div className="flex items-center justify-between">
                <span className="text-sm text-emerald-600">Completed</span>
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              </div>
              <p className="text-2xl font-bold text-emerald-700 mt-1">{stats.completed}</p>
            </div>
            <div className="bg-sky-50 rounded-xl p-4 border border-sky-100">
              <div className="flex items-center justify-between">
                <span className="text-sm text-sky-600">In Progress</span>
                <Activity className="w-4 h-4 text-sky-500" />
              </div>
              <p className="text-2xl font-bold text-sky-700 mt-1">{stats.processing}</p>
            </div>
            <div className="bg-violet-50 rounded-xl p-4 border border-violet-100">
              <div className="flex items-center justify-between">
                <span className="text-sm text-violet-600">Today</span>
                <TrendingUp className="w-4 h-4 text-violet-500" />
              </div>
              <p className="text-2xl font-bold text-violet-700 mt-1">{stats.todayCount}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Priority Queues */}
      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Ready for Review */}
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-100 bg-gradient-to-r from-emerald-50 to-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900">Ready for Review</h3>
                    <p className="text-xs text-slate-500">Analysis complete — awaiting your decision</p>
                  </div>
                </div>
                <span className="text-2xl font-bold text-emerald-600">{queues.readyForReview.length}</span>
              </div>
            </div>
            <div className="divide-y divide-slate-100">
              {queues.readyForReview.length === 0 ? (
                <div className="px-5 py-8 text-center text-slate-400">
                  <CheckCircle2 className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No cases waiting for review</p>
                </div>
              ) : (
                queues.readyForReview.map((app) => (
                  <button
                    key={app.id}
                    onClick={() => onSelectApp(app.id)}
                    className="w-full px-5 py-3 flex items-center justify-between hover:bg-slate-50 transition-colors text-left group"
                  >
                    <div className="flex items-center gap-3">
                      <div 
                        className="w-8 h-8 rounded-lg flex items-center justify-center"
                        style={{ backgroundColor: `${personaConfig.primaryColor}10` }}
                      >
                        <FileText className="w-4 h-4" style={{ color: personaConfig.primaryColor }} />
                      </div>
                      <div>
                        <p className="font-medium text-slate-900 group-hover:text-indigo-600 transition-colors">
                          {getAppDisplayTitle(app)}
                        </p>
                        <p className="text-xs text-slate-400">
                          {new Date(app.created_at).toLocaleDateString()} at {new Date(app.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </div>
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-indigo-500 group-hover:translate-x-0.5 transition-all" />
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Needs AI Analysis */}
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-100 bg-gradient-to-r from-sky-50 to-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-sky-100 flex items-center justify-center">
                    <Activity className="w-4 h-4 text-sky-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900">Agents at Work</h3>
                    <p className="text-xs text-slate-500">AI agents extracting & analyzing</p>
                  </div>
                </div>
                <span className="text-2xl font-bold text-sky-600">{queues.needsAnalysis.length}</span>
              </div>
            </div>
            <div className="divide-y divide-slate-100">
              {queues.needsAnalysis.length === 0 ? (
                <div className="px-5 py-8 text-center text-slate-400">
                  <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">All agents idle</p>
                </div>
              ) : (
                queues.needsAnalysis.slice(0, 5).map((app) => (
                  <button
                    key={app.id}
                    onClick={() => onSelectApp(app.id)}
                    className="w-full px-5 py-3 flex items-center justify-between hover:bg-slate-50 transition-colors text-left group"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-sky-50 flex items-center justify-center">
                        <Loader2 className="w-4 h-4 text-sky-500 animate-spin" />
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">
                          {getAppDisplayTitle(app)}
                        </p>
                        <p className="text-xs text-slate-400 flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse" />
                          {app.processing_status || app.status}
                        </p>
                      </div>
                    </div>
                    <StatusBadge status={app.status} processingStatus={app.processing_status} />
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
        
        {/* Errors Alert */}
        {queues.hasErrors.length > 0 && (
          <div className="mt-4 bg-rose-50 border border-rose-200 rounded-xl p-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-rose-600 flex-shrink-0" />
              <div className="flex-1">
                <p className="font-medium text-rose-800">
                  {queues.hasErrors.length} case{queues.hasErrors.length > 1 ? 's' : ''} require{queues.hasErrors.length === 1 ? 's' : ''} attention
                </p>
                <p className="text-sm text-rose-600 mt-0.5">Processing errors occurred. Click to review and retry.</p>
              </div>
              <button 
                onClick={() => onSelectApp(queues.hasErrors[0].id)}
                className="px-3 py-1.5 bg-rose-600 text-white text-sm font-medium rounded-lg hover:bg-rose-700 transition-colors"
              >
                Review
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Upload Drop Zone */}
      <div className="max-w-7xl mx-auto px-6 lg:px-8 pb-6">
        <div 
          className={clsx(
            "rounded-xl border-2 border-dashed p-6 text-center transition-all relative overflow-hidden",
            dragActive 
              ? "border-indigo-400 bg-indigo-50" 
              : "border-slate-200 bg-white hover:border-slate-300"
          )}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          {dragActive ? (
            <div className="py-8">
              <Upload className="w-10 h-10 text-indigo-500 mx-auto mb-3" />
              <p className="text-lg font-medium text-indigo-600">Drop files to create new application</p>
            </div>
          ) : (
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center gap-4">
                <Upload className="w-5 h-5 text-slate-400" />
                <span className="text-slate-500">
                  Drag and drop {isAutomotiveClaims ? 'images, videos, or PDFs' : 'PDF documents'} here to start a new case
                </span>
                <span className="text-xs text-slate-400 border-l border-slate-200 pl-4">
                  {getAcceptedFileTypes().replaceAll('.', '').toUpperCase().split(',').join(', ')}
                </span>
              </div>
              
              {/* Condense Toggle */}
              {isUnderwritingPersona && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setLargeDocumentMode(!largeDocumentMode);
                  }}
                  className={clsx(
                    "flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all border",
                    largeDocumentMode 
                      ? "bg-indigo-50 border-indigo-200 text-indigo-700" 
                      : "bg-white border-slate-200 text-slate-400 hover:border-slate-300 hover:text-slate-600"
                  )}
                  title="Enable for large documents (50+ pages)"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                  Condense
                  <span className={clsx(
                    "w-2 h-2 rounded-full transition-colors",
                    largeDocumentMode ? "bg-indigo-500" : "bg-slate-300"
                  )} />
                </button>
              )}
            </div>
          )}
        </div>
        
        {error && (
          <div className="mt-4 p-4 bg-rose-50 text-rose-700 rounded-lg flex items-center gap-2">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Applications Table */}
      <div className="max-w-7xl mx-auto px-6 lg:px-8 pb-12">
        {/* Table Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-4">
          <h2 className="text-lg font-semibold text-slate-900">
            Recent Cases
            <span className="ml-2 text-sm font-normal text-slate-500">({filteredApps.length})</span>
          </h2>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <div className="relative flex-1 sm:flex-initial">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input 
                type="text"
                placeholder="Search cases..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm w-full sm:w-64 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
              />
            </div>
            
            <div className="bg-white border border-slate-200 rounded-lg p-1 flex">
              <button 
                onClick={() => setViewMode('grid')}
                className={clsx("p-1.5 rounded transition-colors", viewMode === 'grid' ? "bg-slate-100 text-slate-900" : "text-slate-400 hover:text-slate-600")}
              >
                <LayoutGrid className="w-4 h-4" />
              </button>
              <button 
                onClick={() => setViewMode('list')}
                className={clsx("p-1.5 rounded transition-colors", viewMode === 'list' ? "bg-slate-100 text-slate-900" : "text-slate-400 hover:text-slate-600")}
              >
                <ListIcon className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex justify-center py-20 bg-white rounded-xl border border-slate-200">
            <Loader2 className="w-8 h-8 text-slate-400 animate-spin" />
          </div>
        ) : filteredApps.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-xl border border-slate-200 border-dashed">
            <FileText className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-lg font-medium text-slate-900">No cases found</h3>
            <p className="text-slate-500 mt-1">Upload documents above to create your first case.</p>
          </div>
        ) : viewMode === 'list' ? (
          /* Table View */
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3 font-medium text-slate-600">Case</th>
                  <th className="px-6 py-3 font-medium text-slate-600">Status</th>
                  <th className="px-6 py-3 font-medium text-slate-600">Created</th>
                  <th className="px-6 py-3 font-medium text-slate-600">Reference</th>
                  <th className="px-6 py-3 font-medium text-slate-600 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredApps.map((app) => (
                  <tr 
                    key={app.id}
                    onClick={() => onSelectApp(app.id)}
                    className="hover:bg-slate-50 cursor-pointer transition-colors group"
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div 
                          className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                          style={{ backgroundColor: `${personaConfig.primaryColor}10` }}
                        >
                          <FileText className="w-4 h-4" style={{ color: personaConfig.primaryColor }} />
                        </div>
                        <div>
                          <div className="font-medium text-slate-900 group-hover:text-indigo-600 transition-colors">
                            {getAppDisplayTitle(app)}
                          </div>
                          <div className="text-xs text-slate-400 font-mono flex items-center gap-1">
                            <Hash className="w-3 h-3" />
                            {app.id.substring(0, 8)}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={app.status} processingStatus={app.processing_status} />
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-1.5 text-slate-500">
                        <Calendar className="w-3.5 h-3.5" />
                        <span>{new Date(app.created_at).toLocaleDateString()}</span>
                      </div>
                      <div className="text-xs text-slate-400 mt-0.5">
                        {new Date(app.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-500 max-w-xs">
                      {app.external_reference ? (
                        <span className="font-mono text-xs bg-slate-100 px-2 py-1 rounded">
                          {app.external_reference}
                        </span>
                      ) : (
                        <span className="text-slate-300">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <span 
                        className="inline-flex items-center gap-1 text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity"
                        style={{ color: personaConfig.primaryColor }}
                      >
                        Open
                        <ChevronRight className="w-4 h-4" />
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          /* Grid View */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredApps.map((app) => (
              <button
                key={app.id}
                onClick={() => onSelectApp(app.id)}
                className="bg-white rounded-xl border border-slate-200 p-5 text-left hover:border-slate-300 hover:shadow-md transition-all group flex flex-col"
              >
                <div className="flex justify-between items-start mb-3 w-full">
                  <div 
                    className="w-10 h-10 rounded-lg flex items-center justify-center"
                    style={{ backgroundColor: `${personaConfig.primaryColor}10` }}
                  >
                    <FileText className="w-5 h-5" style={{ color: personaConfig.primaryColor }} />
                  </div>
                  <StatusBadge status={app.status} processingStatus={app.processing_status} />
                </div>
                
                <h3 className="font-semibold text-slate-900 mb-1 line-clamp-1 group-hover:text-indigo-600 transition-colors">
                  {getAppDisplayTitle(app)}
                </h3>
                <div className="text-xs text-slate-400 font-mono flex items-center gap-1 mb-3">
                  <Hash className="w-3 h-3" />
                  {app.id.substring(0, 8)}
                  {app.external_reference && (
                    <>
                      <span className="mx-1">•</span>
                      <span className="truncate">{app.external_reference}</span>
                    </>
                  )}
                </div>
                
                <div className="mt-auto pt-3 border-t border-slate-100 flex justify-between items-center text-sm text-slate-500 w-full">
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>{new Date(app.created_at).toLocaleDateString()}</span>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-300 group-hover:translate-x-0.5 group-hover:text-indigo-500 transition-all" />
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
