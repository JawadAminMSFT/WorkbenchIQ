'use client';

import React, { useState } from 'react';
import { AlertTriangle, DollarSign, Car, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import { DamageArea } from '@/lib/api';

interface DamageViewerProps {
  damageAreas: DamageArea[];
  totalEstimate: number;
  onDamageSelect?: (damage: DamageArea) => void;
  selectedDamageId?: string;
}

const severityConfig = {
  minor: {
    color: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    barColor: 'bg-yellow-500',
    icon: '🟡',
    label: 'Minor',
  },
  moderate: {
    color: 'bg-orange-100 text-orange-800 border-orange-300',
    barColor: 'bg-orange-500',
    icon: '🟠',
    label: 'Moderate',
  },
  severe: {
    color: 'bg-red-100 text-red-800 border-red-300',
    barColor: 'bg-red-500',
    icon: '🔴',
    label: 'Severe',
  },
  total_loss: {
    color: 'bg-gray-800 text-white border-gray-900',
    barColor: 'bg-gray-800',
    icon: '⚫',
    label: 'Total Loss',
  },
};

interface DamageCardProps {
  damage: DamageArea;
  isSelected: boolean;
  onClick: () => void;
  isExpanded: boolean;
  onToggleExpand: () => void;
}

const DamageCard: React.FC<DamageCardProps> = ({
  damage,
  isSelected,
  onClick,
  isExpanded,
  onToggleExpand,
}) => {
  const config = severityConfig[damage.severity];

  return (
    <div
      className={`border rounded-lg overflow-hidden transition-all duration-200 ${
        isSelected
          ? 'ring-2 ring-red-500 border-red-300'
          : 'border-gray-200 hover:border-gray-300'
      }`}
    >
      {/* Header */}
      <div
        className="p-4 cursor-pointer flex items-center justify-between gap-4"
        onClick={onClick}
      >
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className={`p-2 rounded-lg ${config.color}`}>
            <Car className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-gray-900 truncate">{damage.location}</h4>
            <div className="flex items-center gap-2 mt-1">
              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
                {config.label}
              </span>
              <span className="text-sm text-gray-500">
                {(damage.confidence * 100).toFixed(0)}% confidence
              </span>
            </div>
          </div>
        </div>
        <div className="text-right flex-shrink-0">
          <div className="text-lg font-semibold text-gray-900">
            ${damage.estimated_cost.toLocaleString()}
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggleExpand();
            }}
            className="text-gray-400 hover:text-gray-600 mt-1"
          >
            {isExpanded ? (
              <ChevronUp className="w-5 h-5" />
            ) : (
              <ChevronDown className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="px-4 pb-4 pt-0 border-t border-gray-100">
          <p className="text-gray-600 text-sm mt-3">{damage.description}</p>
          
          {/* Confidence Bar */}
          <div className="mt-4">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>AI Confidence</span>
              <span>{(damage.confidence * 100).toFixed(1)}%</span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full ${config.barColor} rounded-full transition-all duration-500`}
                style={{ width: `${damage.confidence * 100}%` }}
              />
            </div>
          </div>

          {/* Source Media Link */}
          {damage.source_media_id && (
            <button className="mt-4 text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1">
              <ExternalLink className="w-4 h-4" />
              View Source Evidence
            </button>
          )}
        </div>
      )}
    </div>
  );
};

// Vehicle damage diagram component
interface VehicleDiagramProps {
  damageAreas: DamageArea[];
  onAreaClick?: (damage: DamageArea) => void;
  selectedDamageId?: string;
}

const VehicleDiagram: React.FC<VehicleDiagramProps> = ({
  damageAreas,
  onAreaClick,
  selectedDamageId,
}) => {
  // Map damage locations to diagram positions
  const locationToPosition: Record<string, { x: number; y: number; label: string }> = {
    'front_bumper': { x: 50, y: 10, label: 'Front Bumper' },
    'front_left_fender': { x: 20, y: 25, label: 'Front Left Fender' },
    'front_right_fender': { x: 80, y: 25, label: 'Front Right Fender' },
    'hood': { x: 50, y: 25, label: 'Hood' },
    'windshield': { x: 50, y: 35, label: 'Windshield' },
    'roof': { x: 50, y: 50, label: 'Roof' },
    'left_door_front': { x: 15, y: 45, label: 'Left Front Door' },
    'left_door_rear': { x: 15, y: 60, label: 'Left Rear Door' },
    'right_door_front': { x: 85, y: 45, label: 'Right Front Door' },
    'right_door_rear': { x: 85, y: 60, label: 'Right Rear Door' },
    'rear_bumper': { x: 50, y: 90, label: 'Rear Bumper' },
    'trunk': { x: 50, y: 80, label: 'Trunk' },
    'rear_left_quarter': { x: 20, y: 75, label: 'Rear Left Quarter' },
    'rear_right_quarter': { x: 80, y: 75, label: 'Rear Right Quarter' },
  };

  const getDamagePosition = (damage: DamageArea) => {
    // Try exact match first
    const normalizedLocation = damage.location.toLowerCase().replace(/\s+/g, '_');
    if (locationToPosition[normalizedLocation]) {
      return locationToPosition[normalizedLocation];
    }
    
    // Try partial match
    for (const [key, value] of Object.entries(locationToPosition)) {
      if (normalizedLocation.includes(key) || key.includes(normalizedLocation)) {
        return value;
      }
    }
    
    // Default center position
    return { x: 50, y: 50, label: damage.location };
  };

  return (
    <div className="relative bg-gray-50 rounded-xl p-6">
      <h4 className="text-sm font-medium text-gray-700 mb-4">Vehicle Damage Map</h4>
      
      {/* Vehicle outline SVG */}
      <div className="relative aspect-[3/4] max-w-xs mx-auto">
        <svg viewBox="0 0 100 100" className="w-full h-full">
          {/* Simple car outline - top view */}
          <path
            d="M30 15 Q50 5 70 15 L75 30 L80 45 L80 75 L75 85 Q50 95 25 85 L20 75 L20 45 L25 30 Z"
            fill="none"
            stroke="#d1d5db"
            strokeWidth="2"
          />
          {/* Windshield */}
          <path
            d="M35 32 Q50 28 65 32 L62 40 Q50 38 38 40 Z"
            fill="none"
            stroke="#d1d5db"
            strokeWidth="1"
          />
          {/* Rear window */}
          <path
            d="M35 75 Q50 78 65 75 L62 68 Q50 70 38 68 Z"
            fill="none"
            stroke="#d1d5db"
            strokeWidth="1"
          />
        </svg>

        {/* Damage indicators */}
        {damageAreas.map((damage) => {
          const position = getDamagePosition(damage);
          const config = severityConfig[damage.severity];
          const isSelected = damage.area_id === selectedDamageId;

          return (
            <button
              key={damage.area_id}
              onClick={() => onAreaClick?.(damage)}
              className={`absolute transform -translate-x-1/2 -translate-y-1/2 transition-all duration-200 ${
                isSelected ? 'scale-125 z-10' : 'hover:scale-110'
              }`}
              style={{ left: `${position.x}%`, top: `${position.y}%` }}
              title={`${damage.location}: ${config.label} - $${damage.estimated_cost.toLocaleString()}`}
            >
              <div
                className={`w-6 h-6 rounded-full ${config.barColor} flex items-center justify-center text-white text-xs font-bold shadow-lg ${
                  isSelected ? 'ring-2 ring-offset-2 ring-red-500' : ''
                }`}
              >
                {damageAreas.indexOf(damage) + 1}
              </div>
            </button>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex justify-center gap-4 mt-6 flex-wrap">
        {Object.entries(severityConfig).map(([key, config]) => (
          <div key={key} className="flex items-center gap-1.5">
            <div className={`w-3 h-3 rounded-full ${config.barColor}`} />
            <span className="text-xs text-gray-600">{config.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const DamageViewer: React.FC<DamageViewerProps> = ({
  damageAreas,
  totalEstimate,
  onDamageSelect,
  selectedDamageId,
}) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'severity' | 'cost'>('severity');

  const severityOrder = { total_loss: 0, severe: 1, moderate: 2, minor: 3 };

  const sortedDamageAreas = [...damageAreas].sort((a, b) => {
    if (sortBy === 'severity') {
      return severityOrder[a.severity] - severityOrder[b.severity];
    }
    return b.estimated_cost - a.estimated_cost;
  });

  const severityCounts = damageAreas.reduce(
    (acc, d) => {
      acc[d.severity] = (acc[d.severity] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Vehicle Diagram */}
      <div className="lg:col-span-1">
        <VehicleDiagram
          damageAreas={damageAreas}
          onAreaClick={onDamageSelect}
          selectedDamageId={selectedDamageId}
        />

        {/* Summary Stats */}
        <div className="mt-6 grid grid-cols-2 gap-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-gray-600 text-sm">
              <AlertTriangle className="w-4 h-4" />
              Damage Areas
            </div>
            <div className="text-2xl font-bold text-gray-900 mt-1">
              {damageAreas.length}
            </div>
          </div>
          <div className="bg-red-50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-red-600 text-sm">
              <DollarSign className="w-4 h-4" />
              Total Estimate
            </div>
            <div className="text-2xl font-bold text-red-700 mt-1">
              ${totalEstimate.toLocaleString()}
            </div>
          </div>
        </div>

        {/* Severity Breakdown */}
        <div className="mt-4 bg-gray-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-700 mb-3">By Severity</h4>
          <div className="space-y-2">
            {Object.entries(severityConfig).map(([key, config]) => {
              const count = severityCounts[key] || 0;
              const percentage = damageAreas.length > 0 ? (count / damageAreas.length) * 100 : 0;
              return (
                <div key={key} className="flex items-center gap-2">
                  <span className="text-xs w-20 text-gray-600">{config.label}</span>
                  <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${config.barColor} rounded-full`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 w-8 text-right">{count}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Damage List */}
      <div className="lg:col-span-2">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Detected Damage Areas
          </h3>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'severity' | 'cost')}
            className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-red-500"
          >
            <option value="severity">Sort by Severity</option>
            <option value="cost">Sort by Cost</option>
          </select>
        </div>

        {damageAreas.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-xl">
            <Car className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p className="text-gray-500">No damage areas detected</p>
            <p className="text-sm text-gray-400 mt-1">
              Upload vehicle images or video to analyze damage
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {sortedDamageAreas.map((damage) => (
              <DamageCard
                key={damage.area_id}
                damage={damage}
                isSelected={damage.area_id === selectedDamageId}
                onClick={() => onDamageSelect?.(damage)}
                isExpanded={expandedId === damage.area_id}
                onToggleExpand={() =>
                  setExpandedId(expandedId === damage.area_id ? null : damage.area_id)
                }
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DamageViewer;
