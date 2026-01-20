/**
 * Automotive Claims Overview Component
 * 
 * Main component for the automotive claims multimodal processing interface.
 * Provides:
 * - Evidence gallery (images, video keyframes, documents)
 * - Damage assessment view
 * - Video timeline with keyframes
 * - Policy-based assessment panel
 * - Adjuster decision controls
 * 
 * @module components/claims/AutomotiveClaimsOverview
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Car, Image, Video, FileText, AlertTriangle, CheckCircle, XCircle, 
  Upload, RefreshCw, BookOpen, DollarSign, Shield, Search
} from 'lucide-react';
import EvidenceGallery from './EvidenceGallery';
import DamageViewer from './DamageViewer';
import VideoTimeline from './VideoTimeline';
import {
  ClaimAssessmentResponse,
  MediaItem,
  Keyframe,
  DamageArea as APIDamageArea,
  PolicyCitationClaim,
  AdjusterDecisionRequest,
  getClaimAssessment,
  getClaimMedia,
  getVideoKeyframes,
  updateAdjusterDecision,
  uploadClaimFiles,
  searchClaimsPolicies,
  ClaimsPolicySearchResult,
} from '@/lib/api';

// Types for automotive claims data
export interface DamageArea {
  location: string;
  damageType: string;
  severity: 'minor' | 'moderate' | 'severe';
  components: string[];
  description: string;
}

export interface VideoSegment {
  timestamp: string;
  duration: string;
  description: string;
  keyframeUrl?: string;
  isImpactFrame?: boolean;
}

export interface PayoutRecommendation {
  minAmount: string;
  maxAmount: string;
  recommendedAmount: string;
}

export interface ClaimAssessment {
  severityRating: 'Minor' | 'Moderate' | 'Heavy' | 'Total Loss';
  liabilityAssessment: 'Clear Liability' | 'Shared' | 'Disputed';
  liabilityPercentage: number;
  payoutRecommendation: PayoutRecommendation;
  policyRulesApplied: string[];
  fraudIndicators: string[];
}

export interface AutomotiveClaimsData {
  claimNumber?: string;
  vehicleMake?: string;
  vehicleModel?: string;
  vehicleYear?: number;
  dateOfLoss?: string;
  damageAreas?: DamageArea[];
  overallDamageSeverity?: string;
  videoSegments?: VideoSegment[];
  estimateTotal?: string;
  assessment?: ClaimAssessment;
}

type TabType = 'evidence' | 'damage' | 'video' | 'assessment';

interface AutomotiveClaimsOverviewProps {
  applicationId: string;
  claimData?: AutomotiveClaimsData;
  isLoading?: boolean;
  onApprove?: () => void;
  onAdjust?: () => void;
  onDeny?: () => void;
  onInvestigate?: () => void;
}

/**
 * Automotive Claims Overview Component
 * 
 * Full implementation with multimodal evidence display
 */
export function AutomotiveClaimsOverview({
  applicationId,
  claimData,
  isLoading = false,
  onApprove,
  onAdjust,
  onDeny,
  onInvestigate,
}: AutomotiveClaimsOverviewProps) {
  const [activeTab, setActiveTab] = useState<TabType>('evidence');
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
      await fetchClaimData(); // Refresh after upload
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
      await fetchClaimData(); // Refresh after decision

      // Call appropriate callback
      switch (decision) {
        case 'approve':
          onApprove?.();
          break;
        case 'adjust':
          onAdjust?.();
          break;
        case 'deny':
          onDeny?.();
          break;
        case 'investigate':
          onInvestigate?.();
          break;
      }
    } catch (err) {
      console.error('Failed to submit decision:', err);
      setError(err instanceof Error ? err.message : 'Failed to submit decision');
    }
  };

  // Handle video selection for keyframes
  const handleVideoSelect = async (media: MediaItem) => {
    if (media.media_type !== 'video') return;
    
    setSelectedVideoId(media.media_id);
    try {
      const keyframeData = await getVideoKeyframes(applicationId, media.media_id);
      setKeyframes(keyframeData.keyframes);
      setVideoDuration(keyframeData.duration);
    } catch (err) {
      console.error('Failed to fetch keyframes:', err);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
        <span className="ml-4 text-gray-600">Processing claim...</span>
      </div>
    );
  }

  const selectedVideo = mediaItems.find((m) => m.media_id === selectedVideoId);

  return (
    <div className="space-y-6">
      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0" />
          <p className="text-red-700">{error}</p>
          <button 
            onClick={() => setError(null)}
            className="ml-auto text-red-600 hover:text-red-800"
          >
            <XCircle className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-red-100 rounded-lg">
              <Car className="h-8 w-8 text-red-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Automotive Claims Assessment
              </h1>
              <p className="text-gray-500">
                Claim #{claimData?.claimNumber || applicationId}
                {claimData?.vehicleMake && ` • ${claimData.vehicleYear} ${claimData.vehicleMake} ${claimData.vehicleModel}`}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {/* Upload Button */}
            <label className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 cursor-pointer transition-colors">
              <Upload className="w-4 h-4" />
              {isUploading ? 'Uploading...' : 'Upload Evidence'}
              <input
                type="file"
                multiple
                accept="image/*,video/*,.pdf"
                onChange={handleFileUpload}
                className="hidden"
                disabled={isUploading}
              />
            </label>
            {/* Refresh Button */}
            <button
              onClick={fetchClaimData}
              disabled={isRefreshing}
              className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-5 h-5 ${isRefreshing ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <SummaryCard
          icon={<AlertTriangle className="h-5 w-5" />}
          label="Damage Severity"
          value={assessment?.overall_severity?.replace('_', ' ').toUpperCase() || claimData?.overallDamageSeverity || 'Pending'}
          color="red"
        />
        <SummaryCard
          icon={<DollarSign className="h-5 w-5" />}
          label="Total Estimate"
          value={assessment?.total_estimated_damage 
            ? `$${assessment.total_estimated_damage.toLocaleString()}`
            : claimData?.estimateTotal || 'N/A'}
          color="blue"
        />
        <SummaryCard
          icon={<Shield className="h-5 w-5" />}
          label="Fraud Indicators"
          value={(assessment?.fraud_indicators?.length || claimData?.assessment?.fraudIndicators?.length || 0).toString()}
          color={(assessment?.fraud_indicators?.length || 0) > 0 ? 'yellow' : 'green'}
        />
        <SummaryCard
          icon={<CheckCircle className="h-5 w-5" />}
          label="Recommended Payout"
          value={assessment?.payout_recommendation?.recommended_amount 
            ? `$${assessment.payout_recommendation.recommended_amount.toLocaleString()}`
            : claimData?.assessment?.payoutRecommendation?.recommendedAmount || 'Pending'}
          color="green"
        />
      </div>

      {/* Tabbed Content */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200 px-6">
          <nav className="flex space-x-8">
            <TabButton 
              active={activeTab === 'evidence'} 
              onClick={() => setActiveTab('evidence')}
              icon={<Image className="w-4 h-4" />}
            >
              Evidence ({mediaItems.length})
            </TabButton>
            <TabButton 
              active={activeTab === 'damage'} 
              onClick={() => setActiveTab('damage')}
              icon={<AlertTriangle className="w-4 h-4" />}
            >
              Damage ({assessment?.damage_areas?.length || 0})
            </TabButton>
            <TabButton 
              active={activeTab === 'video'} 
              onClick={() => setActiveTab('video')}
              icon={<Video className="w-4 h-4" />}
            >
              Video Timeline
            </TabButton>
            <TabButton 
              active={activeTab === 'assessment'} 
              onClick={() => setActiveTab('assessment')}
              icon={<BookOpen className="w-4 h-4" />}
            >
              AI Assessment
            </TabButton>
          </nav>
        </div>
        
        <div className="p-6">
          {/* Evidence Tab */}
          {activeTab === 'evidence' && (
            <EvidenceGallery
              mediaItems={mediaItems}
              damageAreas={assessment?.damage_areas}
              onMediaSelect={handleVideoSelect}
            />
          )}

          {/* Damage Assessment Tab */}
          {activeTab === 'damage' && (
            <DamageViewer
              damageAreas={assessment?.damage_areas || []}
              totalEstimate={assessment?.total_estimated_damage || 0}
            />
          )}

          {/* Video Timeline Tab */}
          {activeTab === 'video' && (
            <div>
              {selectedVideo ? (
                <VideoTimeline
                  videoUrl={selectedVideo.url}
                  duration={videoDuration}
                  keyframes={keyframes}
                />
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <Video className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>No video evidence uploaded</p>
                  <p className="text-sm text-gray-400 mt-1">
                    Upload a video to see the timeline analysis
                  </p>
                </div>
              )}
            </div>
          )}

          {/* AI Assessment Tab */}
          {activeTab === 'assessment' && (
            <div className="space-y-6">
              {/* Liability Assessment */}
              <div className="bg-gray-50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Liability Assessment</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Fault Determination</p>
                    <p className="text-lg font-medium text-gray-900">
                      {assessment?.liability?.fault_determination || 'Pending'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Fault Percentage</p>
                    <p className="text-lg font-medium text-gray-900">
                      {assessment?.liability?.fault_percentage ?? 0}%
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Contributing Factors</p>
                    <p className="text-sm text-gray-700">
                      {assessment?.liability?.contributing_factors?.join(', ') || 'None identified'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Fraud Indicators */}
              {(assessment?.fraud_indicators?.length || 0) > 0 && (
                <div className="bg-yellow-50 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-yellow-800 mb-4 flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5" />
                    Fraud Indicators
                  </h3>
                  <div className="space-y-3">
                    {assessment?.fraud_indicators?.map((indicator, idx) => (
                      <div key={idx} className="flex items-start gap-3 bg-white/50 rounded-lg p-3">
                        <div className={`w-2 h-2 rounded-full mt-2 ${
                          indicator.severity === 'high' ? 'bg-red-500' :
                          indicator.severity === 'medium' ? 'bg-yellow-500' : 'bg-gray-400'
                        }`} />
                        <div>
                          <p className="font-medium text-gray-900">{indicator.indicator_type}</p>
                          <p className="text-sm text-gray-600">{indicator.description}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            Confidence: {(indicator.confidence * 100).toFixed(0)}%
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Policy Citations */}
              <div className="bg-white border border-gray-200 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <BookOpen className="w-5 h-5" />
                  Policy Citations
                </h3>
                
                {/* Policy Search */}
                <div className="flex gap-2 mb-4">
                  <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      type="text"
                      value={policyQuery}
                      onChange={(e) => setPolicyQuery(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handlePolicySearch()}
                      placeholder="Search claims policies..."
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
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

                {/* Policy Search Results */}
                {policyResults.length > 0 && (
                  <div className="mb-4 space-y-2 max-h-48 overflow-y-auto">
                    {policyResults.map((result) => (
                      <div key={result.chunk_id} className="bg-gray-50 rounded-lg p-3">
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="font-medium text-gray-900">{result.policy_name}</p>
                            <p className="text-sm text-gray-500">{result.section}</p>
                          </div>
                          <span className="text-xs bg-gray-200 px-2 py-1 rounded">
                            {(result.score * 100).toFixed(0)}% match
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mt-2 line-clamp-2">{result.content}</p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Applied Citations */}
                <div className="space-y-3">
                  {(assessment?.policy_citations?.length || 0) === 0 ? (
                    <p className="text-gray-500 text-center py-4">
                      No policy citations applied yet
                    </p>
                  ) : (
                    assessment?.policy_citations?.map((citation, idx) => (
                      <div 
                        key={idx} 
                        className={`rounded-lg p-4 ${
                          citation.supports_coverage ? 'bg-green-50' : 'bg-red-50'
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          {citation.supports_coverage ? (
                            <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
                          ) : (
                            <XCircle className="w-5 h-5 text-red-600 mt-0.5" />
                          )}
                          <div>
                            <p className="font-medium text-gray-900">{citation.policy_name}</p>
                            <p className="text-sm text-gray-500">{citation.section}</p>
                            <p className="text-sm text-gray-700 mt-2">{citation.citation_text}</p>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Payout Recommendation */}
              <div className="bg-green-50 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-green-800 mb-4 flex items-center gap-2">
                  <DollarSign className="w-5 h-5" />
                  Payout Recommendation
                </h3>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm text-green-700">Minimum</p>
                    <p className="text-xl font-bold text-green-900">
                      ${assessment?.payout_recommendation?.min_amount?.toLocaleString() || 0}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-green-700">Recommended</p>
                    <p className="text-2xl font-bold text-green-900">
                      ${assessment?.payout_recommendation?.recommended_amount?.toLocaleString() || 0}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-green-700">Maximum</p>
                    <p className="text-xl font-bold text-green-900">
                      ${assessment?.payout_recommendation?.max_amount?.toLocaleString() || 0}
                    </p>
                  </div>
                </div>
                {assessment?.payout_recommendation?.breakdown && (
                  <div className="mt-4 pt-4 border-t border-green-200">
                    <p className="text-sm font-medium text-green-800 mb-2">Breakdown</p>
                    <div className="grid grid-cols-2 gap-2">
                      {Object.entries(assessment.payout_recommendation.breakdown).map(([key, value]) => (
                        <div key={key} className="flex justify-between text-sm">
                          <span className="text-green-700">{key.replace(/_/g, ' ')}</span>
                          <span className="font-medium text-green-900">${value.toLocaleString()}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Adjuster Decision Panel */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Adjuster Decision</h2>
        
        {/* Decision Notes */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Decision Notes
          </label>
          <textarea
            value={decisionNotes}
            onChange={(e) => setDecisionNotes(e.target.value)}
            placeholder="Add notes for your decision..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 resize-none"
            rows={3}
          />
        </div>

        {/* Adjusted Amount (for Adjust decision) */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Adjusted Amount (if adjusting)
          </label>
          <div className="relative w-48">
            <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="number"
              value={adjustedAmount || ''}
              onChange={(e) => setAdjustedAmount(e.target.value ? Number(e.target.value) : undefined)}
              placeholder="0.00"
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
            />
          </div>
        </div>

        {/* Current Decision Status */}
        {assessment?.adjuster_decision && (
          <div className="mb-4 p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Current Decision</p>
            <div className="flex items-center gap-2 mt-1">
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                assessment.adjuster_decision.decision === 'approve' ? 'bg-green-100 text-green-800' :
                assessment.adjuster_decision.decision === 'deny' ? 'bg-red-100 text-red-800' :
                assessment.adjuster_decision.decision === 'investigate' ? 'bg-yellow-100 text-yellow-800' :
                'bg-blue-100 text-blue-800'
              }`}>
                {assessment.adjuster_decision.decision.toUpperCase()}
              </span>
              {assessment.adjuster_decision.adjusted_amount && (
                <span className="text-gray-700">
                  ${assessment.adjuster_decision.adjusted_amount.toLocaleString()}
                </span>
              )}
            </div>
            {assessment.adjuster_decision.notes && (
              <p className="text-sm text-gray-600 mt-2">{assessment.adjuster_decision.notes}</p>
            )}
          </div>
        )}

        {/* Decision Buttons */}
        <div className="flex gap-4">
          <button
            onClick={() => handleDecision('approve')}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <CheckCircle className="h-5 w-5" />
            Approve
          </button>
          <button
            onClick={() => handleDecision('adjust')}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <FileText className="h-5 w-5" />
            Adjust
          </button>
          <button
            onClick={() => handleDecision('deny')}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            <XCircle className="h-5 w-5" />
            Deny
          </button>
          <button
            onClick={() => handleDecision('investigate')}
            className="flex items-center gap-2 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors"
          >
            <AlertTriangle className="h-5 w-5" />
            Investigate
          </button>
        </div>
      </div>
    </div>
  );
}

// Helper Components

interface SummaryCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: 'red' | 'blue' | 'green' | 'yellow';
}

function SummaryCard({ icon, label, value, color }: SummaryCardProps) {
  const colorClasses = {
    red: 'bg-red-50 text-red-600',
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600',
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
          {icon}
        </div>
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-lg font-semibold">{value}</p>
        </div>
      </div>
    </div>
  );
}

interface TabButtonProps {
  children: React.ReactNode;
  active?: boolean;
  onClick?: () => void;
  icon?: React.ReactNode;
}

function TabButton({ children, active = false, onClick, icon }: TabButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
        active
          ? 'border-red-600 text-red-600'
          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
      }`}
    >
      {icon}
      {children}
    </button>
  );
}

export default AutomotiveClaimsOverview;
