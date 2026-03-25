'use client';

import React, { useEffect, useRef, useCallback, useState, useMemo } from 'react';
import {
  X, Download, Sparkles, RefreshCw, Loader2,
  Home, MapPin, TrendingUp, TrendingDown, Minus,
  Building, DollarSign, Camera, CheckCircle, AlertTriangle, XCircle,
  Search, BarChart3, ChevronLeft, ChevronRight, Layers, Ruler,
  Calendar, Car, BedDouble, Bath, Warehouse
} from 'lucide-react';
import type { PropertyDeepDiveData, PropertyDeepDiveComparable, PropertyFeature } from '@/lib/types';
import { getPropertyDeepDive, runPropertyDeepDive } from '@/lib/api';

interface PropertyDeepDiveModalProps {
  isOpen: boolean;
  onClose: () => void;
  applicationId: string;
  propertyAddress?: string;
}

type SortField = 'sold_price' | 'sold_date' | 'distance_km';
type SortDir = 'asc' | 'desc';

const fmtCAD = (v: number | undefined | null) => {
  if (v == null) return '—';
  return new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD', maximumFractionDigits: 0 }).format(v);
};

const fmtNum = (v: number | undefined | null, decimals = 0) => {
  if (v == null) return '—';
  return new Intl.NumberFormat('en-CA', { maximumFractionDigits: decimals }).format(v);
};

const fmtPct = (v: number | undefined | null) => {
  if (v == null) return '—';
  return `${v >= 0 ? '+' : ''}${v.toFixed(1)}%`;
};

export default function PropertyDeepDiveModal({
  isOpen,
  onClose,
  applicationId,
  propertyAddress,
}: PropertyDeepDiveModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const [data, setData] = useState<PropertyDeepDiveData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isRerunning, setIsRerunning] = useState(false);
  const [rerunStatus, setRerunStatus] = useState('');
  const [photoIndex, setPhotoIndex] = useState(0);
  const [compSort, setCompSort] = useState<{ field: SortField; dir: SortDir }>({ field: 'distance_km', dir: 'asc' });

  // Fetch data on open
  useEffect(() => {
    if (!isOpen) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    getPropertyDeepDive(applicationId)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load property analysis');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [isOpen, applicationId]);

  // Cleanup timeouts
  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    const handleEscape = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  // Lock body scroll
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

  const handleRerun = useCallback(async (force = false) => {
    if (isRerunning) return;
    if (timeoutRef.current) { clearTimeout(timeoutRef.current); timeoutRef.current = null; }

    setIsRerunning(true);
    setRerunStatus(force ? 'Force re-running property analysis...' : 'Starting property analysis...');

    try {
      const result = await runPropertyDeepDive(applicationId, force);
      setData(result);
      setRerunStatus('Analysis complete!');
      timeoutRef.current = setTimeout(() => {
        setRerunStatus('');
        setIsRerunning(false);
        timeoutRef.current = null;
      }, 2000);
    } catch (err) {
      console.error('Failed to run property deep dive:', err);
      setRerunStatus('Analysis failed. Please try again.');
      timeoutRef.current = setTimeout(() => {
        setRerunStatus('');
        setIsRerunning(false);
        timeoutRef.current = null;
      }, 3000);
    }
  }, [isRerunning, applicationId]);

  // Sorted comparables
  const sortedComps = useMemo(() => {
    if (!data?.comparable_sales) return [];
    return [...data.comparable_sales].sort((a, b) => {
      const mul = compSort.dir === 'asc' ? 1 : -1;
      if (compSort.field === 'sold_date') {
        return mul * (new Date(a.sold_date).getTime() - new Date(b.sold_date).getTime());
      }
      return mul * ((a[compSort.field] as number) - (b[compSort.field] as number));
    });
  }, [data?.comparable_sales, compSort]);

  const toggleSort = (field: SortField) => {
    setCompSort((prev) =>
      prev.field === field ? { field, dir: prev.dir === 'asc' ? 'desc' : 'asc' } : { field, dir: 'asc' }
    );
  };

  // Group features by category
  const groupedFeatures = useMemo(() => {
    if (!data?.property_features) return new Map<string, PropertyFeature[]>();
    const map = new Map<string, PropertyFeature[]>();
    for (const f of data.property_features) {
      const cat = f.category || 'Other';
      if (!map.has(cat)) map.set(cat, []);
      map.get(cat)!.push(f);
    }
    return map;
  }, [data?.property_features]);

  // Comp stats
  const compStats = useMemo(() => {
    if (!sortedComps.length) return null;
    const avg = sortedComps.reduce((s, c) => s + c.sold_price, 0) / sortedComps.length;
    const subjectPrice = data?.property_summary.purchase_price || 0;
    const variance = subjectPrice ? ((subjectPrice - avg) / avg) * 100 : 0;
    return { avg, variance };
  }, [sortedComps, data?.property_summary.purchase_price]);

  /** Build a print-ready HTML report */
  const handleExportFullReport = useCallback(() => {
    if (!data) return;
    const caseRef = applicationId;
    const now = new Date().toLocaleString();
    const esc = (s: string | undefined | null) =>
      (s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

    const sections: string[] = [];

    // Property Summary
    const ps = data.property_summary;
    let html = '<h2>Property Summary</h2>';
    html += `<table border="1" cellpadding="4" cellspacing="0" style="border-collapse:collapse;width:100%;font-size:12px"><tbody>`;
    html += `<tr><td><strong>Address</strong></td><td>${esc(ps.address)}</td><td><strong>Type</strong></td><td>${esc(ps.property_type)}</td></tr>`;
    html += `<tr><td><strong>Purchase Price</strong></td><td>${fmtCAD(ps.purchase_price)}</td><td><strong>Appraised Value</strong></td><td>${fmtCAD(ps.appraised_value)}</td></tr>`;
    html += `<tr><td><strong>Year Built</strong></td><td>${ps.year_built ?? '—'}</td><td><strong>Living Area</strong></td><td>${ps.living_area ? fmtNum(ps.living_area) + ' sqft' : '—'}</td></tr>`;
    html += `<tr><td><strong>Bedrooms</strong></td><td>${ps.bedrooms ?? '—'}</td><td><strong>Bathrooms</strong></td><td>${ps.bathrooms ?? '—'}</td></tr>`;
    html += `<tr><td><strong>Lot Size</strong></td><td>${esc(ps.lot_size)}</td><td><strong>Parking</strong></td><td>${esc(ps.parking)}</td></tr>`;
    html += `</tbody></table>`;
    sections.push(html);

    // Appraisal Recommendation
    html = '<h2>Appraisal Recommendation</h2>';
    html += `<p><strong>Status:</strong> ${data.auto_appraisal_eligible ? 'Auto-Appraisal Eligible' : 'Physical Appraisal Required'}</p>`;
    html += `<p>${esc(data.auto_appraisal_recommendation)}</p>`;
    if (data.risk_rationale) html += `<p><strong>Risk Rationale:</strong> ${esc(data.risk_rationale)}</p>`;
    sections.push(html);

    // Comparables
    if (data.comparable_sales.length) {
      html = '<h2>Comparable Sales</h2>';
      html += '<table border="1" cellpadding="4" cellspacing="0" style="border-collapse:collapse;width:100%;font-size:12px"><thead><tr>';
      html += '<th>Address</th><th>Sold Price</th><th>Date</th><th>Distance</th><th>Bed/Bath</th><th>Area</th><th>$/sqft</th><th>Similarity</th></tr></thead><tbody>';
      for (const c of data.comparable_sales) {
        html += `<tr><td>${esc(c.address)}</td><td>${fmtCAD(c.sold_price)}</td><td>${esc(c.sold_date)}</td><td>${c.distance_km.toFixed(1)} km</td><td>${c.bedrooms}/${c.bathrooms}</td><td>${fmtNum(c.living_area)} sqft</td><td>${fmtCAD(c.price_psf)}</td><td>${c.similarity_score}%</td></tr>`;
      }
      html += '</tbody></table>';
      sections.push(html);
    }

    // Market Trends
    const pt = data.price_trend;
    if (pt) {
      html = '<h2>Market Trends — ' + esc(pt.area_name) + '</h2>';
      html += `<p>Current Avg: ${fmtCAD(pt.avg_price_current)} | 1yr Ago: ${fmtCAD(pt.avg_price_1yr_ago)} | 3yr Ago: ${fmtCAD(pt.avg_price_3yr_ago)}</p>`;
      html += `<p>YoY Change: ${fmtPct(pt.yoy_change_pct)} | 3yr CAGR: ${fmtPct(pt.cagr_3yr_pct)} | Trend: ${pt.trend_direction}</p>`;
      sections.push(html);
    }

    const fullHtml = `<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Property Deep Dive — ${esc(caseRef)}</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; color: #1e293b; font-size: 13px; line-height: 1.6; }
  h1 { font-size: 20px; border-bottom: 2px solid #059669; padding-bottom: 6px; }
  h2 { font-size: 16px; color: #334155; margin-top: 1.5em; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; }
  table { margin: 8px 0; }
  th { background: #f1f5f9; text-align: left; }
  .meta { color: #94a3b8; font-size: 11px; }
  @media print { body { margin: 0; } }
</style></head><body>
<h1>Property Deep Dive — ${esc(caseRef)}</h1>
<p class="meta">Generated ${esc(now)} — WorkbenchIQ AI Analysis</p>
${sections.join('\n')}
</body></html>`;

    const win = window.open('', '_blank');
    if (win) {
      win.document.write(fullHtml);
      win.document.close();
      setTimeout(() => win.print(), 400);
    }
  }, [data, applicationId]);

  if (!isOpen) return null;

  const photos = data?.photos || [];
  const currentPhoto = photos[photoIndex];
  const ps = data?.property_summary;

  const riskColors: Record<string, string> = {
    low: 'bg-green-100 text-green-700 border-green-200',
    medium: 'bg-amber-100 text-amber-700 border-amber-200',
    high: 'bg-red-100 text-red-700 border-red-200',
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div
        ref={modalRef}
        className="relative w-[95vw] h-[92vh] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-white flex-shrink-0">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold text-slate-900">Property Deep Dive</h2>
            <span className="text-sm text-slate-500">— {applicationId}</span>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-600 border border-emerald-100">
              <Sparkles className="w-3 h-3" />
              AI Analysis
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleRerun(true)}
              disabled={isRerunning}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-emerald-600 bg-emerald-50 hover:bg-emerald-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Force re-run property analysis"
            >
              {isRerunning ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              {isRerunning ? 'Analyzing...' : 'Re-run'}
            </button>
            <button
              onClick={handleExportFullReport}
              disabled={!data}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors disabled:opacity-50"
            >
              <Download className="w-4 h-4" />
              Export
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Body */}
        {loading ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <Loader2 className="w-10 h-10 animate-spin text-emerald-500 mx-auto mb-4" />
              <p className="text-sm text-slate-500">Loading property analysis…</p>
            </div>
          </div>
        ) : error ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center max-w-md">
              <AlertTriangle className="w-10 h-10 text-red-400 mx-auto mb-4" />
              <p className="text-slate-600 mb-4">{error}</p>
              <button
                onClick={() => {
                  setError(null);
                  setLoading(true);
                  getPropertyDeepDive(applicationId)
                    .then(setData)
                    .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load'))
                    .finally(() => setLoading(false));
                }}
                className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors text-sm font-medium"
              >
                <RefreshCw className="w-4 h-4" />
                Retry
              </button>
            </div>
          </div>
        ) : !data ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center max-w-md">
              <Home className="w-10 h-10 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500 mb-4">No property analysis available for this application.</p>
              {rerunStatus && (
                <div className="mb-4 p-3 bg-emerald-50 text-emerald-700 rounded-lg text-sm flex items-center gap-2 justify-center">
                  {isRerunning && <Loader2 className="w-4 h-4 animate-spin" />}
                  {rerunStatus}
                </div>
              )}
              <button
                onClick={() => handleRerun(false)}
                disabled={isRerunning}
                className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isRerunning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                {isRerunning ? 'Analyzing...' : 'Run Property Analysis'}
              </button>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Rerun status banner */}
            {rerunStatus && (
              <div className="px-6 py-2 bg-emerald-50 text-emerald-700 text-sm flex items-center gap-2 border-b border-emerald-100 flex-shrink-0">
                {isRerunning && <Loader2 className="w-4 h-4 animate-spin" />}
                {rerunStatus}
              </div>
            )}

            {/* Warning banner */}
            {data.warning && (
              <div className="px-6 py-2 bg-amber-50 text-amber-700 text-sm flex items-center gap-2 border-b border-amber-100 flex-shrink-0">
                <AlertTriangle className="w-4 h-4" />
                {data.warning}
              </div>
            )}

            <div className="flex-1 flex overflow-hidden">
              {/* Left Panel — Property Overview */}
              <div className="w-80 flex-shrink-0 border-r border-slate-200 overflow-y-auto p-4 bg-slate-50/50">
                {/* Photo Carousel */}
                <div className="bg-white rounded-lg border border-slate-200 overflow-hidden mb-4">
                  <div className="relative aspect-[4/3] bg-slate-100">
                    {currentPhoto ? (
                      <img
                        src={currentPhoto.url}
                        alt={currentPhoto.caption || 'Property photo'}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex flex-col items-center justify-center text-slate-400">
                        <Camera className="w-10 h-10 mb-2" />
                        <span className="text-xs">No photos available</span>
                      </div>
                    )}
                    {photos.length > 1 && (
                      <>
                        <button
                          onClick={() => setPhotoIndex((i) => (i - 1 + photos.length) % photos.length)}
                          className="absolute left-1 top-1/2 -translate-y-1/2 p-1 bg-black/40 hover:bg-black/60 text-white rounded-full transition-colors"
                        >
                          <ChevronLeft className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setPhotoIndex((i) => (i + 1) % photos.length)}
                          className="absolute right-1 top-1/2 -translate-y-1/2 p-1 bg-black/40 hover:bg-black/60 text-white rounded-full transition-colors"
                        >
                          <ChevronRight className="w-4 h-4" />
                        </button>
                        <div className="absolute bottom-2 left-1/2 -translate-x-1/2 bg-black/50 text-white text-xs px-2 py-0.5 rounded-full">
                          {photoIndex + 1} / {photos.length}
                        </div>
                      </>
                    )}
                  </div>
                  {currentPhoto?.caption && (
                    <div className="px-3 py-1.5 text-xs text-slate-500 border-t border-slate-100">
                      {currentPhoto.caption}
                    </div>
                  )}
                </div>

                {/* Quick Stats Cards */}
                <div className="space-y-2">
                  {/* Risk Classification */}
                  <div className="bg-white rounded-lg p-3 border border-slate-200">
                    <div className="text-xs text-slate-500 mb-1">Risk Classification</div>
                    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-sm font-medium border ${riskColors[data.risk_classification] || riskColors.medium}`}>
                      {data.risk_classification === 'low' && <CheckCircle className="w-3.5 h-3.5" />}
                      {data.risk_classification === 'medium' && <AlertTriangle className="w-3.5 h-3.5" />}
                      {data.risk_classification === 'high' && <XCircle className="w-3.5 h-3.5" />}
                      {data.risk_classification.charAt(0).toUpperCase() + data.risk_classification.slice(1)}
                    </span>
                  </div>

                  {/* Auto-Appraisal Status */}
                  <div className="bg-white rounded-lg p-3 border border-slate-200">
                    <div className="text-xs text-slate-500 mb-1">Auto-Appraisal Status</div>
                    <span className={`inline-flex items-center gap-1.5 text-sm font-semibold ${data.auto_appraisal_eligible ? 'text-green-700' : 'text-amber-700'}`}>
                      {data.auto_appraisal_eligible ? <CheckCircle className="w-3.5 h-3.5" /> : <AlertTriangle className="w-3.5 h-3.5" />}
                      {data.auto_appraisal_eligible ? 'Eligible' : 'Not Eligible'}
                    </span>
                  </div>

                  {/* Comparable Sales Count */}
                  <div className="bg-white rounded-lg p-3 border border-slate-200">
                    <div className="text-xs text-slate-500 mb-1">Comparable Sales</div>
                    <div className="text-lg font-semibold text-slate-800">
                      {data.comparable_sales?.length || 0}
                    </div>
                  </div>

                  {/* Price vs Area Average */}
                  {data.price_trend && ps && (
                    <div className="bg-white rounded-lg p-3 border border-slate-200">
                      <div className="text-xs text-slate-500 mb-1">Price vs Area Avg</div>
                      <div className="text-sm font-semibold text-slate-800">
                        {(() => {
                          const diff = data.price_trend.avg_price_current
                            ? ((ps.purchase_price - data.price_trend.avg_price_current) / data.price_trend.avg_price_current) * 100
                            : 0;
                          return (
                            <span className={diff > 5 ? 'text-red-600' : diff < -5 ? 'text-green-600' : 'text-slate-700'}>
                              {diff >= 0 ? '+' : ''}{diff.toFixed(1)}%
                            </span>
                          );
                        })()}
                      </div>
                    </div>
                  )}
                </div>

                {/* Property Details */}
                {ps && (
                  <div className="mt-4 bg-white rounded-lg p-3 border border-slate-200">
                    <div className="text-xs font-semibold text-slate-600 uppercase tracking-wide mb-2">Property</div>
                    <div className="space-y-1.5 text-sm">
                      <div className="flex items-start gap-2 text-slate-700">
                        <MapPin className="w-3.5 h-3.5 text-slate-400 mt-0.5 flex-shrink-0" />
                        <span>{ps.address}</span>
                      </div>
                      <div className="flex items-center gap-2 text-slate-700">
                        <Building className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                        <span>{ps.property_type}</span>
                      </div>
                      <div className="flex items-center gap-2 text-slate-700">
                        <DollarSign className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                        <span>{fmtCAD(ps.purchase_price)}</span>
                      </div>
                      {ps.year_built && (
                        <div className="flex items-center gap-2 text-slate-700">
                          <Calendar className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                          <span>Built {ps.year_built}</span>
                        </div>
                      )}
                      {data.mls_number && (
                        <div className="flex items-center gap-2 text-slate-500 text-xs">
                          <Search className="w-3 h-3 flex-shrink-0" />
                          <span>MLS# {data.mls_number}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Right Panel — Detail Sections */}
              <div className="flex-1 overflow-y-auto p-6 space-y-5">
                {/* 1. Property Summary Card */}
                {ps && (
                  <div className="bg-white rounded-lg border border-slate-200 p-4">
                    <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2 mb-3">
                      <Home className="w-4 h-4 text-emerald-500" /> Property Summary
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
                      <SummaryField label="Purchase Price" value={fmtCAD(ps.purchase_price)} />
                      <SummaryField label="Appraised Value" value={fmtCAD(ps.appraised_value)} />
                      <SummaryField label="Property Type" value={ps.property_type} />
                      <SummaryField label="Year Built" value={ps.year_built != null ? String(ps.year_built) : '—'} />
                      <SummaryField label="Living Area" value={ps.living_area ? `${fmtNum(ps.living_area)} sqft` : '—'} />
                      <SummaryField label="Lot Size" value={ps.lot_size || '—'} />
                      <SummaryField label="Bedrooms" value={ps.bedrooms != null ? String(ps.bedrooms) : '—'} icon={<BedDouble className="w-3.5 h-3.5 text-slate-400" />} />
                      <SummaryField label="Bathrooms" value={ps.bathrooms != null ? String(ps.bathrooms) : '—'} icon={<Bath className="w-3.5 h-3.5 text-slate-400" />} />
                      <SummaryField label="Garages" value={ps.garages != null ? String(ps.garages) : '—'} icon={<Warehouse className="w-3.5 h-3.5 text-slate-400" />} />
                      <SummaryField label="Parking" value={ps.parking || '—'} icon={<Car className="w-3.5 h-3.5 text-slate-400" />} />
                    </div>
                  </div>
                )}

                {/* 2. Appraisal Recommendation Card */}
                <div className="bg-white rounded-lg border border-slate-200 p-4">
                  <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2 mb-3">
                    <Layers className="w-4 h-4 text-emerald-500" /> Appraisal Recommendation
                  </h3>
                  {/* Status Banner */}
                  <div className={`rounded-lg px-4 py-3 mb-3 flex items-center gap-2 ${
                    data.auto_appraisal_eligible
                      ? 'bg-green-50 border border-green-200 text-green-700'
                      : data.needs_physical_appraisal
                        ? 'bg-red-50 border border-red-200 text-red-700'
                        : 'bg-amber-50 border border-amber-200 text-amber-700'
                  }`}>
                    {data.auto_appraisal_eligible ? (
                      <CheckCircle className="w-5 h-5" />
                    ) : data.needs_physical_appraisal ? (
                      <XCircle className="w-5 h-5" />
                    ) : (
                      <AlertTriangle className="w-5 h-5" />
                    )}
                    <span className="font-medium">
                      {data.auto_appraisal_eligible
                        ? 'Auto-Appraisal Eligible'
                        : data.needs_physical_appraisal
                          ? 'Physical Appraisal Required'
                          : 'Manual Review Recommended'}
                    </span>
                  </div>
                  <p className="text-sm text-slate-700 mb-2">{data.auto_appraisal_recommendation}</p>
                  {data.risk_rationale && (
                    <p className="text-sm text-slate-500"><span className="font-medium text-slate-600">Risk Rationale:</span> {data.risk_rationale}</p>
                  )}
                  {data.physical_appraisal_reason && (
                    <p className="text-sm text-slate-500 mt-1"><span className="font-medium text-slate-600">Reason:</span> {data.physical_appraisal_reason}</p>
                  )}
                </div>

                {/* 3. Comparable Sales Card */}
                {sortedComps.length > 0 && (
                  <div className="bg-white rounded-lg border border-slate-200 p-4">
                    <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2 mb-3">
                      <BarChart3 className="w-4 h-4 text-emerald-500" /> Comparable Sales
                      <span className="text-xs font-normal text-slate-400">({sortedComps.length} found)</span>
                    </h3>

                    {compStats && (
                      <div className="flex gap-4 mb-3">
                        <div className="text-xs text-slate-500">
                          Avg Comp Price: <span className="font-medium text-slate-700">{fmtCAD(compStats.avg)}</span>
                        </div>
                        <div className="text-xs text-slate-500">
                          Subject Variance:{' '}
                          <span className={`font-medium ${compStats.variance > 5 ? 'text-red-600' : compStats.variance < -5 ? 'text-green-600' : 'text-slate-700'}`}>
                            {compStats.variance >= 0 ? '+' : ''}{compStats.variance.toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    )}

                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-slate-200">
                            <th className="text-left py-2 pr-3 text-xs font-medium text-slate-500 uppercase tracking-wide">Address</th>
                            <SortableHeader label="Sold Price" field="sold_price" current={compSort} onToggle={toggleSort} />
                            <SortableHeader label="Date" field="sold_date" current={compSort} onToggle={toggleSort} />
                            <SortableHeader label="Distance" field="distance_km" current={compSort} onToggle={toggleSort} />
                            <th className="text-left py-2 pr-3 text-xs font-medium text-slate-500 uppercase tracking-wide">Bed/Bath</th>
                            <th className="text-right py-2 pr-3 text-xs font-medium text-slate-500 uppercase tracking-wide">Area</th>
                            <th className="text-right py-2 pr-3 text-xs font-medium text-slate-500 uppercase tracking-wide">$/sqft</th>
                            <th className="text-right py-2 text-xs font-medium text-slate-500 uppercase tracking-wide">Similarity</th>
                          </tr>
                        </thead>
                        <tbody>
                          {sortedComps.map((c, i) => (
                            <tr key={i} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                              <td className="py-2 pr-3 text-slate-700 max-w-[180px] truncate" title={c.address}>{c.address}</td>
                              <td className="py-2 pr-3 text-slate-700">{fmtCAD(c.sold_price)}</td>
                              <td className="py-2 pr-3 text-slate-500">{c.sold_date}</td>
                              <td className="py-2 pr-3 text-slate-500">{c.distance_km.toFixed(1)} km</td>
                              <td className="py-2 pr-3 text-slate-500">{c.bedrooms}/{c.bathrooms}</td>
                              <td className="py-2 pr-3 text-right text-slate-500">{fmtNum(c.living_area)}</td>
                              <td className="py-2 pr-3 text-right text-slate-500">{fmtCAD(c.price_psf)}</td>
                              <td className="py-2 text-right">
                                <SimilarityBadge score={c.similarity_score} />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* 4. Market Trends Card */}
                {data.price_trend && (
                  <div className="bg-white rounded-lg border border-slate-200 p-4">
                    <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2 mb-3">
                      <TrendingUp className="w-4 h-4 text-emerald-500" /> Market Trends
                    </h3>
                    <div className="text-xs text-slate-500 mb-3">{data.price_trend.area_name}</div>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                      <div>
                        <div className="text-xs text-slate-500 mb-0.5">Current Avg Price</div>
                        <div className="text-sm font-semibold text-slate-800">{fmtCAD(data.price_trend.avg_price_current)}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500 mb-0.5">1 Year Ago</div>
                        <div className="text-sm font-semibold text-slate-800">{fmtCAD(data.price_trend.avg_price_1yr_ago)}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500 mb-0.5">3 Years Ago</div>
                        <div className="text-sm font-semibold text-slate-800">{fmtCAD(data.price_trend.avg_price_3yr_ago)}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500 mb-0.5">YoY Change</div>
                        <div className={`text-sm font-semibold flex items-center gap-1 ${data.price_trend.yoy_change_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {data.price_trend.yoy_change_pct >= 0 ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                          {fmtPct(data.price_trend.yoy_change_pct)}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500 mb-0.5">3yr CAGR</div>
                        <div className={`text-sm font-semibold flex items-center gap-1 ${data.price_trend.cagr_3yr_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {fmtPct(data.price_trend.cagr_3yr_pct)}
                        </div>
                      </div>
                    </div>
                    <div className="mt-3 flex items-center gap-2">
                      <span className="text-xs text-slate-500">Trend:</span>
                      <TrendIndicator direction={data.price_trend.trend_direction} />
                    </div>
                  </div>
                )}

                {/* 5. Property Features Card */}
                {groupedFeatures.size > 0 && (
                  <div className="bg-white rounded-lg border border-slate-200 p-4">
                    <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2 mb-3">
                      <Ruler className="w-4 h-4 text-emerald-500" /> Property Features
                    </h3>
                    <div className="space-y-4">
                      {Array.from(groupedFeatures.entries()).map(([category, features]) => (
                        <div key={category}>
                          <div className="text-xs font-semibold text-slate-600 uppercase tracking-wide mb-2">{category}</div>
                          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-4 gap-y-2">
                            {features.map((f, i) => (
                              <div key={i} className="flex flex-col">
                                <span className="text-xs text-slate-500">{f.feature}</span>
                                <span className="text-sm text-slate-700">{f.value}</span>
                                {f.data_point_source && (
                                  <span className="text-[10px] text-slate-400">Source: {f.data_point_source}</span>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 6. MLS Data Points Card */}
                {data.appraisal_data_points && Object.keys(data.appraisal_data_points).length > 0 && (
                  <div className="bg-white rounded-lg border border-slate-200 p-4">
                    <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2 mb-3">
                      <Search className="w-4 h-4 text-emerald-500" /> MLS Data Points
                    </h3>
                    {data.mls_listing_url && (
                      <div className="mb-3">
                        <a
                          href={data.mls_listing_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-emerald-600 hover:text-emerald-700 underline"
                        >
                          View MLS Listing →
                        </a>
                      </div>
                    )}
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-4 gap-y-2">
                      {Object.entries(data.appraisal_data_points).map(([key, value]) => (
                        <div key={key} className="flex flex-col">
                          <span className="text-xs text-slate-500">{key.replace(/_/g, ' ')}</span>
                          <span className="text-sm text-slate-700">{value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Footer */}
                <div className="text-center py-4">
                  <span className="text-xs text-slate-400">Powered by AI Analysis</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Helper Components
// ============================================================================

function SummaryField({ label, value, icon }: { label: string; value: string; icon?: React.ReactNode }) {
  return (
    <div className="flex flex-col">
      <span className="text-xs text-slate-500 mb-0.5">{label}</span>
      <span className="text-sm text-slate-700 flex items-center gap-1">
        {icon}
        {value}
      </span>
    </div>
  );
}

function SimilarityBadge({ score }: { score: number }) {
  let colorClass = 'bg-green-100 text-green-700';
  if (score < 60) colorClass = 'bg-red-100 text-red-700';
  else if (score < 80) colorClass = 'bg-amber-100 text-amber-700';

  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium ${colorClass}`}>
      {score}%
    </span>
  );
}

function SortableHeader({
  label,
  field,
  current,
  onToggle,
}: {
  label: string;
  field: SortField;
  current: { field: SortField; dir: SortDir };
  onToggle: (f: SortField) => void;
}) {
  const isActive = current.field === field;
  return (
    <th
      className="text-left py-2 pr-3 text-xs font-medium text-slate-500 uppercase tracking-wide cursor-pointer hover:text-slate-700 select-none"
      onClick={() => onToggle(field)}
    >
      <span className="flex items-center gap-1">
        {label}
        {isActive && (
          <span className="text-emerald-500">{current.dir === 'asc' ? '↑' : '↓'}</span>
        )}
      </span>
    </th>
  );
}

function TrendIndicator({ direction }: { direction: 'up' | 'down' | 'stable' }) {
  if (direction === 'up') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
        <TrendingUp className="w-3 h-3" /> Upward
      </span>
    );
  }
  if (direction === 'down') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
        <TrendingDown className="w-3 h-3" /> Downward
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600">
      <Minus className="w-3 h-3" /> Stable
    </span>
  );
}
