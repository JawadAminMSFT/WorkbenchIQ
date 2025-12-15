/**
 * Persona definitions and types for WorkbenchIQ.
 * This module defines the available personas and their UI configurations.
 */

import { ClipboardList, HeartPulse, Home, Car, Stethoscope } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

export type PersonaId = 'underwriting' | 'life_health_claims' | 'property_casualty_claims' | 'mortgage';

export interface Persona {
  id: PersonaId;
  name: string;
  description: string;
  icon: LucideIcon;
  color: string;
  enabled: boolean;
}

export interface PersonaConfig extends Persona {
  // UI-specific settings
  primaryColor: string;
  secondaryColor: string;
  accentColor: string;
}

/**
 * Persona registry with UI configurations
 */
export const PERSONAS: Record<PersonaId, PersonaConfig> = {
  underwriting: {
    id: 'underwriting',
    name: 'Underwriting',
    description: 'Life insurance underwriting workbench for processing applications and medical documents',
    icon: ClipboardList,
    color: '#6366f1',
    enabled: true,
    primaryColor: '#6366f1', // Indigo
    secondaryColor: '#818cf8',
    accentColor: '#4f46e5',
  },
  life_health_claims: {
    id: 'life_health_claims',
    name: 'Life & Health Claims',
    description: 'Health insurance claims processing workbench for medical claims, eligibility verification, and benefits adjudication',
    icon: Stethoscope,
    color: '#6366f1',
    enabled: true,
    primaryColor: '#6366f1', // Indigo
    secondaryColor: '#818cf8',
    accentColor: '#4f46e5',
  },
  property_casualty_claims: {
    id: 'property_casualty_claims',
    name: 'Property & Casualty Claims',
    description: 'P&C claims processing workbench for auto, liability, and property damage claims',
    icon: Car,
    color: '#6366f1',
    enabled: true,
    primaryColor: '#6366f1', // Indigo
    secondaryColor: '#818cf8',
    accentColor: '#4f46e5',
  },
  mortgage: {
    id: 'mortgage',
    name: 'Mortgage',
    description: 'Mortgage underwriting workbench for loan applications and property documents',
    icon: Home,
    color: '#6366f1',
    enabled: false,
    primaryColor: '#6366f1', // Indigo
    secondaryColor: '#818cf8',
    accentColor: '#4f46e5',
  },
};

/**
 * Get persona configuration by ID
 */
export function getPersona(id: PersonaId): PersonaConfig {
  return PERSONAS[id];
}

/**
 * Get all available personas
 */
export function getAllPersonas(): PersonaConfig[] {
  return Object.values(PERSONAS);
}

/**
 * Get only enabled personas
 */
export function getEnabledPersonas(): PersonaConfig[] {
  return Object.values(PERSONAS).filter(p => p.enabled);
}

/**
 * Default persona
 */
export const DEFAULT_PERSONA: PersonaId = 'underwriting';

/**
 * Local storage key for persisting selected persona
 */
export const PERSONA_STORAGE_KEY = 'workbenchiq-persona';
