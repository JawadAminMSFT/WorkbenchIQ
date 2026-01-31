'use client';

import { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check, ClipboardList, Stethoscope, Landmark } from 'lucide-react';
import { usePersona } from '@/lib/PersonaContext';
import { getEnabledPersonas, PersonaConfig, PersonaId, PERSONAS } from '@/lib/personas';
import clsx from 'clsx';

// UI display names that map to actual persona IDs
const PERSONA_UI_LABELS: Record<PersonaId, string> = {
  underwriting: 'Life & Health Underwriting',
  life_health_claims: 'Life & Health Claims',
  automotive_claims: 'Automotive Claims',
  property_casualty_claims: 'Property & Casualty Claims',
  mortgage: 'Mortgage Underwriting',
};

// Placeholder personas that don't exist in the backend yet (shown as disabled)
interface PlaceholderPersona {
  id: string;
  label: string;
  enabled: false;
}

const PLACEHOLDER_PERSONAS: PlaceholderPersona[] = [
  { id: 'securities_lending', label: 'Securities Lending', enabled: false },
];

// Group personas into categories for the dropdown
interface PersonaGroup {
  id: string;
  label: string;
  icon: typeof ClipboardList;
  personaIds: PersonaId[];
  placeholders?: PlaceholderPersona[];
}

const PERSONA_GROUPS: PersonaGroup[] = [
  {
    id: 'underwriting',
    label: 'Underwriting',
    icon: ClipboardList,
    personaIds: ['underwriting', 'mortgage'],
  },
  {
    id: 'claims',
    label: 'Claims',
    icon: Stethoscope,
    personaIds: ['life_health_claims', 'automotive_claims'],
  },
  {
    id: 'wealth',
    label: 'Wealth',
    icon: Landmark,
    personaIds: [],
    placeholders: [PLACEHOLDER_PERSONAS.find(p => p.id === 'securities_lending')!],
  },
];

export default function PersonaSelector() {
  const { currentPersona, personaConfig, setPersona } = usePersona();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  const enabledPersonas = getEnabledPersonas();
  const enabledPersonaIds = new Set(enabledPersonas.map(p => p.id));

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectPersona = (persona: PersonaConfig) => {
    if (persona.enabled) {
      setPersona(persona.id);
      setIsOpen(false);
    }
  };

  // Get the current persona's UI label
  const currentUILabel = PERSONA_UI_LABELS[currentPersona] || personaConfig.name;
  const IconComponent = personaConfig.icon;

  // Filter groups to only show those with at least one enabled persona OR placeholders
  const visibleGroups = PERSONA_GROUPS.map(group => ({
    ...group,
    personas: enabledPersonas.filter(p => group.personaIds.includes(p.id)),
  })).filter(group => group.personas.length > 0 || (group.placeholders && group.placeholders.length > 0));

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Selector Button - matches Application Selector styling */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 bg-slate-50 hover:bg-slate-100 rounded-lg border border-slate-200 transition-colors"
      >
        <IconComponent className="w-4 h-4 text-slate-600" />
        <span className="text-sm font-medium text-slate-700">{currentUILabel}</span>
        <ChevronDown 
          className={clsx(
            'w-4 h-4 text-slate-500 transition-transform',
            isOpen && 'rotate-180'
          )} 
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute top-full left-0 mt-1 w-72 bg-white rounded-lg shadow-lg border border-slate-200 py-2 z-20">
            {visibleGroups.map((group, groupIndex) => {
              const GroupIcon = group.icon;
              return (
                <div key={group.id}>
                  {/* Group Header */}
                  <div className="px-4 py-1.5 flex items-center gap-2">
                    <GroupIcon className="w-4 h-4 text-slate-400" />
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide">
                      {group.label}
                    </span>
                  </div>
                  
                  {/* Group Items */}
                  {group.personas.map((persona) => {
                    const PersonaIcon = persona.icon;
                    const uiLabel = PERSONA_UI_LABELS[persona.id] || persona.name;
                    return (
                      <button
                        key={persona.id}
                        onClick={() => handleSelectPersona(persona)}
                        className={clsx(
                          'w-full text-left px-4 py-2 text-sm transition-colors flex items-center gap-3 pl-8',
                          'hover:bg-slate-50 cursor-pointer',
                          currentPersona === persona.id && 'bg-indigo-50 text-indigo-700'
                        )}
                      >
                        <PersonaIcon className="w-4 h-4 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{uiLabel}</span>
                            {currentPersona === persona.id && (
                              <Check className="w-3 h-3" />
                            )}
                          </div>
                        </div>
                      </button>
                    );
                  })}
                  
                  {/* Placeholder Items (Coming Soon) */}
                  {group.placeholders?.map((placeholder) => (
                    <div
                      key={placeholder.id}
                      className="w-full text-left px-4 py-2 text-sm flex items-center gap-3 pl-8 opacity-50 cursor-not-allowed"
                    >
                      <Landmark className="w-4 h-4 flex-shrink-0 text-slate-400" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-slate-400">{placeholder.label}</span>
                          <span className="text-[10px] px-1.5 py-0.5 bg-slate-100 text-slate-500 rounded font-medium">
                            Coming Soon
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {/* Divider between groups */}
                  {groupIndex < visibleGroups.length - 1 && (
                    <div className="my-2 border-t border-slate-100" />
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
