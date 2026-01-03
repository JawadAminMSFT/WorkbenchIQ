'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import Link from 'next/link';
import {
  createApplication,
  listApplications,
  getApplication,
  startProcessing,
  runContentUnderstanding,
  runUnderwritingAnalysis,
  getPrompts,
  updatePrompt,
  createPrompt,
  deletePrompt,
  getAnalyzerStatus,
  getAnalyzerSchema,
  listAnalyzers,
  createAnalyzer,
  deleteAnalyzer,
  getPolicies,
  createPolicy as createPolicyApi,
  updatePolicy as updatePolicyApi,
  deletePolicy as deletePolicyApi,
} from '@/lib/api';
import type { ApplicationListItem, PromptsData, AnalyzerStatus, AnalyzerInfo, FieldSchema, UnderwritingPolicy, PolicyCriteriaItem } from '@/lib/types';
import PersonaSelector from '@/components/PersonaSelector';
import { usePersona } from '@/lib/PersonaContext';

type ProcessingStep = 'idle' | 'uploading' | 'extracting' | 'analyzing' | 'complete' | 'error';
type AdminTab = 'documents' | 'prompts' | 'policies' | 'analyzer';

interface ProcessingState {
  step: ProcessingStep;
  message: string;
  appId?: string;
}

export default function AdminPage() {
  // Persona context
  const { currentPersona, personaConfig } = usePersona();

  // Tab state
  const [activeTab, setActiveTab] = useState<AdminTab>('documents');

  // Document processing state
  const [applications, setApplications] = useState<ApplicationListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processing, setProcessing] = useState<ProcessingState>({ step: 'idle', message: '' });
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [externalRef, setExternalRef] = useState('');
  const [dragActive, setDragActive] = useState(false);
  
  // Track which app is being polled to avoid duplicate polling
  const pollingAppIdRef = useRef<string | null>(null);

  // Prompts state
  const [promptsData, setPromptsData] = useState<PromptsData | null>(null);
  const [selectedSection, setSelectedSection] = useState<string>('');
  const [selectedSubsection, setSelectedSubsection] = useState<string>('');
  const [promptText, setPromptText] = useState<string>('');
  const [promptsLoading, setPromptsLoading] = useState(false);
  const [promptsSaving, setPromptsSaving] = useState(false);
  const [promptsError, setPromptsError] = useState<string | null>(null);
  const [promptsSuccess, setPromptsSuccess] = useState<string | null>(null);

  // New prompt form state
  const [showNewPromptForm, setShowNewPromptForm] = useState(false);
  const [newSection, setNewSection] = useState('');
  const [newSubsection, setNewSubsection] = useState('');
  const [newPromptText, setNewPromptText] = useState('');

  // Analyzer state
  const [analyzerStatus, setAnalyzerStatus] = useState<AnalyzerStatus | null>(null);
  const [analyzerSchema, setAnalyzerSchema] = useState<FieldSchema | null>(null);
  const [analyzers, setAnalyzers] = useState<AnalyzerInfo[]>([]);
  const [analyzerLoading, setAnalyzerLoading] = useState(false);
  const [analyzerProcessing, setAnalyzerProcessing] = useState(false);
  const [analyzerError, setAnalyzerError] = useState<string | null>(null);
  const [analyzerSuccess, setAnalyzerSuccess] = useState<string | null>(null);

  // Policies state
  const [policies, setPolicies] = useState<UnderwritingPolicy[]>([]);
  const [policiesLoading, setPoliciesLoading] = useState(false);
  const [policiesSaving, setPoliciesSaving] = useState(false);
  const [policiesError, setPoliciesError] = useState<string | null>(null);
  const [policiesSuccess, setPoliciesSuccess] = useState<string | null>(null);
  const [selectedPolicy, setSelectedPolicy] = useState<UnderwritingPolicy | null>(null);
  const [showNewPolicyForm, setShowNewPolicyForm] = useState(false);
  const [policyFormData, setPolicyFormData] = useState({
    id: '',
    category: '',
    subcategory: '',
    name: '',
    description: '',
    criteria: [] as PolicyCriteriaItem[],
    references: [] as string[],
  });
  
  // Claims policy form state (different structure)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [claimsPolicyFormData, setClaimsPolicyFormData] = useState<Record<string, any>>({});
  
  // Helper to check if current persona is claims-related
  const isClaimsPersona = currentPersona.includes('claims');

  // Load applications
  const loadApplications = useCallback(async () => {
    try {
      const apps = await listApplications(currentPersona);
      setApplications(apps);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load applications');
    } finally {
      setLoading(false);
    }
  }, [currentPersona]);

  // Poll for processing completion - reusable function
  const pollForProcessingCompletion = useCallback((appId: string) => {
    // Avoid duplicate polling for the same app
    if (pollingAppIdRef.current === appId) {
      return;
    }
    pollingAppIdRef.current = appId;
    
    const pollInterval = 2000;
    const maxPolls = 300;
    let pollCount = 0;
    
    const poll = async () => {
      // Check if we should stop polling (component unmounted or different app started)
      if (pollingAppIdRef.current !== appId) {
        return;
      }
      
      pollCount++;
      if (pollCount > maxPolls) {
        setProcessing({
          step: 'error',
          message: 'Processing timed out.',
          appId,
        });
        pollingAppIdRef.current = null;
        return;
      }
      
      try {
        const status = await getApplication(appId);
        
        if (status.processing_status === 'extracting') {
          setProcessing({
            step: 'extracting',
            message: 'Running document extraction...',
            appId,
          });
          setTimeout(poll, pollInterval);
        } else if (status.processing_status === 'analyzing') {
          setProcessing({
            step: 'analyzing',
            message: 'Running analysis...',
            appId,
          });
          setTimeout(poll, pollInterval);
        } else if (status.processing_status === 'error') {
          setProcessing({
            step: 'error',
            message: status.processing_error || 'Processing failed',
            appId,
          });
          pollingAppIdRef.current = null;
          await loadApplications();
        } else if (!status.processing_status) {
          // Complete
          setProcessing({ step: 'complete', message: 'Processing complete!', appId });
          pollingAppIdRef.current = null;
          await loadApplications();
          setTimeout(() => {
            setProcessing({ step: 'idle', message: '' });
          }, 3000);
        }
      } catch (err) {
        console.warn('Polling error, retrying...', err);
        setTimeout(poll, pollInterval);
      }
    };
    
    // Set initial status and start polling
    setProcessing({
      step: 'extracting',
      message: 'Resuming progress tracking...',
      appId,
    });
    setTimeout(poll, pollInterval);
  }, [loadApplications]);

  // Load prompts
  const loadPrompts = useCallback(async (resetSelection: boolean = false) => {
    setPromptsLoading(true);
    setPromptsError(null);
    try {
      const data = await getPrompts(currentPersona);
      setPromptsData(data);
      
      // Auto-select first section/subsection when resetting or on initial load
      if (resetSelection && data.prompts) {
        const sections = Object.keys(data.prompts);
        if (sections.length > 0) {
          const firstSection = sections[0];
          setSelectedSection(firstSection);
          const subsections = Object.keys(data.prompts[firstSection]);
          if (subsections.length > 0) {
            setSelectedSubsection(subsections[0]);
            setPromptText(data.prompts[firstSection][subsections[0]]);
          }
        } else {
          setSelectedSection('');
          setSelectedSubsection('');
          setPromptText('');
        }
      }
    } catch (err) {
      setPromptsError(err instanceof Error ? err.message : 'Failed to load prompts');
    } finally {
      setPromptsLoading(false);
    }
  }, [currentPersona]);

  // Load analyzer data
  const loadAnalyzerData = useCallback(async () => {
    setAnalyzerLoading(true);
    setAnalyzerError(null);
    try {
      const [status, schema, list] = await Promise.all([
        getAnalyzerStatus(currentPersona),
        getAnalyzerSchema(currentPersona),
        listAnalyzers(),
      ]);
      setAnalyzerStatus(status);
      setAnalyzerSchema(schema);
      setAnalyzers(list.analyzers);
    } catch (err) {
      setAnalyzerError(err instanceof Error ? err.message : 'Failed to load analyzer data');
    } finally {
      setAnalyzerLoading(false);
    }
  }, [currentPersona]);

  // Load policies for the current persona
  const loadPolicies = useCallback(async () => {
    setPoliciesLoading(true);
    setPoliciesError(null);
    try {
      const data = await getPolicies(currentPersona);
      setPolicies(data.policies);
    } catch (err) {
      setPoliciesError(err instanceof Error ? err.message : 'Failed to load policies');
    } finally {
      setPoliciesLoading(false);
    }
  }, [currentPersona]);

  useEffect(() => {
    loadApplications();
  }, [loadApplications]);

  // Load prompts when tab becomes active (initial load)
  useEffect(() => {
    if (activeTab === 'prompts' && !promptsData && !promptsLoading) {
      loadPrompts(true);
    }
  }, [activeTab, promptsData, promptsLoading, loadPrompts]);

  // Load policies when tab becomes active
  useEffect(() => {
    if (activeTab === 'policies' && policies.length === 0 && !policiesLoading) {
      loadPolicies();
    }
  }, [activeTab, policies.length, policiesLoading, loadPolicies]);

  // Reload prompts when persona changes
  useEffect(() => {
    if (activeTab === 'prompts') {
      setPromptsData(null); // Clear data to trigger reload
    }
  }, [currentPersona]);

  // Reload policies when persona changes
  useEffect(() => {
    if (activeTab === 'policies') {
      setPolicies([]); // Clear policies to trigger reload
    }
  }, [currentPersona]);

  // Reload analyzer data when persona changes
  useEffect(() => {
    if (activeTab === 'analyzer') {
      setAnalyzerSchema(null); // Clear schema to trigger reload
    }
  }, [currentPersona]);

  // Load analyzer data when tab becomes active or schema is cleared
  useEffect(() => {
    if (activeTab === 'analyzer' && (!analyzerSchema || !analyzerStatus)) {
      loadAnalyzerData();
    }
  }, [activeTab, analyzerSchema, analyzerStatus, loadAnalyzerData]);

  // Update prompt text when selection changes
  useEffect(() => {
    if (promptsData && selectedSection && selectedSubsection) {
      const text = promptsData.prompts[selectedSection]?.[selectedSubsection] || '';
      setPromptText(text);
    }
  }, [promptsData, selectedSection, selectedSubsection]);

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

    const files = Array.from(e.dataTransfer.files).filter(
      (f) => f.type === 'application/pdf'
    );
    if (files.length > 0) {
      setSelectedFiles((prev) => [...prev, ...files]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files).filter(
        (f) => f.type === 'application/pdf'
      );
      setSelectedFiles((prev) => [...prev, ...files]);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUploadAndProcess = async () => {
    if (selectedFiles.length === 0) return;

    try {
      // Step 1: Upload files
      setProcessing({ step: 'uploading', message: 'Uploading files...' });
      const app = await createApplication(
        selectedFiles,
        externalRef || undefined,
        currentPersona
      );
      
      // Reset form
      setSelectedFiles([]);
      setExternalRef('');
      
      // Step 2: Start background processing (extraction + analysis)
      await startProcessing(app.id);
      
      // Step 3: Start polling for completion
      pollForProcessingCompletion(app.id);
      
    } catch (err) {
      setProcessing({
        step: 'error',
        message: err instanceof Error ? err.message : 'Processing failed',
      });
    }
  };

  const handleReprocess = async (appId: string, step: 'extract' | 'analyze' | 'prompts-only', sections?: string[]) => {
    try {
      // Start processing in background mode
      if (step === 'extract') {
        // Full reprocess: extraction + analysis
        setProcessing({
          step: 'extracting',
          message: 'Starting full reprocessing...',
          appId,
        });
        await startProcessing(appId); // This does both extract + analyze
      } else if (step === 'prompts-only') {
        setProcessing({
          step: 'analyzing',
          message: sections?.length ? `Re-running prompts for: ${sections.join(', ')}...` : 'Re-running all prompts...',
          appId,
        });
        await runUnderwritingAnalysis(appId, sections, true); // background=true
      } else {
        setProcessing({
          step: 'analyzing',
          message: 'Starting analysis...',
          appId,
        });
        await runUnderwritingAnalysis(appId, undefined, true); // background=true
      }
      
      // Start polling for completion
      pollForProcessingCompletion(appId);
      
    } catch (err) {
      setProcessing({
        step: 'error',
        message: err instanceof Error ? err.message : 'Reprocessing failed',
      });
    }
  };

  // Prompt handlers
  const handleSavePrompt = async () => {
    if (!selectedSection || !selectedSubsection) return;
    
    setPromptsSaving(true);
    setPromptsError(null);
    setPromptsSuccess(null);
    
    try {
      await updatePrompt(selectedSection, selectedSubsection, promptText, currentPersona);
      setPromptsSuccess('Prompt saved successfully!');
      await loadPrompts(false);
      
      setTimeout(() => setPromptsSuccess(null), 3000);
    } catch (err) {
      setPromptsError(err instanceof Error ? err.message : 'Failed to save prompt');
    } finally {
      setPromptsSaving(false);
    }
  };

  const handleDeletePrompt = async () => {
    if (!selectedSection || !selectedSubsection) return;
    if (!confirm(`Are you sure you want to reset the prompt "${selectedSection}/${selectedSubsection}" to default?`)) return;
    
    setPromptsSaving(true);
    setPromptsError(null);
    
    try {
      await deletePrompt(selectedSection, selectedSubsection, currentPersona);
      setPromptsSuccess('Prompt reset to default');
      await loadPrompts(true);
      
      setTimeout(() => setPromptsSuccess(null), 3000);
    } catch (err) {
      setPromptsError(err instanceof Error ? err.message : 'Failed to reset prompt');
    } finally {
      setPromptsSaving(false);
    }
  };

  const handleCreatePrompt = async () => {
    if (!newSection || !newSubsection || !newPromptText) {
      setPromptsError('Please fill in all fields');
      return;
    }
    
    setPromptsSaving(true);
    setPromptsError(null);
    
    try {
      await createPrompt(newSection, newSubsection, newPromptText, currentPersona);
      setPromptsSuccess('New prompt created!');
      setShowNewPromptForm(false);
      setNewSection('');
      setNewSubsection('');
      setNewPromptText('');
      await loadPrompts(true);
      
      setTimeout(() => setPromptsSuccess(null), 3000);
    } catch (err) {
      setPromptsError(err instanceof Error ? err.message : 'Failed to create prompt');
    } finally {
      setPromptsSaving(false);
    }
  };

  // Analyzer handlers
  const handleCreateAnalyzer = async () => {
    setAnalyzerProcessing(true);
    setAnalyzerError(null);
    setAnalyzerSuccess(null);
    
    try {
      // Pass current persona to use persona-specific field schema
      const result = await createAnalyzer(undefined, currentPersona);
      setAnalyzerSuccess(`Analyzer "${result.analyzer_id}" created successfully!`);
      await loadAnalyzerData();
      
      setTimeout(() => setAnalyzerSuccess(null), 5000);
    } catch (err) {
      setAnalyzerError(err instanceof Error ? err.message : 'Failed to create analyzer');
    } finally {
      setAnalyzerProcessing(false);
    }
  };

  const handleDeleteAnalyzer = async (analyzerId: string) => {
    if (!confirm(`Are you sure you want to delete the analyzer "${analyzerId}"?`)) return;
    
    setAnalyzerProcessing(true);
    setAnalyzerError(null);
    
    try {
      await deleteAnalyzer(analyzerId);
      setAnalyzerSuccess('Analyzer deleted successfully');
      await loadAnalyzerData();
      
      setTimeout(() => setAnalyzerSuccess(null), 3000);
    } catch (err) {
      setAnalyzerError(err instanceof Error ? err.message : 'Failed to delete analyzer');
    } finally {
      setAnalyzerProcessing(false);
    }
  };

  // Policy handlers
  const handleSelectPolicy = (policy: UnderwritingPolicy) => {
    setSelectedPolicy(policy);
    if (isClaimsPersona) {
      // Claims policies have different structure - store the raw policy data
      setClaimsPolicyFormData({ ...policy });
    } else {
      // Underwriting policies
      setPolicyFormData({
        id: policy.id,
        category: policy.category,
        subcategory: policy.subcategory,
        name: policy.name,
        description: policy.description,
        criteria: policy.criteria || [],
        references: policy.references || [],
      });
    }
    setShowNewPolicyForm(false);
  };

  const handleNewPolicyClick = () => {
    setSelectedPolicy(null);
    if (isClaimsPersona) {
      setClaimsPolicyFormData({
        id: '',
        plan_name: '',
        plan_type: 'HMO',
        network: '',
        deductible: { individual: '', family: '' },
        oop_max: { individual: '', family: '' },
        copays: { pcp_visit: '', specialist_visit: '', urgent_care: '', er_visit: '' },
        coinsurance: '',
        preventive_care: 'Covered 100%',
        exclusions: [],
      });
    } else {
      setPolicyFormData({
        id: '',
        category: '',
        subcategory: '',
        name: '',
        description: '',
        criteria: [],
        references: [],
      });
    }
    setShowNewPolicyForm(true);
  };

  const handleSavePolicy = async () => {
    setPoliciesSaving(true);
    setPoliciesError(null);
    setPoliciesSuccess(null);

    try {
      if (showNewPolicyForm) {
        // Create new policy
        await createPolicyApi(policyFormData);
        setPoliciesSuccess('Policy created successfully!');
        setShowNewPolicyForm(false);
      } else if (selectedPolicy) {
        // Update existing policy
        const { id, ...updateData } = policyFormData;
        await updatePolicyApi(selectedPolicy.id, updateData);
        setPoliciesSuccess('Policy updated successfully!');
      }
      await loadPolicies();
      setTimeout(() => setPoliciesSuccess(null), 3000);
    } catch (err) {
      setPoliciesError(err instanceof Error ? err.message : 'Failed to save policy');
    } finally {
      setPoliciesSaving(false);
    }
  };

  const handleDeletePolicy = async () => {
    if (!selectedPolicy) return;
    if (!confirm(`Are you sure you want to delete the policy "${selectedPolicy.name}"?`)) return;

    setPoliciesSaving(true);
    setPoliciesError(null);

    try {
      await deletePolicyApi(selectedPolicy.id);
      setPoliciesSuccess('Policy deleted successfully');
      setSelectedPolicy(null);
      await loadPolicies();
      setTimeout(() => setPoliciesSuccess(null), 3000);
    } catch (err) {
      setPoliciesError(err instanceof Error ? err.message : 'Failed to delete policy');
    } finally {
      setPoliciesSaving(false);
    }
  };

  const handleAddCriteria = () => {
    setPolicyFormData(prev => ({
      ...prev,
      criteria: [
        ...prev.criteria,
        { id: `${prev.id}-${prev.criteria.length + 1}`, condition: '', risk_level: 'Low', action: '', rationale: '' }
      ]
    }));
  };

  const handleRemoveCriteria = (index: number) => {
    setPolicyFormData(prev => ({
      ...prev,
      criteria: prev.criteria.filter((_, i) => i !== index)
    }));
  };

  const handleCriteriaChange = (index: number, field: keyof PolicyCriteriaItem, value: string) => {
    setPolicyFormData(prev => ({
      ...prev,
      criteria: prev.criteria.map((c, i) => i === index ? { ...c, [field]: value } : c)
    }));
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      pending: 'bg-amber-100 text-amber-800',
      extracted: 'bg-sky-100 text-sky-800',
      completed: 'bg-emerald-100 text-emerald-800',
      error: 'bg-rose-100 text-rose-800',
    };
    return styles[status] || 'bg-slate-100 text-slate-800';
  };

  const isProcessing = ['uploading', 'extracting', 'analyzing'].includes(processing.step);

  // Reanalyze menu state
  const [reanalyzeMenuOpen, setReanalyzeMenuOpen] = useState<string | null>(null);

  // Render Documents Tab content
  const renderDocumentsTab = () => (
    <>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Upload Section */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-slate-900">Upload New Application</h2>
          </div>

          {/* Processing Status - Moved to top of upload panel */}
          {processing.step !== 'idle' && (
            <div
              className={`mb-4 p-4 rounded-lg ${
                processing.step === 'error'
                  ? 'bg-rose-50 border border-rose-200'
                  : processing.step === 'complete'
                  ? 'bg-emerald-50 border border-emerald-200'
                  : 'bg-indigo-50 border border-indigo-200'
              }`}
            >
              {/* Progress Steps */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-4">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    processing.step === 'uploading' ? 'bg-indigo-500 text-white' :
                    processing.step === 'error' ? 'bg-rose-500 text-white' :
                    'bg-emerald-500 text-white'
                  }`}>1</div>
                  <div className={`w-12 h-1 rounded ${
                    ['extracting', 'analyzing', 'complete'].includes(processing.step) ? 'bg-emerald-500' : 'bg-slate-200'
                  }`}></div>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    processing.step === 'extracting' ? 'bg-indigo-500 text-white' :
                    ['analyzing', 'complete'].includes(processing.step) ? 'bg-emerald-500 text-white' :
                    'bg-slate-200 text-slate-500'
                  }`}>2</div>
                  <div className={`w-12 h-1 rounded ${
                    ['analyzing', 'complete'].includes(processing.step) ? 'bg-emerald-500' : 'bg-slate-200'
                  }`}></div>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    processing.step === 'analyzing' ? 'bg-indigo-500 text-white' :
                    processing.step === 'complete' ? 'bg-emerald-500 text-white' :
                    'bg-slate-200 text-slate-500'
                  }`}>3</div>
                  <div className={`w-12 h-1 rounded ${
                    processing.step === 'complete' ? 'bg-emerald-500' : 'bg-slate-200'
                  }`}></div>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    processing.step === 'complete' ? 'bg-emerald-500 text-white' : 'bg-slate-200 text-slate-500'
                  }`}>✓</div>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                {isProcessing && (
                  <svg className="animate-spin h-5 w-5 text-indigo-600" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                )}
                <span className={`font-medium ${
                  processing.step === 'error' ? 'text-rose-700' :
                  processing.step === 'complete' ? 'text-emerald-700' :
                  'text-indigo-700'
                }`}>{processing.message}</span>
              </div>
              
              {processing.appId && processing.step === 'complete' && (
                <Link
                  href={`/?id=${processing.appId}`}
                  className="mt-2 inline-block text-sm text-emerald-700 underline hover:text-emerald-800"
                >
                  View Application →
                </Link>
              )}
              
              {processing.step === 'error' && (
                <button
                  onClick={() => setProcessing({ step: 'idle', message: '' })}
                  className="mt-2 text-sm text-rose-600 hover:text-rose-800 underline"
                >
                  Dismiss
                </button>
              )}
            </div>
          )}

          {/* File Drop Zone */}
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive
                ? 'border-indigo-500 bg-indigo-50'
                : 'border-slate-300 hover:border-slate-400'
            } ${isProcessing ? 'opacity-50 pointer-events-none' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <div className="space-y-2">
              <svg
                className="mx-auto h-12 w-12 text-slate-400"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 48 48"
              >
                <path
                  d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <div className="text-slate-600">
                <label className="cursor-pointer text-indigo-600 hover:text-indigo-500">
                  <span>Upload PDF files</span>
                  <input
                    type="file"
                    className="sr-only"
                    accept=".pdf"
                    multiple
                    onChange={handleFileInput}
                    disabled={isProcessing}
                  />
                </label>
                <span> or drag and drop</span>
              </div>
              <p className="text-xs text-slate-500">PDF files only</p>
            </div>
          </div>

          {/* Selected Files */}
          {selectedFiles.length > 0 && (
            <div className="mt-4">
              <h3 className="text-sm font-medium text-slate-700 mb-2">
                Selected Files ({selectedFiles.length})
              </h3>
              <ul className="space-y-2">
                {selectedFiles.map((file, index) => (
                  <li
                    key={index}
                    className="flex items-center justify-between bg-slate-50 px-3 py-2 rounded-lg"
                  >
                    <span className="text-sm text-slate-700 truncate">
                      {file.name}
                    </span>
                    <button
                      onClick={() => removeFile(index)}
                      className="text-rose-500 hover:text-rose-700"
                      disabled={isProcessing}
                    >
                      ✕
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* External Reference */}
          <div className="mt-4">
            <label className="block text-sm font-medium text-slate-700 mb-1">
              External Reference (optional)
            </label>
            <input
              type="text"
              value={externalRef}
              onChange={(e) => setExternalRef(e.target.value)}
              placeholder="e.g., Policy number, Case ID"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              disabled={isProcessing}
            />
          </div>

          {/* Submit Button */}
          <button
            onClick={handleUploadAndProcess}
            disabled={selectedFiles.length === 0 || isProcessing}
            className={`mt-4 w-full py-3 rounded-lg font-medium transition-colors ${
              selectedFiles.length === 0 || isProcessing
                ? 'bg-slate-300 text-slate-500 cursor-not-allowed'
                : 'bg-indigo-600 text-white hover:bg-indigo-700'
            }`}
          >
            {isProcessing ? 'Processing...' : 'Upload & Process'}
          </button>
        </div>

        {/* Applications List */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-slate-900">Applications</h2>
            <button
              onClick={loadApplications}
              className="text-sm text-indigo-600 hover:text-indigo-700"
              disabled={loading}
            >
              Refresh
            </button>
          </div>

          {loading ? (
            <div className="text-center py-8 text-slate-500">
              Loading applications...
            </div>
          ) : error ? (
            <div className="text-center py-8 text-rose-500">{error}</div>
          ) : applications.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              No applications found. Upload documents to get started.
            </div>
          ) : (
            <ul className="divide-y divide-slate-200">
              {applications.map((app) => (
                <li key={app.id} className="py-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm font-medium text-slate-900">
                          {app.id}
                        </span>
                        {/* Processing status indicator */}
                        {app.processing_status ? (
                          <span className="px-2 py-0.5 text-xs rounded-full bg-amber-100 text-amber-700 flex items-center gap-1">
                            <span className="inline-block w-2 h-2 bg-amber-500 rounded-full animate-pulse"></span>
                            {app.processing_status === 'extracting' ? 'Extracting...' : 
                             app.processing_status === 'analyzing' ? 'Analyzing...' : 
                             app.processing_status}
                          </span>
                        ) : (
                          <span
                            className={`px-2 py-0.5 text-xs rounded-full ${getStatusBadge(
                              app.status
                            )}`}
                          >
                            {app.status}
                          </span>
                        )}
                      </div>
                      {app.external_reference && (
                        <p className="text-sm text-slate-500">
                          Ref: {app.external_reference}
                        </p>
                      )}
                      {app.created_at && (
                        <p className="text-xs text-slate-400">
                          Created:{' '}
                          {new Date(app.created_at).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {/* Resume tracking button for in-progress apps */}
                      {app.processing_status && (app.processing_status === 'extracting' || app.processing_status === 'analyzing') && (
                        <button
                          onClick={() => pollForProcessingCompletion(app.id)}
                          disabled={processing.appId === app.id}
                          className="text-xs px-2 py-1 bg-amber-100 text-amber-700 rounded-lg hover:bg-amber-200 disabled:opacity-50 transition-colors flex items-center gap-1"
                          title="Resume tracking progress"
                        >
                          {processing.appId === app.id ? (
                            <>
                              <span className="inline-block w-2 h-2 bg-amber-500 rounded-full animate-pulse"></span>
                              Tracking...
                            </>
                          ) : (
                            <>
                              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M8 5v14l11-7z"/>
                              </svg>
                              Resume
                            </>
                          )}
                        </button>
                      )}
                      {app.status === 'pending' && !app.processing_status && (
                        <button
                          onClick={() => handleReprocess(app.id, 'extract')}
                          disabled={isProcessing}
                          className="text-xs px-2 py-1 bg-sky-100 text-sky-700 rounded-lg hover:bg-sky-200 disabled:opacity-50 transition-colors"
                        >
                          Extract
                        </button>
                      )}
                      {app.status === 'extracted' && !app.processing_status && (
                        <button
                          onClick={() => handleReprocess(app.id, 'analyze')}
                          disabled={isProcessing}
                          className="text-xs px-2 py-1 bg-violet-100 text-violet-700 rounded-lg hover:bg-violet-200 disabled:opacity-50 transition-colors"
                        >
                          Analyze
                        </button>
                      )}
                      {app.status === 'completed' && (
                        <Link
                          href={`/?id=${app.id}`}
                          className="text-xs px-2 py-1 bg-emerald-100 text-emerald-700 rounded-lg hover:bg-emerald-200 transition-colors"
                        >
                          View
                        </Link>
                      )}
                      {/* Reanalyze Dropdown Menu */}
                      <div className="relative">
                        <button
                          onClick={() => setReanalyzeMenuOpen(reanalyzeMenuOpen === app.id ? null : app.id)}
                          disabled={isProcessing}
                          className="text-xs px-2 py-1 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 disabled:opacity-50 transition-colors flex items-center gap-1"
                          title="Reanalyze options"
                        >
                          ↻
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>
                        
                        {reanalyzeMenuOpen === app.id && (
                          <div className="absolute right-0 mt-1 w-56 bg-white rounded-lg shadow-lg border border-slate-200 z-10">
                            <div className="p-2">
                              <div className="text-xs font-semibold text-slate-500 uppercase px-2 py-1">Reanalyze Options</div>
                              <button
                                onClick={() => {
                                  setReanalyzeMenuOpen(null);
                                  handleReprocess(app.id, 'extract');
                                }}
                                className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md"
                              >
                                <div className="font-medium">Full Extraction</div>
                                <div className="text-xs text-slate-500">Re-run document extraction + all prompts</div>
                              </button>
                              <button
                                onClick={() => {
                                  setReanalyzeMenuOpen(null);
                                  handleReprocess(app.id, 'prompts-only');
                                }}
                                className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md"
                              >
                                <div className="font-medium">All Prompts Only</div>
                                <div className="text-xs text-slate-500">Re-run all underwriting prompts</div>
                              </button>
                              <div className="border-t border-slate-100 my-1"></div>
                              <div className="text-xs font-semibold text-slate-500 uppercase px-2 py-1">Specific Sections</div>
                              <button
                                onClick={() => {
                                  setReanalyzeMenuOpen(null);
                                  handleReprocess(app.id, 'prompts-only', ['application_summary']);
                                }}
                                className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md"
                              >
                                Application Summary
                              </button>
                              <button
                                onClick={() => {
                                  setReanalyzeMenuOpen(null);
                                  handleReprocess(app.id, 'prompts-only', ['medical_summary']);
                                }}
                                className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md"
                              >
                                Medical Summary
                              </button>
                              <button
                                onClick={() => {
                                  setReanalyzeMenuOpen(null);
                                  handleReprocess(app.id, 'prompts-only', ['risk_assessment']);
                                }}
                                className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 rounded-md"
                              >
                                Risk Assessment
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

    </>
  );

  // Render Prompts Tab content
  const renderPromptsTab = () => (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      {/* Prompt Selector */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h2 className="text-xl font-semibold mb-4 text-slate-900">Prompt Catalog</h2>
        
        {promptsLoading ? (
          <div className="text-center py-8 text-slate-500">Loading prompts...</div>
        ) : promptsData ? (
          <div className="space-y-4">
            {/* Section Selector */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Section
              </label>
              <select
                value={selectedSection}
                onChange={(e) => {
                  setSelectedSection(e.target.value);
                  const subsections = Object.keys(promptsData.prompts[e.target.value] || {});
                  if (subsections.length > 0) {
                    setSelectedSubsection(subsections[0]);
                  }
                }}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {Object.keys(promptsData.prompts).map((section) => (
                  <option key={section} value={section}>
                    {section.replace(/_/g, ' ')}
                  </option>
                ))}
              </select>
            </div>

            {/* Subsection Selector */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Subsection
              </label>
              <select
                value={selectedSubsection}
                onChange={(e) => setSelectedSubsection(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {selectedSection &&
                  Object.keys(promptsData.prompts[selectedSection] || {}).map(
                    (subsection) => (
                      <option key={subsection} value={subsection}>
                        {subsection.replace(/_/g, ' ')}
                      </option>
                    )
                  )}
              </select>
            </div>

            {/* Prompt List */}
            <div className="border-t pt-4 mt-4">
              <h3 className="text-sm font-medium text-slate-700 mb-2">All Prompts</h3>
              <div className="max-h-64 overflow-y-auto space-y-1">
                {Object.entries(promptsData.prompts).map(([section, subsections]) => (
                  <div key={section}>
                    <div className="text-xs font-semibold text-slate-500 uppercase mt-2">
                      {section.replace(/_/g, ' ')}
                    </div>
                    {Object.keys(subsections).map((subsection) => (
                      <button
                        key={`${section}-${subsection}`}
                        onClick={() => {
                          setSelectedSection(section);
                          setSelectedSubsection(subsection);
                        }}
                        className={`w-full text-left px-2 py-1 text-sm rounded ${
                          selectedSection === section && selectedSubsection === subsection
                            ? 'bg-indigo-100 text-indigo-700'
                            : 'hover:bg-slate-100 text-slate-700'
                        }`}
                      >
                        {subsection.replace(/_/g, ' ')}
                      </button>
                    ))}
                  </div>
                ))}
              </div>
            </div>

            {/* Add New Prompt Button */}
            <button
              onClick={() => setShowNewPromptForm(true)}
              className="w-full py-2 text-sm text-indigo-600 border border-indigo-300 rounded-lg hover:bg-indigo-50 transition-colors"
            >
              + Add New Prompt
            </button>
          </div>
        ) : null}
      </div>

      {/* Prompt Editor */}
      <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-slate-900">
            {selectedSection && selectedSubsection
              ? `${selectedSection.replace(/_/g, ' ')} / ${selectedSubsection.replace(/_/g, ' ')}`
              : 'Select a Prompt'}
          </h2>
          <div className="flex items-center gap-2">
            <button
              onClick={handleDeletePrompt}
              disabled={!selectedSection || !selectedSubsection || promptsSaving}
              className="px-3 py-1.5 text-sm text-rose-600 border border-rose-300 rounded-lg hover:bg-rose-50 disabled:opacity-50 transition-colors"
            >
              Reset to Default
            </button>
            <button
              onClick={handleSavePrompt}
              disabled={!selectedSection || !selectedSubsection || promptsSaving}
              className="px-4 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              {promptsSaving ? 'Saving...' : 'Save'}
            </button>
          </div>
        </div>

        {/* Status Messages */}
        {promptsError && (
          <div className="mb-4 p-3 bg-rose-50 text-rose-700 rounded-lg text-sm">
            {promptsError}
          </div>
        )}
        {promptsSuccess && (
          <div className="mb-4 p-3 bg-emerald-50 text-emerald-700 rounded-lg text-sm">
            {promptsSuccess}
          </div>
        )}

        {/* Prompt Text Editor */}
        <textarea
          value={promptText}
          onChange={(e) => setPromptText(e.target.value)}
          className="w-full h-96 px-4 py-3 border border-slate-300 rounded-lg font-mono text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
          placeholder="Select a prompt to edit..."
          disabled={!selectedSection || !selectedSubsection}
        />

        {/* Help Text */}
        <p className="mt-2 text-xs text-slate-500">
          Prompts should return valid JSON. Use markdown formatting for instructions.
        </p>
      </div>

      {/* New Prompt Modal */}
      {showNewPromptForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-lg mx-4">
            <h3 className="text-lg font-semibold mb-4">Create New Prompt</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Section
                </label>
                <input
                  type="text"
                  value={newSection}
                  onChange={(e) => setNewSection(e.target.value)}
                  placeholder="e.g., medical_summary"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Subsection
                </label>
                <input
                  type="text"
                  value={newSubsection}
                  onChange={(e) => setNewSubsection(e.target.value)}
                  placeholder="e.g., diabetes"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Prompt Text
                </label>
                <textarea
                  value={newPromptText}
                  onChange={(e) => setNewPromptText(e.target.value)}
                  placeholder="Enter your prompt text..."
                  className="w-full h-40 px-3 py-2 border border-slate-300 rounded-lg font-mono text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => {
                  setShowNewPromptForm(false);
                  setNewSection('');
                  setNewSubsection('');
                  setNewPromptText('');
                }}
                className="px-4 py-2 text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreatePrompt}
                disabled={promptsSaving}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
              >
                {promptsSaving ? 'Creating...' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  // Render Analyzer Tab content
  const renderAnalyzerTab = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Analyzer Status */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h2 className="text-xl font-semibold mb-4 text-slate-900">Content Understanding Analyzer</h2>

        {analyzerLoading ? (
          <div className="text-center py-8 text-slate-500">Loading analyzer status...</div>
        ) : analyzerError ? (
          <div className="p-4 bg-rose-50 text-rose-700 rounded-lg">{analyzerError}</div>
        ) : analyzerStatus ? (
          <div className="space-y-4">
            {/* Status Messages */}
            {analyzerSuccess && (
              <div className="p-3 bg-emerald-50 text-emerald-700 rounded-lg text-sm">
                {analyzerSuccess}
              </div>
            )}

            {/* Current Status */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-50 p-4 rounded-lg">
                <div className="text-xs text-slate-500 uppercase mb-1">Custom Analyzer</div>
                <div className="font-mono text-sm">{analyzerStatus.analyzer_id}</div>
                <span
                  className={`inline-block mt-2 px-2 py-0.5 text-xs rounded-full ${
                    analyzerStatus.exists
                      ? 'bg-emerald-100 text-emerald-700'
                      : 'bg-amber-100 text-amber-700'
                  }`}
                >
                  {analyzerStatus.exists ? 'Exists' : 'Not Created'}
                </span>
              </div>
              
              <div className="bg-slate-50 p-4 rounded-lg">
                <div className="text-xs text-slate-500 uppercase mb-1">Confidence Scoring</div>
                <div className="font-medium">
                  {analyzerStatus.confidence_scoring_enabled ? 'Enabled' : 'Disabled'}
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  Default: {analyzerStatus.default_analyzer_id}
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2 pt-4">
              <button
                onClick={handleCreateAnalyzer}
                disabled={analyzerProcessing}
                className="flex-1 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
              >
                {analyzerProcessing ? 'Processing...' : analyzerStatus.exists ? 'Update Analyzer' : 'Create Analyzer'}
              </button>
              
              {analyzerStatus.exists && (
                <button
                  onClick={() => handleDeleteAnalyzer(analyzerStatus.analyzer_id)}
                  disabled={analyzerProcessing}
                  className="px-4 py-2 text-rose-600 border border-rose-300 rounded-lg hover:bg-rose-50 disabled:opacity-50 transition-colors"
                >
                  Delete
                </button>
              )}
            </div>

            {/* Info Box */}
            <div className="bg-sky-50 border border-sky-200 rounded-lg p-4 mt-4">
              <h4 className="font-medium text-sky-900 mb-2">💡 About Custom Analyzers</h4>
              <p className="text-sm text-sky-800">
                The custom analyzer extracts structured fields from underwriting documents with confidence scores.
                This enables better validation and review of extracted data. After creating or updating the analyzer,
                re-run extraction on existing applications to get confidence scores.
              </p>
            </div>

            {/* Available Analyzers */}
            <div className="border-t pt-4 mt-4">
              <h3 className="font-medium text-slate-900 mb-3">Available Analyzers</h3>
              <ul className="space-y-2">
                {analyzers.map((analyzer) => (
                  <li
                    key={analyzer.id}
                    className="flex items-center justify-between p-3 bg-slate-50 rounded-lg"
                  >
                    <div>
                      <div className="font-mono text-sm">{analyzer.id}</div>
                      <div className="text-xs text-slate-500">
                        {analyzer.type === 'prebuilt' ? 'Azure Prebuilt' : 'Custom'} • {analyzer.description}
                      </div>
                    </div>
                    <span
                      className={`px-2 py-0.5 text-xs rounded-full ${
                        analyzer.exists
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-slate-200 text-slate-600'
                      }`}
                    >
                      {analyzer.exists ? 'Ready' : 'Not Created'}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ) : null}
      </div>

      {/* Field Schema */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-slate-900">Field Schema</h2>
          {analyzerSchema && (
            <span className="text-sm text-slate-500">
              {analyzerSchema.field_count} fields defined
            </span>
          )}
        </div>

        {analyzerSchema ? (
          <div className="space-y-4">
            {/* Field List */}
            <div className="max-h-[600px] overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-white">
                  <tr className="border-b">
                    <th className="text-left py-2 font-medium text-slate-700">Field Name</th>
                    <th className="text-left py-2 font-medium text-slate-700">Type</th>
                    <th className="text-left py-2 font-medium text-slate-700">Confidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {Object.entries(analyzerSchema.schema.fields).map(([fieldName, field]) => (
                    <tr key={fieldName} className="hover:bg-slate-50">
                      <td className="py-2">
                        <div className="font-mono text-xs">{fieldName}</div>
                        <div className="text-xs text-slate-500 truncate max-w-xs" title={field.description}>
                          {field.description}
                        </div>
                      </td>
                      <td className="py-2">
                        <span className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-xs">
                          {field.type}
                        </span>
                      </td>
                      <td className="py-2">
                        {field.estimateSourceAndConfidence ? (
                          <span className="text-emerald-600">✓</span>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Raw Schema Toggle */}
            <details className="border-t pt-4">
              <summary className="cursor-pointer text-sm text-indigo-600 hover:text-indigo-700">
                View Raw Schema JSON
              </summary>
              <pre className="mt-2 p-4 bg-slate-900 text-slate-100 rounded-lg overflow-x-auto text-xs max-h-64">
                {JSON.stringify(analyzerSchema.schema, null, 2)}
              </pre>
            </details>
          </div>
        ) : analyzerLoading ? (
          <div className="text-center py-8 text-slate-500">Loading schema...</div>
        ) : null}
      </div>
    </div>
  );

  // Render Policies Tab content
  const renderPoliciesTab = () => (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Policy List */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-slate-900">
            {isClaimsPersona ? 'Claims Policies' : 'Underwriting Policies'}
          </h2>
          <button
            onClick={handleNewPolicyClick}
            className="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            + New Policy
          </button>
        </div>

        {policiesLoading ? (
          <div className="text-center py-8 text-slate-500">Loading policies...</div>
        ) : policies.length === 0 ? (
          <div className="text-center py-8 text-slate-500">No policies found</div>
        ) : (
          <div className="space-y-2 max-h-[600px] overflow-y-auto">
            {policies.map((policy) => (
              <button
                key={policy.id}
                onClick={() => handleSelectPolicy(policy)}
                className={`w-full text-left p-3 rounded-lg border transition-colors ${
                  selectedPolicy?.id === policy.id
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-slate-200 hover:border-indigo-300 hover:bg-slate-50'
                }`}
              >
                <div className="font-medium text-slate-900 text-sm">{policy.name || policy.id}</div>
                {isClaimsPersona ? (
                  <div className="text-xs text-slate-500">
                    {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                    {(policy as any).plan_type} • {(policy as any).network?.split(' ')[0] || 'N/A'}
                  </div>
                ) : (
                  <div className="text-xs text-slate-500">{policy.category} / {policy.subcategory}</div>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Policy Editor */}
      <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        {policiesError && (
          <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-sm">
            {policiesError}
          </div>
        )}
        {policiesSuccess && (
          <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-700 text-sm">
            {policiesSuccess}
          </div>
        )}

        {(selectedPolicy || showNewPolicyForm) ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">
                {showNewPolicyForm ? 'Create New Policy' : `Edit Policy: ${selectedPolicy?.name || selectedPolicy?.id}`}
              </h2>
              {selectedPolicy && !showNewPolicyForm && (
                <button
                  onClick={handleDeletePolicy}
                  className="px-3 py-1.5 text-sm text-rose-600 hover:text-rose-700 hover:bg-rose-50 rounded-lg"
                >
                  Delete
                </button>
              )}
            </div>

            {isClaimsPersona ? (
              /* Claims Policy Editor */
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Plan Name</label>
                    <input
                      type="text"
                      value={claimsPolicyFormData.plan_name || claimsPolicyFormData.name || ''}
                      onChange={(e) => setClaimsPolicyFormData(prev => ({ ...prev, plan_name: e.target.value, name: e.target.value }))}
                      disabled={!showNewPolicyForm}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm disabled:bg-slate-100"
                      placeholder="e.g., HealthPlus Gold HMO"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Plan Type</label>
                    <select
                      value={claimsPolicyFormData.plan_type || 'HMO'}
                      onChange={(e) => setClaimsPolicyFormData(prev => ({ ...prev, plan_type: e.target.value }))}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                    >
                      <option value="HMO">HMO</option>
                      <option value="PPO">PPO</option>
                      <option value="EPO">EPO</option>
                      <option value="POS">POS</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Network</label>
                  <input
                    type="text"
                    value={claimsPolicyFormData.network || ''}
                    onChange={(e) => setClaimsPolicyFormData(prev => ({ ...prev, network: e.target.value }))}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                    placeholder="e.g., In-Network Only (except emergencies)"
                  />
                </div>

                {/* Deductible */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Deductible</label>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs text-slate-500 mb-1">Individual</label>
                      <input
                        type="text"
                        value={claimsPolicyFormData.deductible?.individual || ''}
                        onChange={(e) => setClaimsPolicyFormData(prev => ({ 
                          ...prev, 
                          deductible: { ...prev.deductible, individual: e.target.value }
                        }))}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                        placeholder="$500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-slate-500 mb-1">Family</label>
                      <input
                        type="text"
                        value={claimsPolicyFormData.deductible?.family || ''}
                        onChange={(e) => setClaimsPolicyFormData(prev => ({ 
                          ...prev, 
                          deductible: { ...prev.deductible, family: e.target.value }
                        }))}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                        placeholder="$1,000"
                      />
                    </div>
                  </div>
                </div>

                {/* Out-of-Pocket Max */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Out-of-Pocket Maximum</label>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs text-slate-500 mb-1">Individual</label>
                      <input
                        type="text"
                        value={claimsPolicyFormData.oop_max?.individual || ''}
                        onChange={(e) => setClaimsPolicyFormData(prev => ({ 
                          ...prev, 
                          oop_max: { ...prev.oop_max, individual: e.target.value }
                        }))}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                        placeholder="$3,000"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-slate-500 mb-1">Family</label>
                      <input
                        type="text"
                        value={claimsPolicyFormData.oop_max?.family || ''}
                        onChange={(e) => setClaimsPolicyFormData(prev => ({ 
                          ...prev, 
                          oop_max: { ...prev.oop_max, family: e.target.value }
                        }))}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                        placeholder="$6,000"
                      />
                    </div>
                  </div>
                </div>

                {/* Copays */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Copays</label>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs text-slate-500 mb-1">PCP Visit</label>
                      <input
                        type="text"
                        value={claimsPolicyFormData.copays?.pcp_visit || ''}
                        onChange={(e) => setClaimsPolicyFormData(prev => ({ 
                          ...prev, 
                          copays: { ...prev.copays, pcp_visit: e.target.value }
                        }))}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                        placeholder="$20"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-slate-500 mb-1">Specialist Visit</label>
                      <input
                        type="text"
                        value={claimsPolicyFormData.copays?.specialist_visit || ''}
                        onChange={(e) => setClaimsPolicyFormData(prev => ({ 
                          ...prev, 
                          copays: { ...prev.copays, specialist_visit: e.target.value }
                        }))}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                        placeholder="$40"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-slate-500 mb-1">Urgent Care</label>
                      <input
                        type="text"
                        value={claimsPolicyFormData.copays?.urgent_care || ''}
                        onChange={(e) => setClaimsPolicyFormData(prev => ({ 
                          ...prev, 
                          copays: { ...prev.copays, urgent_care: e.target.value }
                        }))}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                        placeholder="$50"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-slate-500 mb-1">ER Visit</label>
                      <input
                        type="text"
                        value={claimsPolicyFormData.copays?.er_visit || ''}
                        onChange={(e) => setClaimsPolicyFormData(prev => ({ 
                          ...prev, 
                          copays: { ...prev.copays, er_visit: e.target.value }
                        }))}
                        className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                        placeholder="$250"
                      />
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Coinsurance</label>
                    <input
                      type="text"
                      value={claimsPolicyFormData.coinsurance || ''}
                      onChange={(e) => setClaimsPolicyFormData(prev => ({ ...prev, coinsurance: e.target.value }))}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                      placeholder="10% after deductible"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Preventive Care</label>
                    <input
                      type="text"
                      value={claimsPolicyFormData.preventive_care || ''}
                      onChange={(e) => setClaimsPolicyFormData(prev => ({ ...prev, preventive_care: e.target.value }))}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                      placeholder="Covered 100%"
                    />
                  </div>
                </div>

                {/* Exclusions */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Exclusions</label>
                  <textarea
                    value={Array.isArray(claimsPolicyFormData.exclusions) ? claimsPolicyFormData.exclusions.join('\n') : ''}
                    onChange={(e) => setClaimsPolicyFormData(prev => ({ 
                      ...prev, 
                      exclusions: e.target.value.split('\n').filter(Boolean)
                    }))}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm h-20"
                    placeholder="One exclusion per line"
                  />
                </div>
              </div>
            ) : (
              /* Underwriting Policy Editor */
              <>
                {/* Basic Info */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Policy ID</label>
                    <input
                      type="text"
                      value={policyFormData.id}
                      onChange={(e) => setPolicyFormData(prev => ({ ...prev, id: e.target.value }))}
                      disabled={!showNewPolicyForm}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm disabled:bg-slate-100"
                      placeholder="e.g., CVD-BP-001"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Name</label>
                    <input
                      type="text"
                      value={policyFormData.name}
                      onChange={(e) => setPolicyFormData(prev => ({ ...prev, name: e.target.value }))}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                      placeholder="Policy name"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Category</label>
                    <input
                      type="text"
                      value={policyFormData.category}
                      onChange={(e) => setPolicyFormData(prev => ({ ...prev, category: e.target.value }))}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                      placeholder="e.g., cardiovascular"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Subcategory</label>
                    <input
                      type="text"
                      value={policyFormData.subcategory}
                      onChange={(e) => setPolicyFormData(prev => ({ ...prev, subcategory: e.target.value }))}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                      placeholder="e.g., hypertension"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
                  <textarea
                    value={policyFormData.description}
                    onChange={(e) => setPolicyFormData(prev => ({ ...prev, description: e.target.value }))}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm h-20"
                    placeholder="Policy description"
                  />
                </div>

                {/* Criteria Section */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-slate-700">Criteria</label>
                    <button
                      type="button"
                      onClick={handleAddCriteria}
                      className="text-sm text-indigo-600 hover:text-indigo-700"
                    >
                      + Add Criteria
                    </button>
                  </div>
                  <div className="space-y-3 max-h-[300px] overflow-y-auto">
                    {policyFormData.criteria.map((criteria, index) => (
                      <div key={index} className="p-3 border border-slate-200 rounded-lg bg-slate-50">
                        <div className="flex justify-between items-start mb-2">
                          <span className="text-xs font-mono text-slate-500">{criteria.id}</span>
                          <button
                            type="button"
                            onClick={() => handleRemoveCriteria(index)}
                            className="text-rose-500 hover:text-rose-700 text-sm"
                          >
                            Remove
                          </button>
                        </div>
                        <div className="grid grid-cols-2 gap-2 mb-2">
                          <input
                            type="text"
                            value={criteria.condition}
                            onChange={(e) => handleCriteriaChange(index, 'condition', e.target.value)}
                            className="px-2 py-1 border border-slate-300 rounded text-xs"
                            placeholder="Condition"
                          />
                          <select
                            value={criteria.risk_level}
                            onChange={(e) => handleCriteriaChange(index, 'risk_level', e.target.value)}
                            className="px-2 py-1 border border-slate-300 rounded text-xs"
                          >
                            <option value="Low">Low</option>
                            <option value="Low-Moderate">Low-Moderate</option>
                            <option value="Moderate">Moderate</option>
                            <option value="Moderate-High">Moderate-High</option>
                            <option value="High">High</option>
                          </select>
                        </div>
                        <input
                          type="text"
                          value={criteria.action}
                          onChange={(e) => handleCriteriaChange(index, 'action', e.target.value)}
                          className="w-full px-2 py-1 border border-slate-300 rounded text-xs mb-2"
                          placeholder="Action"
                        />
                        <textarea
                          value={criteria.rationale}
                          onChange={(e) => handleCriteriaChange(index, 'rationale', e.target.value)}
                          className="w-full px-2 py-1 border border-slate-300 rounded text-xs h-12"
                          placeholder="Rationale"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* Save Button */}
            <div className="flex justify-end gap-2 pt-4 border-t">
              <button
                onClick={() => {
                  setSelectedPolicy(null);
                  setShowNewPolicyForm(false);
                }}
                className="px-4 py-2 text-sm text-slate-600 hover:text-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={handleSavePolicy}
                disabled={policiesSaving}
                className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                {policiesSaving ? 'Saving...' : showNewPolicyForm ? 'Create Policy' : 'Save Changes'}
              </button>
            </div>
          </div>
        ) : (
          <div className="text-center py-16 text-slate-500">
            <p className="text-lg mb-2">Select a policy to edit</p>
            <p className="text-sm">Or click &quot;New Policy&quot; to create one</p>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-2">
              <div 
                className="w-9 h-9 rounded-lg flex items-center justify-center shadow-sm"
                style={{ background: `linear-gradient(135deg, ${personaConfig.primaryColor}, ${personaConfig.accentColor})` }}
              >
                <span className="text-white font-bold text-xs">W.IQ</span>
              </div>
              <span className="font-semibold text-lg text-slate-900">WorkbenchIQ</span>
            </Link>
            <span className="text-slate-300">|</span>
            <h1 className="text-xl font-semibold text-slate-700">
              Admin Panel
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <PersonaSelector />
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
              <span className="text-sm text-slate-600">Backend Connected</span>
            </div>
          </div>
        </div>
      </header>

      {/* Persona Banner */}
      <div 
        className="border-b"
        style={{ 
          backgroundColor: `${personaConfig.color}08`,
          borderColor: `${personaConfig.color}20`
        }}
      >
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-3">
          <personaConfig.icon className="w-6 h-6" style={{ color: personaConfig.color }} />
          <div>
            <h2 className="font-medium text-slate-900">{personaConfig.name} Workbench</h2>
            <p className="text-sm text-slate-600">{personaConfig.description}</p>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('documents')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'documents'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
              }`}
            >
              Document Processing
            </button>
            <button
              onClick={() => setActiveTab('prompts')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'prompts'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
              }`}
            >
              Prompt Catalog
            </button>
            <button
              onClick={() => setActiveTab('policies')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'policies'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
              }`}
            >
              {currentPersona.includes('claims') ? 'Claims Policies' : 'Underwriting Policies'}
            </button>
            <button
              onClick={() => setActiveTab('analyzer')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'analyzer'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
              }`}
            >
              Analyzer Management
            </button>
          </nav>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {activeTab === 'documents' && renderDocumentsTab()}
        {activeTab === 'prompts' && renderPromptsTab()}
        {activeTab === 'policies' && renderPoliciesTab()}
        {activeTab === 'analyzer' && renderAnalyzerTab()}
      </main>
    </div>
  );
}
