'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { PersonaId, PersonaConfig, PERSONAS, DEFAULT_PERSONA, PERSONA_STORAGE_KEY } from './personas';

interface PersonaContextType {
  currentPersona: PersonaId;
  personaConfig: PersonaConfig;
  setPersona: (persona: PersonaId) => void;
  isLoading: boolean;
}

const PersonaContext = createContext<PersonaContextType | undefined>(undefined);

interface PersonaProviderProps {
  children: React.ReactNode;
}

export function PersonaProvider({ children }: PersonaProviderProps) {
  const [currentPersona, setCurrentPersona] = useState<PersonaId>(DEFAULT_PERSONA);
  const [isLoading, setIsLoading] = useState(true);

  // Load persona from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(PERSONA_STORAGE_KEY);
      if (stored && stored in PERSONAS) {
        setCurrentPersona(stored as PersonaId);
      }
    } catch (e) {
      console.warn('Failed to load persona from localStorage:', e);
    }
    setIsLoading(false);
  }, []);

  // Save persona to localStorage when it changes
  const setPersona = useCallback((persona: PersonaId) => {
    setCurrentPersona(persona);
    try {
      localStorage.setItem(PERSONA_STORAGE_KEY, persona);
    } catch (e) {
      console.warn('Failed to save persona to localStorage:', e);
    }
  }, []);

  const personaConfig = PERSONAS[currentPersona];

  return (
    <PersonaContext.Provider
      value={{
        currentPersona,
        personaConfig,
        setPersona,
        isLoading,
      }}
    >
      {children}
    </PersonaContext.Provider>
  );
}

export function usePersona(): PersonaContextType {
  const context = useContext(PersonaContext);
  if (context === undefined) {
    throw new Error('usePersona must be used within a PersonaProvider');
  }
  return context;
}

export { PersonaContext };
