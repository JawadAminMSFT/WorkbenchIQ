/**
 * Automotive Claims Overview Component - Redesigned
 * 
 * Single-page layout showing all claim information:
 * - Claim Summary with AI Analysis
 * - Evidence Gallery with PDF viewer and video thumbnails
 * - Damage Assessment
 * - Video Timeline
 * - Liability & Fraud Assessment
 * - Policy Citations
 * - Adjuster Decision Panel
 * 
 * Follows the same styling as the underwriting persona.
 * 
 * @module components/claims/AutomotiveClaimsOverview
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Car, Image, Video, FileText, AlertTriangle, CheckCircle, XCircle, 
  Upload, RefreshCw, BookOpen, DollarSign, Shield, Search, Sparkles,
  Play, Clock, ChevronRight, Eye
} from 'lucide-react';
import VideoTimeline from './VideoTimeline';
import PDFViewer from './PDFViewer';
import DamageViewer from './DamageViewer';
import PolicySearchResults from './PolicySearchResults';
import ConfidenceIndicator from '../ConfidenceIndicator';
import {
  ClaimAssessmentResponse,
  MediaItem,
  Keyframe,
  AdjusterDecisionRequest,
  getClaimAssessment,
  getClaimMedia,
  getVideoKeyframes,
  updateAdjusterDecision,
  uploadClaimFiles,
  searchClaimsPolicies,
  ClaimsPolicySearchResult,
} from '@/lib/api';

interface AutomotiveClaimsOverviewProps {
  applicationId: string;
  isLoading?: boolean;
  onApprove?: () => void;
  onAdjust?: () => void;
  onDeny?: () => void;
  onInvestigate?: () => void;
}

/**
 * Automotive Claims Overview Component
 */
export function AutomotiveClaimsOverview({
  applicationId,
  isLoading = false,
  onApprove,
  onAdjust,
  onDeny,
  onInvestigate,
}: AutomotiveClaimsOverviewProps) {
  const [assessment, setAssessment] = useState<ClaimAssessmentResponse | null>(null);
  const [mediaItems, setMediaItems] = useState<MediaItem[]>([]);
  const [keyframes, setKeyframes] = useState<Keyframe[]>([]);
  const [videoDuration, setVideoDuration] = useState(0);
  const [selectedVideoId, setSelectedVideoId] = useState<string | null>(null);
  const [policyResults, setPolicyResults] = useState<ClaimsPolicySearchResult[]>([]);
  const [policyQuery, setPolicyQuery] = useState('');
  const [isSearchingPolicies, setIsSearchingPolicies] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [decisionNotes, setDecisionNotes] = useState('');
  const [adjustedAmount, setAdjustedAmount] = useState<number | undefined>();
  const [error, setError] = useState<string | null>(null);
  
  // Modal states
  const [selectedPDF, setSelectedPDF] = useState<MediaItem | null>(null);
  const [selectedImage, setSelectedImage] = useState<MediaItem | null>(null);
  const [showVideoModal, setShowVideoModal] = useState(false);
  const [selectedPolicy, setSelectedPolicy] = useState<ClaimsPolicySearchResult | null>(null);

  // Fetch claim assessment and media
  const fetchClaimData = useCallback(async () => {
    setIsRefreshing(true);
    setError(null);
    try {
      const [assessmentData, mediaData] = await Promise.all([
        getClaimAssessment(applicationId),
        getClaimMedia(applicationId),
      ]);
      setAssessment(assessmentData);
      setMediaItems(mediaData.media_items);

      // Find first video and get its keyframes
      const firstVideo = mediaData.media_items.find((m) => m.media_type === 'video');
      if (firstVideo) {
        setSelectedVideoId(firstVideo.media_id);
        const keyframeData = await getVideoKeyframes(applicationId, firstVideo.media_id);
        setKeyframes(keyframeData.keyframes);
        setVideoDuration(keyframeData.duration);
      }
    } catch (err) {
      console.error('Failed to fetch claim data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load claim data');
    } finally {
      setIsRefreshing(false);
    }
  }, [applicationId]);

  useEffect(() => {
    fetchClaimData();
  }, [fetchClaimData]);

  // Handle file upload
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    setError(null);
    try {
      await uploadClaimFiles(applicationId, Array.from(files));
      await fetchClaimData();
    } catch (err) {
      console.error('Failed to upload files:', err);
      setError(err instanceof Error ? err.message : 'Failed to upload files');
    } finally {
      setIsUploading(false);
    }
  };

  // Handle policy search
  const handlePolicySearch = async () => {
    if (!policyQuery.trim()) return;
    
    setIsSearchingPolicies(true);
    try {
      const results = await searchClaimsPolicies({ query: policyQuery, limit: 10 });
      setPolicyResults(results.results);
    } catch (err) {
      console.error('Failed to search policies:', err);
    } finally {
      setIsSearchingPolicies(false);
    }
  };

  // Handle adjuster decision
  const handleDecision = async (decision: 'approve' | 'adjust' | 'deny' | 'investigate') => {
    try {
      const request: AdjusterDecisionRequest = {
        decision,
        notes: decisionNotes || undefined,
        adjusted_amount: decision === 'adjust' ? adjustedAmount : undefined,
      };
      await updateAdjusterDecision(applicationId, request);
      await fetchClaimData();

      switch (decision) {
        case 'approve': onApprove?.(); break;
        case 'adjust': onAdjust?.(); break;
        case 'deny': onDeny?.(); break;
        case 'investigate': onInvestigate?.(); break;
      }
    } catch (err) {
      console.error('Failed to submit decision:', err);
      setError(err instanceof Error ? err.message : 'Failed to submit decision');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
        <span className="ml-4 text-slate-600">Processing claim...</span>
      </div>
    );
  }

  const selectedVideo = mediaItems.find((m) => m.media_id === selectedVideoId);
  const images = mediaItems.filter((m) => m.media_type === 'image');
  const videos = mediaItems.filter((m) => m.media_type === 'video');
  const documents = mediaItems.filter((m) => m.media_type === 'document');

  // Risk level helper
  const getRiskLevel = (severity: string | undefined) => {
    const s = (severity || '').toLowerCase();
    if (s.includes('high') || s.includes('severe') || s.includes('heavy')) {
      return { label: 'High', bgColor: 'bg-rose-50', textColor: 'text-rose-700', borderColor: 'border-rose-200' };
    }
    if (s.includes('moderate') || s.includes('medium')) {
      return { label: 'Moderate', bgColor: 'bg-amber-50', textColor: 'text-amber-700', borderColor: 'border-amber-200' };
    }
    return { label: 'Low', bgColor: 'bg-emerald-50', textColor: 'text-emerald-700', borderColor: 'border-emerald-200' };
  };

  const severityInfo = getRiskLevel(assessment?.overall_severity);

  return (
    <div className="flex-1 overflow-auto p-6">
      <div className="space-y-6">
        {/* Error Banner */}
        {error && (
          <div className="bg-rose-50 border border-rose-200 rounded-lg p-4 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-600 flex-shrink-0" />
            <p className="text-rose-700">{error}</p>
            <button onClick={() => setError(null)} className="ml-auto text-rose-600 hover:text-rose-800">
              <XCircle className="w-5 h-5" />
            </button>
          </div>
        )}

        {/* Header with Upload */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <Car className="h-6 w-6 text-red-600" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-slate-900">Automotive Claim #{applicationId}</h1>
              <p className="text-sm text-slate-500">{mediaItems.length} evidence files uploaded</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 cursor-pointer transition-colors">
              <Upload className="w-4 h-4" />
              {isUploading ? 'Uploading...' : 'Upload Evidence'}
              <input type="file" multiple accept="image/*,video/*,.pdf" onChange={handleFileUpload} className="hidden" disabled={isUploading} />
            </label>
            <button onClick={fetchClaimData} disabled={isRefreshing} className="p-2 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors disabled:opacity-50">
              <RefreshCw className={`w-5 h-5 ${isRefreshing ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Payout Summary - Horizontal Card at Top */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-start gap-8">
            {/* Recommended Payout - Primary */}
            <div className="flex-shrink-0">
              <p className="text-xs text-emerald-600 font-medium uppercase tracking-wider mb-1">Recommended Payout</p>
              <p className="text-4xl font-bold text-emerald-700">
                ${assessment?.payout_recommendation?.recommended_amount?.toLocaleString() || 0}
              </p>
            </div>
            
            {/* Min/Max Range */}
            <div className="flex gap-6 border-l border-slate-200 pl-8">
              <div>
                <p className="text-xs text-slate-500 mb-1">Minimum</p>
                <p className="text-xl font-semibold text-slate-900">
                  ${assessment?.payout_recommendation?.min_amount?.toLocaleString() || 0}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1">Maximum</p>
                <p className="text-xl font-semibold text-slate-900">
                  ${assessment?.payout_recommendation?.max_amount?.toLocaleString() || 0}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1">Total Estimated</p>
                <p className="text-xl font-semibold text-slate-900">
                  ${assessment?.total_estimated_damage?.toLocaleString() || 0}
                </p>
              </div>
            </div>
            
            {/* Quick Stats */}
            <div className="flex gap-6 border-l border-slate-200 pl-8 ml-auto">
              <div className="text-center">
                <p className="text-2xl font-bold text-slate-900">{mediaItems.length}</p>
                <p className="text-xs text-slate-500">Evidence Files</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-slate-900">{assessment?.damage_areas?.length || 0}</p>
                <p className="text-xs text-slate-500">Damage Areas</p>
              </div>
              <div className="text-center">
                <p className={`text-2xl font-bold ${(assessment?.fraud_indicators?.length || 0) > 0 ? 'text-amber-600' : 'text-slate-900'}`}>
                  {assessment?.fraud_indicators?.length || 0}
                </p>
                <p className="text-xs text-slate-500">Fraud Flags</p>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Sections */}
        <div className="space-y-6">
          {/* Claim Summary Card (like Patient Summary) */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">
                    <Car className="w-5 h-5 text-red-600" />
                  </div>
                  <h2 className="text-lg font-semibold text-slate-900">Claim Summary</h2>
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-600 border border-indigo-100">
                    <Sparkles className="w-3 h-3" />
                    AI Analysis
                  </span>
                </div>
                
                {/* Severity Badge */}
                <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${severityInfo.bgColor} ${severityInfo.textColor} border ${severityInfo.borderColor}`}>
                  <Clock className="w-4 h-4" />
                  {assessment?.overall_severity?.replace('_', ' ') || 'Pending Assessment'}
                </span>
              </div>

              {/* Summary Content */}
              <div className="space-y-4">
                {assessment?.damage_areas && assessment.damage_areas.length > 0 ? (
                  <p className="text-sm text-slate-700 leading-relaxed">
                    This claim involves <strong>{assessment.damage_areas.length} identified damage areas</strong> with 
                    an estimated total of <strong>${assessment.total_estimated_damage?.toLocaleString() || 0}</strong>. 
                    {assessment.liability?.fault_determination && (
                      <> Liability assessment indicates <strong>{assessment.liability.fault_determination}</strong> with {assessment.liability.fault_percentage || 0}% fault determination.</>
                    )}
                    {assessment.fraud_indicators && assessment.fraud_indicators.length > 0 && (
                      <> <span className="text-amber-600">⚠ {assessment.fraud_indicators.length} potential fraud indicator(s) detected.</span></>
                    )}
                  </p>
                ) : (
                  <p className="text-sm text-slate-500 italic">Processing claim evidence. Analysis results will appear here.</p>
                )}
              </div>
            </div>

            {/* AI Risk Analysis Card (like Policy Summary Panel) */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
              <div className="px-6 py-4 bg-slate-50 border-b border-slate-100">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center text-red-600">
                    <Shield className="w-5 h-5" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h2 className="text-lg font-semibold text-slate-900">Claim Risk Analysis</h2>
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-600 border border-indigo-100">
                        <Sparkles className="w-3 h-3" />
                        AI Analysis
                      </span>
                    </div>
                    <span className={`text-sm font-medium ${severityInfo.textColor}`}>{severityInfo.label} Risk</span>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-slate-900">{assessment?.damage_areas?.length || 0}</div>
                    <div className="text-xs text-slate-500">Damage Areas</div>
                  </div>
                </div>
              </div>
              
              <div className="p-6 space-y-4">
                {/* Summary */}
                {assessment?.liability && (
                  <p className="text-sm text-slate-700 leading-relaxed">
                    {assessment.liability.fault_determination === 'at_fault' 
                      ? 'The claimant appears to be at fault based on the evidence analysis.'
                      : assessment.liability.fault_determination === 'not_at_fault'
                      ? 'The claimant does not appear to be at fault based on the evidence analysis.'
                      : 'Liability is shared or disputed based on the available evidence.'}
                    {assessment.fraud_indicators && assessment.fraud_indicators.length > 0 
                      ? ` However, ${assessment.fraud_indicators.length} potential fraud indicator(s) require additional review.`
                      : ' No fraud indicators were detected.'}
                  </p>
                )}

                {/* Premium Recommendation equivalent - Payout */}
                <div className="pt-4 border-t border-slate-100">
                  <div className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">PAYOUT RECOMMENDATION</div>
                  <div className="flex items-center gap-4">
                    <span className={`text-lg font-semibold ${
                      (assessment?.fraud_indicators?.length || 0) > 0 ? 'text-amber-600' : 'text-emerald-600'
                    }`}>
                      {(assessment?.fraud_indicators?.length || 0) > 0 ? 'Review Required' : 'Approve'}
                    </span>
                    <span className="text-slate-600">
                      Recommended: <strong className="text-slate-900">${assessment?.payout_recommendation?.recommended_amount?.toLocaleString() || 0}</strong>
                    </span>
                  </div>
                </div>

                {/* Key Findings */}
                <div className="pt-4 border-t border-slate-100">
                  <div className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3">KEY FINDINGS</div>
                  <div className="space-y-3">
                    {/* Damage Assessment */}
                    {assessment?.damage_areas?.slice(0, 3).map((area, idx) => (
                      <div key={idx} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                        <span className={`px-2 py-0.5 text-xs font-medium rounded ${
                          area.severity === 'severe' ? 'bg-rose-100 text-rose-700' :
                          area.severity === 'moderate' ? 'bg-amber-100 text-amber-700' :
                          'bg-emerald-100 text-emerald-700'
                        }`}>
                          {area.severity?.toUpperCase()}
                        </span>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-slate-900">{area.location?.replace(/_/g, ' ')}</p>
                          <p className="text-xs text-slate-600">{area.description}</p>
                          {area.estimated_cost && (
                            <p className="text-xs text-slate-500 mt-1">Est. cost: ${area.estimated_cost.toLocaleString()}</p>
                          )}
                        </div>
                        <ConfidenceIndicator confidence={area.confidence || 0.8} />
                      </div>
                    ))}

                    {/* Fraud Indicators */}
                    {assessment?.fraud_indicators?.map((indicator, idx) => (
                      <div key={`fraud-${idx}`} className="flex items-start gap-3 p-3 bg-amber-50 rounded-lg border border-amber-200">
                        <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5" />
                        <div className="flex-1">
                          <p className="text-sm font-medium text-amber-800">{indicator.indicator_type}</p>
                          <p className="text-xs text-amber-700">{indicator.description}</p>
                        </div>
                        <ConfidenceIndicator confidence={indicator.confidence || 0.7} />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Section Divider - Evidence */}
            <div className="flex items-center gap-4 py-2">
              <div className="flex-1 border-t border-slate-200" />
              <div className="flex items-center gap-2 text-xs font-medium text-slate-400 uppercase tracking-wider">
                <FileText className="w-4 h-4" />
                <span>Evidence Gallery</span>
              </div>
              <div className="flex-1 border-t border-slate-200" />
            </div>

            {/* Evidence Grid */}
            <div className="grid grid-cols-3 gap-6">
              {/* Images Panel */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Image className="w-5 h-5 text-blue-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900">Photos ({images.length})</h3>
                </div>
                <div className="space-y-2">
                  {images.length === 0 ? (
                    <p className="text-sm text-slate-500 italic">No photos uploaded</p>
                  ) : (
                    images.slice(0, 4).map((img) => (
                      <div 
                        key={img.media_id}
                        className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors"
                        onClick={() => setSelectedImage(img)}
                      >
                        <div className="w-12 h-12 rounded-lg overflow-hidden bg-slate-100 flex-shrink-0">
                          <img src={img.url} alt={img.filename} className="w-full h-full object-cover" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-slate-900 truncate">{img.filename}</p>
                          <p className="text-xs text-slate-500">{(img.size / 1024).toFixed(0)} KB</p>
                        </div>
                        <Eye className="w-4 h-4 text-slate-400" />
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Videos Panel */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                    <Video className="w-5 h-5 text-purple-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900">Videos ({videos.length})</h3>
                </div>
                <div className="space-y-2">
                  {videos.length === 0 ? (
                    <p className="text-sm text-slate-500 italic">No videos uploaded</p>
                  ) : (
                    videos.map((vid) => (
                      <div 
                        key={vid.media_id}
                        className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors"
                        onClick={() => setShowVideoModal(true)}
                      >
                        <div className="w-12 h-12 rounded-lg overflow-hidden bg-slate-800 flex-shrink-0 relative">
                          {/* Video thumbnail - use first keyframe or placeholder */}
                          {keyframes.length > 0 && keyframes[0].thumbnail_url ? (
                            <img src={keyframes[0].thumbnail_url} alt="Video thumbnail" className="w-full h-full object-cover" />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center">
                              <Play className="w-4 h-4 text-white" />
                            </div>
                          )}
                          <div className="absolute inset-0 flex items-center justify-center">
                            <div className="w-6 h-6 rounded-full bg-white/80 flex items-center justify-center">
                              <Play className="w-3 h-3 text-slate-800" />
                            </div>
                          </div>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-slate-900 truncate">{vid.filename}</p>
                          <p className="text-xs text-slate-500">{keyframes.length} keyframes • {Math.round(videoDuration)}s</p>
                        </div>
                        <ChevronRight className="w-4 h-4 text-slate-400" />
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Documents Panel */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center">
                    <FileText className="w-5 h-5 text-amber-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900">Documents ({documents.length})</h3>
                </div>
                <div className="space-y-2">
                  {documents.length === 0 ? (
                    <p className="text-sm text-slate-500 italic">No documents uploaded</p>
                  ) : (
                    documents.map((doc) => (
                      <div 
                        key={doc.media_id}
                        className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors"
                        onClick={() => setSelectedPDF(doc)}
                      >
                        <div className="w-10 h-12 rounded bg-rose-50 border border-rose-200 flex items-center justify-center flex-shrink-0">
                          <FileText className="w-5 h-5 text-rose-500" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-slate-900 truncate">{doc.filename}</p>
                          <p className="text-xs text-slate-500">{(doc.size / 1024).toFixed(0)} KB • PDF</p>
                        </div>
                        <Eye className="w-4 h-4 text-slate-400" />
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* Damage Assessment Section with Vehicle Diagram */}
            {assessment?.damage_areas && assessment.damage_areas.length > 0 && (
              <>
                <div className="flex items-center gap-4 py-2">
                  <div className="flex-1 border-t border-slate-200" />
                  <div className="flex items-center gap-2 text-xs font-medium text-slate-400 uppercase tracking-wider">
                    <Car className="w-4 h-4" />
                    <span>Damage Assessment</span>
                  </div>
                  <div className="flex-1 border-t border-slate-200" />
                </div>

                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                  <DamageViewer
                    damageAreas={assessment.damage_areas}
                    totalEstimate={assessment.total_estimated_damage || 0}
                  />
                </div>
              </>
            )}

            {/* Video Timeline Section (inline, not in tab) */}
            {selectedVideo && (
              <>
                <div className="flex items-center gap-4 py-2">
                  <div className="flex-1 border-t border-slate-200" />
                  <div className="flex items-center gap-2 text-xs font-medium text-slate-400 uppercase tracking-wider">
                    <Video className="w-4 h-4" />
                    <span>Video Timeline Analysis</span>
                  </div>
                  <div className="flex-1 border-t border-slate-200" />
                </div>

                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                  <VideoTimeline
                    videoUrl={selectedVideo.url}
                    duration={videoDuration}
                    keyframes={keyframes}
                  />
                </div>
              </>
            )}

            {/* Policy Citations Section */}
            <div className="flex items-center gap-4 py-2">
              <div className="flex-1 border-t border-slate-200" />
              <div className="flex items-center gap-2 text-xs font-medium text-slate-400 uppercase tracking-wider">
                <BookOpen className="w-4 h-4" />
                <span>Policy Citations</span>
              </div>
              <div className="flex-1 border-t border-slate-200" />
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              {/* Policy Search */}
              <div className="flex gap-2 mb-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    value={policyQuery}
                    onChange={(e) => setPolicyQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handlePolicySearch()}
                    placeholder="Search claims policies..."
                    className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
                  />
                </div>
                <button
                  onClick={handlePolicySearch}
                  disabled={isSearchingPolicies}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                >
                  {isSearchingPolicies ? 'Searching...' : 'Search'}
                </button>
              </div>

              {/* Search Results */}
              {policyResults.length > 0 && (
                <div className="mb-4 max-h-96 overflow-y-auto">
                  <PolicySearchResults 
                    results={policyResults}
                    onPolicySelect={(result) => {
                      setSelectedPolicy(result);
                    }}
                  />
                </div>
              )}

              {/* Applied Citations */}
              <div className="space-y-3">
                {(assessment?.policy_citations?.length || 0) === 0 ? (
                  <p className="text-slate-500 text-center py-4">No policy citations applied yet</p>
                ) : (
                  assessment?.policy_citations?.map((citation, idx) => (
                    <div 
                      key={idx} 
                      className={`rounded-lg p-4 ${citation.supports_coverage ? 'bg-emerald-50 border border-emerald-200' : 'bg-rose-50 border border-rose-200'}`}
                    >
                      <div className="flex items-start gap-3">
                        {citation.supports_coverage ? (
                          <CheckCircle className="w-5 h-5 text-emerald-600 mt-0.5" />
                        ) : (
                          <XCircle className="w-5 h-5 text-rose-600 mt-0.5" />
                        )}
                        <div className="flex-1">
                          <p className="font-medium text-slate-900">{citation.policy_name}</p>
                          <p className="text-sm text-slate-500">{citation.section}</p>
                          <p className="text-sm text-slate-700 mt-2">{citation.citation_text}</p>
                        </div>
                        <ConfidenceIndicator confidence={citation.relevance_score || 0.9} />
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Adjuster Decision Panel */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <h2 className="text-lg font-semibold text-slate-900 mb-4">Adjuster Decision</h2>
              
              {/* Decision Notes */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-slate-700 mb-2">Decision Notes</label>
                <textarea
                  value={decisionNotes}
                  onChange={(e) => setDecisionNotes(e.target.value)}
                  placeholder="Add notes for your decision..."
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 resize-none"
                  rows={3}
                />
              </div>

              {/* Adjusted Amount */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-slate-700 mb-2">Adjusted Amount (if adjusting)</label>
                <div className="relative w-48">
                  <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="number"
                    value={adjustedAmount || ''}
                    onChange={(e) => setAdjustedAmount(e.target.value ? Number(e.target.value) : undefined)}
                    placeholder="0.00"
                    className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
                  />
                </div>
              </div>

              {/* Decision Buttons */}
              <div className="flex gap-4">
                <button onClick={() => handleDecision('approve')} className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors">
                  <CheckCircle className="h-5 w-5" /> Approve
                </button>
                <button onClick={() => handleDecision('adjust')} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                  <FileText className="h-5 w-5" /> Adjust
                </button>
                <button onClick={() => handleDecision('deny')} className="flex items-center gap-2 px-4 py-2 bg-rose-600 text-white rounded-lg hover:bg-rose-700 transition-colors">
                  <XCircle className="h-5 w-5" /> Deny
                </button>
                <button onClick={() => handleDecision('investigate')} className="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors">
                  <AlertTriangle className="h-5 w-5" /> Investigate
                </button>
              </div>
            </div>
          </div>
      </div>

      {/* PDF Viewer Modal */}
      {selectedPDF && (
        <PDFViewer
          url={selectedPDF.url}
          filename={selectedPDF.filename}
          onClose={() => setSelectedPDF(null)}
        />
      )}

      {/* Image Viewer Modal */}
      {selectedImage && (
        <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center" onClick={() => setSelectedImage(null)}>
          <button onClick={() => setSelectedImage(null)} className="absolute top-4 right-4 p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors">
            <XCircle className="w-6 h-6 text-white" />
          </button>
          <img src={selectedImage.url} alt={selectedImage.filename} className="max-w-[90vw] max-h-[90vh] object-contain" />
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-black/70 text-white px-4 py-2 rounded-lg">
            {selectedImage.filename}
          </div>
        </div>
      )}

      {/* Video Modal */}
      {showVideoModal && selectedVideo && (
        <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center" onClick={() => setShowVideoModal(false)}>
          <button onClick={() => setShowVideoModal(false)} className="absolute top-4 right-4 p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors">
            <XCircle className="w-6 h-6 text-white" />
          </button>
          <video src={selectedVideo.url} controls autoPlay className="max-w-[90vw] max-h-[90vh]" onClick={(e) => e.stopPropagation()} />
        </div>
      )}

      {/* Policy Detail Modal */}
      {selectedPolicy && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={() => setSelectedPolicy(null)}>
          <div 
            className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto" 
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Shield className="w-6 h-6 text-red-600" />
                <h3 className="text-lg font-semibold text-slate-900">{selectedPolicy.policy_name}</h3>
              </div>
              <button onClick={() => setSelectedPolicy(null)} className="p-1 rounded-full hover:bg-slate-100 transition-colors">
                <XCircle className="w-5 h-5 text-slate-500" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-4">
              {/* Badges */}
              <div className="flex flex-wrap gap-2">
                <span className="inline-flex items-center gap-1 text-xs font-mono bg-indigo-100 text-indigo-700 px-2 py-1 rounded">
                  <FileText className="w-3 h-3" />
                  {selectedPolicy.policy_id}
                </span>
                <span className="inline-flex items-center text-xs px-2 py-1 rounded bg-slate-100 text-slate-700">
                  {selectedPolicy.category.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                </span>
                {selectedPolicy.similarity !== undefined && (
                  <span className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded bg-emerald-100 text-emerald-700">
                    {Math.round(selectedPolicy.similarity * 100)}% match
                  </span>
                )}
              </div>

              {/* Full Content */}
              <div className="bg-slate-50 rounded-lg p-4">
                <h4 className="text-sm font-medium text-slate-700 mb-2">Policy Content</h4>
                <div className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">
                  {selectedPolicy.content.split(/(?=Condition:|Risk Level:|Action:|Rationale:|Description:|Modifying Factors:)/i).map((part, idx) => {
                    const trimmed = part.trim();
                    if (!trimmed) return null;
                    const labelMatch = trimmed.match(/^(Condition|Risk Level|Action|Rationale|Description|Modifying Factors):/i);
                    if (labelMatch) {
                      return (
                        <div key={idx} className="mb-3">
                          <span className="font-semibold text-slate-800">{labelMatch[1]}: </span>
                          <span>{trimmed.slice(labelMatch[0].length).trim()}</span>
                        </div>
                      );
                    }
                    return <p key={idx} className="mb-2">{trimmed}</p>;
                  })}
                </div>
              </div>

              {/* Criteria ID if available */}
              {selectedPolicy.criteria_id && (
                <div className="text-xs text-slate-500">
                  Criteria ID: <span className="font-mono">{selectedPolicy.criteria_id}</span>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="sticky bottom-0 bg-white border-t border-slate-200 px-6 py-4">
              <button 
                onClick={() => setSelectedPolicy(null)}
                className="w-full px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AutomotiveClaimsOverview;
