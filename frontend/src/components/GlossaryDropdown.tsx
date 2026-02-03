'use client';

import { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import { Book, ChevronDown, Search, X } from 'lucide-react';
import { usePersona } from '@/lib/PersonaContext';
import { searchGlossary, getGlossary } from '@/lib/api';
import type { GlossaryTerm, PersonaGlossary } from '@/lib/api';

interface GlossaryDropdownProps {
  className?: string;
}

export default function GlossaryDropdown({ className = '' }: GlossaryDropdownProps) {
  const { currentPersona, personaConfig } = usePersona();
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<GlossaryTerm[]>([]);
  const [allTerms, setAllTerms] = useState<GlossaryTerm[]>([]);
  const [loading, setLoading] = useState(false);
  const [glossaryInfo, setGlossaryInfo] = useState<{ name: string; count: number } | null>(null);
  const [letterFilter, setLetterFilter] = useState<string | null>(null);
  
  const dropdownRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

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

  // Load glossary when persona changes or dropdown opens
  useEffect(() => {
    if (!isOpen) return;
    
    async function loadGlossary() {
      try {
        setLoading(true);
        const glossary = await getGlossary(currentPersona);
        setGlossaryInfo({ name: glossary.name, count: glossary.total_terms });
        
        // Flatten all terms for display
        const terms: GlossaryTerm[] = [];
        glossary.categories.forEach(cat => {
          cat.terms.forEach(term => {
            terms.push({
              ...term,
              category: cat.name,
              category_id: cat.id,
            });
          });
        });
        // Sort alphabetically
        terms.sort((a, b) => a.abbreviation.localeCompare(b.abbreviation));
        setAllTerms(terms);
      } catch (err) {
        console.error('Failed to load glossary:', err);
      } finally {
        setLoading(false);
      }
    }
    
    loadGlossary();
  }, [currentPersona, isOpen]);

  // Search effect with debounce
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    const timeoutId = setTimeout(async () => {
      try {
        const result = await searchGlossary(currentPersona, searchQuery);
        setSearchResults(result.results);
      } catch (err) {
        console.error('Search failed:', err);
      }
    }, 200);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, currentPersona]);

  // Get available letters for quick navigation
  const availableLetters = useMemo(() => {
    const letters = new Set<string>();
    allTerms.forEach(term => {
      const firstChar = term.abbreviation.charAt(0).toUpperCase();
      if (/[A-Z0-9]/.test(firstChar)) {
        letters.add(firstChar);
      }
    });
    return Array.from(letters).sort();
  }, [allTerms]);

  // Filter terms by letter
  const filteredTerms = useMemo(() => {
    if (!letterFilter) return allTerms.slice(0, 50); // Show first 50 if no filter
    return allTerms.filter(term =>
      term.abbreviation.toUpperCase().startsWith(letterFilter)
    );
  }, [allTerms, letterFilter]);

  // Terms to display (search results or filtered terms)
  const displayTerms = searchQuery.trim() ? searchResults : filteredTerms;

  // Focus search input when opened
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen]);

  const handleToggle = useCallback(() => {
    setIsOpen(prev => !prev);
    if (!isOpen) {
      setSearchQuery('');
      setLetterFilter(null);
    }
  }, [isOpen]);

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* Toggle Button */}
      <button
        onClick={handleToggle}
        className="flex items-center gap-2 px-3 py-2 text-sm bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors shadow-sm"
        title="Glossary - Domain Terminology Reference"
      >
        <Book className="w-4 h-4 text-indigo-600" />
        <span className="hidden sm:inline text-slate-700">Glossary</span>
        <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-96 max-h-[500px] bg-white rounded-lg shadow-xl border border-slate-200 z-50 overflow-hidden">
          {/* Header */}
          <div className="p-3 bg-slate-50 border-b border-slate-200">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Book className="w-4 h-4 text-indigo-600" />
                <span className="font-medium text-slate-800">
                  {glossaryInfo?.name || personaConfig.name} Glossary
                </span>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="text-xs text-slate-500 mb-2">
              {glossaryInfo ? `${glossaryInfo.count} terms` : 'Loading...'}
            </div>
            
            {/* Search Input */}
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setLetterFilter(null);
                }}
                placeholder="Search terms..."
                className="w-full pl-8 pr-3 py-1.5 text-sm border border-slate-200 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          {/* Letter Navigation */}
          {!searchQuery && availableLetters.length > 0 && (
            <div className="px-3 py-2 border-b border-slate-100 flex flex-wrap gap-1">
              <button
                onClick={() => setLetterFilter(null)}
                className={`px-1.5 py-0.5 text-xs rounded transition-colors ${
                  letterFilter === null
                    ? 'bg-indigo-600 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                All
              </button>
              {availableLetters.map(letter => (
                <button
                  key={letter}
                  onClick={() => setLetterFilter(letter)}
                  className={`px-1.5 py-0.5 text-xs rounded transition-colors ${
                    letterFilter === letter
                      ? 'bg-indigo-600 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {letter}
                </button>
              ))}
            </div>
          )}

          {/* Terms List */}
          <div className="max-h-80 overflow-y-auto">
            {loading ? (
              <div className="p-4 text-center text-slate-500 text-sm">
                Loading glossary...
              </div>
            ) : displayTerms.length === 0 ? (
              <div className="p-4 text-center text-slate-500 text-sm">
                {searchQuery ? `No terms matching "${searchQuery}"` : 'No terms available'}
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {displayTerms.map((term) => (
                  <div
                    key={term.abbreviation}
                    className="px-3 py-2 hover:bg-slate-50 cursor-default"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="font-mono font-semibold text-indigo-700">
                          {term.abbreviation}
                        </span>
                        <span className="mx-2 text-slate-400">—</span>
                        <span className="text-slate-700">{term.meaning}</span>
                      </div>
                    </div>
                    {term.context && (
                      <div className="text-xs text-slate-500 mt-0.5 ml-0">
                        {term.context}
                      </div>
                    )}
                    {term.category && !searchQuery && (
                      <div className="text-xs text-slate-400 mt-0.5">
                        Category: {term.category}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-3 py-2 bg-slate-50 border-t border-slate-200 text-xs text-slate-500 text-center">
            {searchQuery
              ? `${searchResults.length} results`
              : letterFilter
              ? `${filteredTerms.length} terms starting with "${letterFilter}"`
              : `Showing first ${Math.min(50, allTerms.length)} of ${allTerms.length} terms`}
          </div>
        </div>
      )}
    </div>
  );
}
