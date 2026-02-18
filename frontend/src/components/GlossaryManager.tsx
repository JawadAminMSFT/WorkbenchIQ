'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Search,
  Plus,
  Trash2,
  Edit2,
  Save,
  X,
  ChevronDown,
  ChevronRight,
  Book,
  FolderPlus,
  AlertCircle,
  Check,
  Loader2,
} from 'lucide-react';
import {
  getGlossary,
  searchGlossary,
  createGlossaryTerm,
  updateGlossaryTerm,
  deleteGlossaryTerm,
  createGlossaryCategory,
  updateGlossaryCategory,
  deleteGlossaryCategory,
} from '@/lib/api';
import type { PersonaGlossary, GlossaryCategory, GlossaryTerm } from '@/lib/api';

interface GlossaryManagerProps {
  persona: string;
  personaName: string;
}

export default function GlossaryManager({ persona, personaName }: GlossaryManagerProps) {
  // State
  const [glossary, setGlossary] = useState<PersonaGlossary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<GlossaryTerm[] | null>(null);
  const [searching, setSearching] = useState(false);

  // Expanded categories
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  // Edit state
  const [editingTerm, setEditingTerm] = useState<string | null>(null);
  const [editingCategory, setEditingCategory] = useState<string | null>(null);
  const [editFormData, setEditFormData] = useState<Partial<GlossaryTerm>>({});
  const [editCategoryName, setEditCategoryName] = useState('');

  // New term form
  const [showNewTermForm, setShowNewTermForm] = useState<string | null>(null);
  const [newTermData, setNewTermData] = useState<Partial<GlossaryTerm>>({
    abbreviation: '',
    meaning: '',
    context: '',
  });

  // New category form
  const [showNewCategoryForm, setShowNewCategoryForm] = useState(false);
  const [newCategoryData, setNewCategoryData] = useState({ id: '', name: '' });

  // Alphabetic filter
  const [letterFilter, setLetterFilter] = useState<string | null>(null);

  // Load glossary
  const loadGlossary = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getGlossary(persona);
      setGlossary(data);
      // Expand first category by default
      if (data.categories.length > 0) {
        setExpandedCategories(new Set([data.categories[0].id]));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load glossary');
    } finally {
      setLoading(false);
    }
  }, [persona]);

  useEffect(() => {
    loadGlossary();
  }, [loadGlossary]);

  // Search handling
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }

    const timeoutId = setTimeout(async () => {
      try {
        setSearching(true);
        const result = await searchGlossary(persona, searchQuery);
        setSearchResults(result.results);
      } catch (err) {
        console.error('Search failed:', err);
      } finally {
        setSearching(false);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, persona]);

  // Filtered categories based on letter filter
  const filteredCategories = useMemo(() => {
    if (!glossary) return [];
    if (!letterFilter) return glossary.categories;

    return glossary.categories.map(cat => ({
      ...cat,
      terms: cat.terms.filter(term =>
        term.abbreviation.toUpperCase().startsWith(letterFilter)
      ),
    })).filter(cat => cat.terms.length > 0);
  }, [glossary, letterFilter]);

  // Get unique first letters for filter
  const availableLetters = useMemo(() => {
    if (!glossary) return [];
    const letters = new Set<string>();
    glossary.categories.forEach(cat => {
      cat.terms.forEach(term => {
        const firstChar = term.abbreviation.charAt(0).toUpperCase();
        if (/[A-Z]/.test(firstChar)) {
          letters.add(firstChar);
        }
      });
    });
    return Array.from(letters).sort();
  }, [glossary]);

  // Toggle category expansion
  const toggleCategory = (categoryId: string) => {
    setExpandedCategories(prev => {
      const newSet = new Set(prev);
      if (newSet.has(categoryId)) {
        newSet.delete(categoryId);
      } else {
        newSet.add(categoryId);
      }
      return newSet;
    });
  };

  // Show message temporarily
  const showMessage = (message: string, isError: boolean = false) => {
    if (isError) {
      setError(message);
      setTimeout(() => setError(null), 5000);
    } else {
      setSuccess(message);
      setTimeout(() => setSuccess(null), 3000);
    }
  };

  // Add new term
  const handleAddTerm = async (categoryId: string) => {
    if (!newTermData.abbreviation || !newTermData.meaning) {
      showMessage('Abbreviation and meaning are required', true);
      return;
    }

    try {
      setSaving(true);
      await createGlossaryTerm(persona, categoryId, {
        abbreviation: newTermData.abbreviation,
        meaning: newTermData.meaning,
        context: newTermData.context || undefined,
      });
      showMessage(`Added term "${newTermData.abbreviation}"`);
      setShowNewTermForm(null);
      setNewTermData({ abbreviation: '', meaning: '', context: '' });
      await loadGlossary();
    } catch (err) {
      showMessage(err instanceof Error ? err.message : 'Failed to add term', true);
    } finally {
      setSaving(false);
    }
  };

  // Update term
  const handleUpdateTerm = async (abbreviation: string) => {
    if (!editFormData.meaning) {
      showMessage('Meaning is required', true);
      return;
    }

    try {
      setSaving(true);
      await updateGlossaryTerm(persona, abbreviation, {
        meaning: editFormData.meaning,
        context: editFormData.context || undefined,
      });
      showMessage(`Updated term "${abbreviation}"`);
      setEditingTerm(null);
      setEditFormData({});
      await loadGlossary();
    } catch (err) {
      showMessage(err instanceof Error ? err.message : 'Failed to update term', true);
    } finally {
      setSaving(false);
    }
  };

  // Delete term
  const handleDeleteTerm = async (abbreviation: string) => {
    if (!confirm(`Delete term "${abbreviation}"?`)) return;

    try {
      setSaving(true);
      await deleteGlossaryTerm(persona, abbreviation);
      showMessage(`Deleted term "${abbreviation}"`);
      await loadGlossary();
    } catch (err) {
      showMessage(err instanceof Error ? err.message : 'Failed to delete term', true);
    } finally {
      setSaving(false);
    }
  };

  // Add category
  const handleAddCategory = async () => {
    if (!newCategoryData.id || !newCategoryData.name) {
      showMessage('Category ID and name are required', true);
      return;
    }

    try {
      setSaving(true);
      await createGlossaryCategory(persona, newCategoryData.id, newCategoryData.name);
      showMessage(`Added category "${newCategoryData.name}"`);
      setShowNewCategoryForm(false);
      setNewCategoryData({ id: '', name: '' });
      await loadGlossary();
    } catch (err) {
      showMessage(err instanceof Error ? err.message : 'Failed to add category', true);
    } finally {
      setSaving(false);
    }
  };

  // Update category
  const handleUpdateCategory = async (categoryId: string) => {
    if (!editCategoryName) {
      showMessage('Category name is required', true);
      return;
    }

    try {
      setSaving(true);
      await updateGlossaryCategory(persona, categoryId, editCategoryName);
      showMessage(`Updated category "${editCategoryName}"`);
      setEditingCategory(null);
      setEditCategoryName('');
      await loadGlossary();
    } catch (err) {
      showMessage(err instanceof Error ? err.message : 'Failed to update category', true);
    } finally {
      setSaving(false);
    }
  };

  // Delete category
  const handleDeleteCategory = async (categoryId: string, termCount: number) => {
    if (termCount > 0) {
      showMessage('Cannot delete category with terms. Delete all terms first.', true);
      return;
    }
    if (!confirm(`Delete category "${categoryId}"?`)) return;

    try {
      setSaving(true);
      await deleteGlossaryCategory(persona, categoryId);
      showMessage(`Deleted category`);
      await loadGlossary();
    } catch (err) {
      showMessage(err instanceof Error ? err.message : 'Failed to delete category', true);
    } finally {
      setSaving(false);
    }
  };

  // Start editing term
  const startEditingTerm = (term: GlossaryTerm) => {
    setEditingTerm(term.abbreviation);
    setEditFormData({
      meaning: term.meaning,
      context: term.context || '',
    });
  };

  // Render term row
  const renderTermRow = (term: GlossaryTerm, categoryId: string) => {
    const isEditing = editingTerm === term.abbreviation;

    if (isEditing) {
      return (
        <tr key={term.abbreviation} className="bg-indigo-50">
          <td className="px-4 py-2">
            <span className="font-mono font-semibold text-indigo-700">
              {term.abbreviation}
            </span>
          </td>
          <td className="px-4 py-2">
            <input
              type="text"
              value={editFormData.meaning || ''}
              onChange={(e) => setEditFormData(prev => ({ ...prev, meaning: e.target.value }))}
              className="w-full px-2 py-1 border border-slate-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Meaning"
            />
          </td>
          <td className="px-4 py-2">
            <input
              type="text"
              value={editFormData.context || ''}
              onChange={(e) => setEditFormData(prev => ({ ...prev, context: e.target.value }))}
              className="w-full px-2 py-1 border border-slate-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Context (optional)"
            />
          </td>
          <td className="px-4 py-2 text-right">
            <button
              onClick={() => handleUpdateTerm(term.abbreviation)}
              disabled={saving}
              className="text-green-600 hover:text-green-800 p-1 mr-1"
              title="Save"
            >
              <Save className="w-4 h-4" />
            </button>
            <button
              onClick={() => {
                setEditingTerm(null);
                setEditFormData({});
              }}
              className="text-slate-500 hover:text-slate-700 p-1"
              title="Cancel"
            >
              <X className="w-4 h-4" />
            </button>
          </td>
        </tr>
      );
    }

    return (
      <tr key={term.abbreviation} className="hover:bg-slate-50">
        <td className="px-4 py-2">
          <span className="font-mono font-semibold text-slate-800">
            {term.abbreviation}
          </span>
        </td>
        <td className="px-4 py-2 text-slate-700">{term.meaning}</td>
        <td className="px-4 py-2 text-slate-500 text-sm">{term.context || '-'}</td>
        <td className="px-4 py-2 text-right">
          <button
            onClick={() => startEditingTerm(term)}
            className="text-indigo-600 hover:text-indigo-800 p-1 mr-1"
            title="Edit"
          >
            <Edit2 className="w-4 h-4" />
          </button>
          <button
            onClick={() => handleDeleteTerm(term.abbreviation)}
            disabled={saving}
            className="text-red-500 hover:text-red-700 p-1"
            title="Delete"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </td>
      </tr>
    );
  };

  // Render new term form
  const renderNewTermForm = (categoryId: string) => {
    if (showNewTermForm !== categoryId) return null;

    return (
      <tr className="bg-green-50">
        <td className="px-4 py-2">
          <input
            type="text"
            value={newTermData.abbreviation || ''}
            onChange={(e) => setNewTermData(prev => ({ ...prev, abbreviation: e.target.value }))}
            className="w-full px-2 py-1 border border-slate-300 rounded text-sm font-mono focus:outline-none focus:ring-2 focus:ring-green-500"
            placeholder="Abbreviation"
            autoFocus
          />
        </td>
        <td className="px-4 py-2">
          <input
            type="text"
            value={newTermData.meaning || ''}
            onChange={(e) => setNewTermData(prev => ({ ...prev, meaning: e.target.value }))}
            className="w-full px-2 py-1 border border-slate-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
            placeholder="Meaning"
          />
        </td>
        <td className="px-4 py-2">
          <input
            type="text"
            value={newTermData.context || ''}
            onChange={(e) => setNewTermData(prev => ({ ...prev, context: e.target.value }))}
            className="w-full px-2 py-1 border border-slate-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
            placeholder="Context (optional)"
          />
        </td>
        <td className="px-4 py-2 text-right">
          <button
            onClick={() => handleAddTerm(categoryId)}
            disabled={saving}
            className="text-green-600 hover:text-green-800 p-1 mr-1"
            title="Add"
          >
            <Check className="w-4 h-4" />
          </button>
          <button
            onClick={() => {
              setShowNewTermForm(null);
              setNewTermData({ abbreviation: '', meaning: '', context: '' });
            }}
            className="text-slate-500 hover:text-slate-700 p-1"
            title="Cancel"
          >
            <X className="w-4 h-4" />
          </button>
        </td>
      </tr>
    );
  };

  // Render category section
  const renderCategory = (category: GlossaryCategory) => {
    const isExpanded = expandedCategories.has(category.id);
    const isEditingCat = editingCategory === category.id;

    return (
      <div key={category.id} className="border border-slate-200 rounded-lg mb-4 overflow-hidden">
        {/* Category header */}
        <div className="bg-slate-100 px-4 py-3 flex items-center justify-between">
          <button
            onClick={() => toggleCategory(category.id)}
            className="flex items-center gap-2 font-medium text-slate-800 hover:text-indigo-600"
          >
            {isExpanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
            {isEditingCat ? (
              <input
                type="text"
                value={editCategoryName}
                onChange={(e) => setEditCategoryName(e.target.value)}
                onClick={(e) => e.stopPropagation()}
                className="px-2 py-1 border border-slate-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                autoFocus
              />
            ) : (
              <span>{category.name}</span>
            )}
            <span className="text-sm font-normal text-slate-500">
              ({category.terms.length} terms)
            </span>
          </button>

          <div className="flex items-center gap-2">
            {isEditingCat ? (
              <>
                <button
                  onClick={() => handleUpdateCategory(category.id)}
                  disabled={saving}
                  className="text-green-600 hover:text-green-800 p-1"
                  title="Save"
                >
                  <Save className="w-4 h-4" />
                </button>
                <button
                  onClick={() => {
                    setEditingCategory(null);
                    setEditCategoryName('');
                  }}
                  className="text-slate-500 hover:text-slate-700 p-1"
                  title="Cancel"
                >
                  <X className="w-4 h-4" />
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => {
                    setShowNewTermForm(category.id);
                    setExpandedCategories(prev => new Set(Array.from(prev).concat(category.id)));
                  }}
                  className="text-green-600 hover:text-green-800 p-1"
                  title="Add term"
                >
                  <Plus className="w-4 h-4" />
                </button>
                <button
                  onClick={() => {
                    setEditingCategory(category.id);
                    setEditCategoryName(category.name);
                  }}
                  className="text-indigo-600 hover:text-indigo-800 p-1"
                  title="Edit category"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDeleteCategory(category.id, category.terms.length)}
                  disabled={saving || category.terms.length > 0}
                  className={`p-1 ${
                    category.terms.length > 0
                      ? 'text-slate-300 cursor-not-allowed'
                      : 'text-red-500 hover:text-red-700'
                  }`}
                  title={category.terms.length > 0 ? 'Delete all terms first' : 'Delete category'}
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </>
            )}
          </div>
        </div>

        {/* Category terms table */}
        {isExpanded && (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-slate-600 w-32">
                  Abbreviation
                </th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">
                  Meaning
                </th>
                <th className="px-4 py-2 text-left font-medium text-slate-600 w-48">
                  Context
                </th>
                <th className="px-4 py-2 text-right font-medium text-slate-600 w-24">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {renderNewTermForm(category.id)}
              {category.terms.map((term) => renderTermRow(term, category.id))}
              {category.terms.length === 0 && showNewTermForm !== category.id && (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-slate-500">
                    No terms in this category.{' '}
                    <button
                      onClick={() => setShowNewTermForm(category.id)}
                      className="text-indigo-600 hover:underline"
                    >
                      Add the first term
                    </button>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    );
  };

  // Render search results
  const renderSearchResults = () => {
    if (!searchResults) return null;

    return (
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-medium text-slate-700">
            Search Results ({searchResults.length})
          </h3>
          <button
            onClick={() => {
              setSearchQuery('');
              setSearchResults(null);
            }}
            className="text-sm text-slate-500 hover:text-slate-700"
          >
            Clear search
          </button>
        </div>
        <div className="border border-slate-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-slate-600 w-32">
                  Abbreviation
                </th>
                <th className="px-4 py-2 text-left font-medium text-slate-600">
                  Meaning
                </th>
                <th className="px-4 py-2 text-left font-medium text-slate-600 w-40">
                  Category
                </th>
                <th className="px-4 py-2 text-right font-medium text-slate-600 w-24">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {searchResults.map((term) => (
                <tr key={term.abbreviation} className="hover:bg-slate-50">
                  <td className="px-4 py-2">
                    <span className="font-mono font-semibold text-slate-800">
                      {term.abbreviation}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-slate-700">{term.meaning}</td>
                  <td className="px-4 py-2 text-slate-500 text-sm">
                    {term.category || '-'}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <button
                      onClick={() => startEditingTerm(term)}
                      className="text-indigo-600 hover:text-indigo-800 p-1 mr-1"
                      title="Edit"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteTerm(term.abbreviation)}
                      disabled={saving}
                      className="text-red-500 hover:text-red-700 p-1"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
              {searchResults.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-slate-500">
                    No terms found matching "{searchQuery}"
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
        <span className="ml-3 text-slate-600">Loading glossary...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Book className="w-6 h-6 text-indigo-600" />
          <div>
            <h2 className="text-lg font-semibold text-slate-900">
              {personaName} Glossary
            </h2>
            <p className="text-sm text-slate-600">
              {glossary?.total_terms || 0} terms in {glossary?.categories.length || 0} categories
            </p>
          </div>
        </div>
        <button
          onClick={() => setShowNewCategoryForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <FolderPlus className="w-4 h-4" />
          Add Category
        </button>
      </div>

      {/* Messages */}
      {error && (
        <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
      {success && (
        <div className="flex items-center gap-2 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
          <Check className="w-5 h-5 flex-shrink-0" />
          <span>{success}</span>
        </div>
      )}

      {/* New category form */}
      {showNewCategoryForm && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <h3 className="font-medium text-slate-800 mb-3">Add New Category</h3>
          <div className="flex items-end gap-3">
            <div className="flex-1">
              <label className="block text-sm text-slate-600 mb-1">Category ID</label>
              <input
                type="text"
                value={newCategoryData.id}
                onChange={(e) => setNewCategoryData(prev => ({ ...prev, id: e.target.value.toLowerCase().replace(/\s+/g, '_') }))}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                placeholder="e.g., cardiovascular"
              />
            </div>
            <div className="flex-1">
              <label className="block text-sm text-slate-600 mb-1">Display Name</label>
              <input
                type="text"
                value={newCategoryData.name}
                onChange={(e) => setNewCategoryData(prev => ({ ...prev, name: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                placeholder="e.g., Cardiovascular"
              />
            </div>
            <button
              onClick={handleAddCategory}
              disabled={saving}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
              Add
            </button>
            <button
              onClick={() => {
                setShowNewCategoryForm(false);
                setNewCategoryData({ id: '', name: '' });
              }}
              className="px-4 py-2 bg-slate-200 text-slate-700 rounded-lg hover:bg-slate-300 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Search and filter bar */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search terms..."
            className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          {searching && (
            <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 animate-spin" />
          )}
        </div>

        {/* Alphabetic filter */}
        <div className="flex items-center gap-1 flex-wrap">
          <button
            onClick={() => setLetterFilter(null)}
            className={`px-2 py-1 text-xs rounded ${
              letterFilter === null
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            All
          </button>
          {availableLetters.map((letter) => (
            <button
              key={letter}
              onClick={() => setLetterFilter(letter)}
              className={`px-2 py-1 text-xs rounded ${
                letterFilter === letter
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {letter}
            </button>
          ))}
        </div>
      </div>

      {/* Search results or categories */}
      {searchResults ? (
        renderSearchResults()
      ) : (
        <div>
          {filteredCategories.map((category) => renderCategory(category))}
          {filteredCategories.length === 0 && (
            <div className="text-center py-12 text-slate-500">
              {letterFilter
                ? `No terms starting with "${letterFilter}"`
                : 'No categories found'}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
