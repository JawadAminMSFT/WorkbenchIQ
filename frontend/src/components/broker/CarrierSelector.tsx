'use client';

import React, { useState, useEffect } from 'react';
import { Plus, Loader2, Package } from 'lucide-react';
import { getCarriers } from '../../lib/broker-api';
import type { CarrierProfile } from '../../lib/broker-types';

interface CarrierSelectorProps {
  selectedCarriers: string[];
  onCarriersChange: (carriers: string[]) => void;
  onGeneratePackage: () => void;
  generating: boolean;
  disabled: boolean;
}

export default function CarrierSelector({
  selectedCarriers,
  onCarriersChange,
  onGeneratePackage,
  generating,
  disabled,
}: CarrierSelectorProps) {
  const [carriers, setCarriers] = useState<CarrierProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddInput, setShowAddInput] = useState(false);
  const [newCarrierName, setNewCarrierName] = useState('');

  useEffect(() => {
    let cancelled = false;
    const fetchCarriers = async () => {
      setLoading(true);
      try {
        const data = await getCarriers();
        if (!cancelled) setCarriers(data);
      } catch (err) {
        console.error('Failed to fetch carriers:', err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetchCarriers();
    return () => {
      cancelled = true;
    };
  }, []);

  const toggleCarrier = (name: string) => {
    if (selectedCarriers.includes(name)) {
      onCarriersChange(selectedCarriers.filter((c) => c !== name));
    } else {
      onCarriersChange([...selectedCarriers, name]);
    }
  };

  const handleAddCarrier = () => {
    const name = newCarrierName.trim();
    if (!name) return;
    if (!selectedCarriers.includes(name)) {
      onCarriersChange([...selectedCarriers, name]);
    }
    setNewCarrierName('');
    setShowAddInput(false);
  };

  // Combine API carriers with any manually-added carriers
  const allCarrierNames = [
    ...new Set([
      ...carriers.map((c) => c.carrier_name),
      ...selectedCarriers.filter(
        (name) => !carriers.some((c) => c.carrier_name === name),
      ),
    ]),
  ];

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-4 text-slate-400">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span className="text-sm">Loading carriers…</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm font-medium text-slate-700">Select Carriers:</p>

      <div className="flex flex-wrap gap-3">
        {allCarrierNames.map((name) => (
          <label
            key={name}
            className="flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-200 hover:border-amber-300 cursor-pointer transition-colors"
          >
            <input
              type="checkbox"
              checked={selectedCarriers.includes(name)}
              onChange={() => toggleCarrier(name)}
              className="w-4 h-4 rounded border-slate-300 text-amber-600 focus:ring-amber-500"
            />
            <span className="text-sm text-slate-700">{name}</span>
          </label>
        ))}

        {showAddInput ? (
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={newCarrierName}
              onChange={(e) => setNewCarrierName(e.target.value)}
              placeholder="Carrier name"
              className="px-3 py-1.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleAddCarrier();
                if (e.key === 'Escape') setShowAddInput(false);
              }}
            />
            <button
              onClick={handleAddCarrier}
              className="text-sm text-amber-600 hover:text-amber-700 font-medium"
            >
              Add
            </button>
          </div>
        ) : (
          <button
            onClick={() => setShowAddInput(true)}
            className="flex items-center gap-1.5 px-3 py-2 text-sm text-amber-600 hover:text-amber-700 border border-dashed border-amber-300 rounded-lg hover:bg-amber-50 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            Add Carrier
          </button>
        )}
      </div>

      <button
        onClick={onGeneratePackage}
        disabled={disabled || generating || selectedCarriers.length === 0}
        className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 disabled:opacity-50 rounded-lg transition-colors"
      >
        {generating ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Package className="w-4 h-4" />
        )}
        {generating ? 'Generating…' : 'Generate Package'}
      </button>
    </div>
  );
}
