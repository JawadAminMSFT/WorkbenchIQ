# Glossary Feature - Task Breakdown

**Feature Branch**: `009-glossary-feature`  
**Created**: 2026-02-03  

---

## Phase 1: Data Layer & Glossary JSON

### Task 1.1: Create Glossary JSON File

**Description**: Create the initial glossary.json file with all four personas and their terminology.

**File**: `prompts/glossary.json`

**Acceptance Criteria**:
- [ ] JSON validates against schema
- [ ] Contains Life & Health Underwriting terms (58+ terms from user input)
- [ ] Contains Life & Health Claims terms (shared with underwriting)
- [ ] Contains Mortgage Underwriting terms (50+ terms)
- [ ] Contains Automotive Claims terms (50+ terms)
- [ ] Each term has: abbreviation, meaning, optional context, optional examples
- [ ] Terms organized by category within each persona

**Test Coverage**:
```python
def test_glossary_json_valid_schema():
    """Verify glossary.json validates against JSON schema."""
    
def test_glossary_contains_all_personas():
    """Verify all four personas have glossary entries."""
    
def test_glossary_term_structure():
    """Verify each term has required fields."""
```

---

### Task 1.2: Create Glossary Module

**Description**: Create the Python module for glossary CRUD operations.

**File**: `app/glossary.py`

**Functions**:
```python
def load_glossary(prompts_root: str) -> dict:
    """Load the entire glossary file."""

def get_glossary_for_persona(prompts_root: str, persona: str) -> dict:
    """Get glossary entries for a specific persona."""

def search_glossary(prompts_root: str, persona: str, query: str, category: Optional[str] = None) -> List[dict]:
    """Search for terms matching a query."""

def add_term(prompts_root: str, persona: str, category_id: str, term: dict) -> dict:
    """Add a new term to a persona's glossary."""

def update_term(prompts_root: str, persona: str, abbreviation: str, updates: dict) -> dict:
    """Update an existing term."""

def delete_term(prompts_root: str, persona: str, abbreviation: str) -> bool:
    """Delete a term from the glossary."""

def add_category(prompts_root: str, persona: str, category: dict) -> dict:
    """Add a new category to a persona's glossary."""

def update_category(prompts_root: str, persona: str, category_id: str, updates: dict) -> dict:
    """Update an existing category."""

def delete_category(prompts_root: str, persona: str, category_id: str) -> bool:
    """Delete a category (must be empty)."""

def format_glossary_for_prompt(prompts_root: str, persona: str, max_terms: int = 100) -> str:
    """Format glossary as markdown table for LLM injection."""
```

**Acceptance Criteria**:
- [ ] All CRUD functions work correctly
- [ ] Search supports partial matching (case-insensitive)
- [ ] Category operations include validation
- [ ] Format function produces readable markdown

**Test Coverage**:
```python
def test_load_glossary():
    """Test loading the full glossary."""

def test_get_glossary_for_persona():
    """Test getting persona-specific glossary."""

def test_search_glossary_by_abbreviation():
    """Test searching by abbreviation."""

def test_search_glossary_by_meaning():
    """Test searching by meaning."""

def test_add_term():
    """Test adding a new term."""

def test_add_term_duplicate_raises():
    """Test that duplicate abbreviation raises error."""

def test_update_term():
    """Test updating a term."""

def test_delete_term():
    """Test deleting a term."""

def test_format_glossary_for_prompt():
    """Test markdown formatting output."""
```

---

### Task 1.3: Add Glossary API Endpoints

**Description**: Add REST API endpoints for glossary management.

**File**: `api_server.py` (add to existing)

**Endpoints**:
```
GET    /api/glossary                         - List all glossaries summary
GET    /api/glossary/{persona}               - Get complete glossary for persona
GET    /api/glossary/{persona}/search        - Search terms (query param: q, category)
POST   /api/glossary/{persona}/terms         - Add term
PUT    /api/glossary/{persona}/terms/{abbr}  - Update term
DELETE /api/glossary/{persona}/terms/{abbr}  - Delete term
POST   /api/glossary/{persona}/categories    - Add category
PUT    /api/glossary/{persona}/categories/{id} - Update category
DELETE /api/glossary/{persona}/categories/{id} - Delete category
```

**Pydantic Models**:
```python
class GlossaryTerm(BaseModel):
    abbreviation: str
    meaning: str
    context: Optional[str] = None
    examples: Optional[List[str]] = None

class GlossaryCategory(BaseModel):
    id: str
    name: str
    terms: List[GlossaryTerm] = []

class GlossaryTermCreate(BaseModel):
    category_id: str
    abbreviation: str
    meaning: str
    context: Optional[str] = None
    examples: Optional[List[str]] = None

class GlossaryTermUpdate(BaseModel):
    meaning: Optional[str] = None
    context: Optional[str] = None
    examples: Optional[List[str]] = None
    category_id: Optional[str] = None  # For moving between categories

class GlossaryCategoryCreate(BaseModel):
    id: str
    name: str

class GlossaryCategoryUpdate(BaseModel):
    name: Optional[str] = None
```

**Acceptance Criteria**:
- [ ] All endpoints return correct HTTP status codes
- [ ] Validation errors return 422 with details
- [ ] Not found returns 404
- [ ] Duplicate term returns 409

**Test Coverage**:
```python
def test_api_list_glossaries():
    """Test GET /api/glossary returns all personas."""

def test_api_get_glossary_for_persona():
    """Test GET /api/glossary/{persona}."""

def test_api_get_glossary_unknown_persona():
    """Test 404 for unknown persona."""

def test_api_search_glossary():
    """Test search endpoint."""

def test_api_add_term():
    """Test POST term endpoint."""

def test_api_add_term_duplicate():
    """Test 409 for duplicate term."""

def test_api_update_term():
    """Test PUT term endpoint."""

def test_api_delete_term():
    """Test DELETE term endpoint."""

def test_api_category_crud():
    """Test category create/update/delete."""
```

---

## Phase 2: Admin UI - Glossary Management

### Task 2.1: Add Glossary Tab to Admin Page

**Description**: Add 'glossary' as a new tab option in the admin page.

**File**: `frontend/src/app/admin/page.tsx`

**Changes**:
```typescript
type AdminTab = 'documents' | 'prompts' | 'policies' | 'glossary' | 'analyzer';

// Add tab button in the tab bar
// Add conditional rendering for GlossaryPanel component
```

**Acceptance Criteria**:
- [ ] Glossary tab appears in admin navigation
- [ ] Tab respects current persona context
- [ ] Tab icon uses appropriate Lucide icon (Book or BookA)

---

### Task 2.2: Create GlossaryPanel Component

**Description**: Create the main glossary management panel for the admin view.

**File**: `frontend/src/components/admin/GlossaryPanel.tsx`

**Component Structure**:
```tsx
interface GlossaryPanelProps {
  persona: string;
}

export default function GlossaryPanel({ persona }: GlossaryPanelProps) {
  // State for glossary data
  // State for selected category
  // State for search query
  // State for add/edit modals
  
  return (
    <div>
      {/* Header with search and add button */}
      {/* Category filter dropdown */}
      {/* Collapsible category sections */}
      {/* Term table within each category */}
      {/* Add/Edit term modal */}
      {/* Add/Edit category modal */}
    </div>
  );
}
```

**Sub-components**:
- `GlossaryTermRow` - Individual term display with edit/delete
- `GlossaryTermModal` - Add/edit term form
- `GlossaryCategorySection` - Collapsible category with terms
- `GlossaryCategoryModal` - Add/edit category form

**Acceptance Criteria**:
- [ ] Displays all categories and terms for current persona
- [ ] Search filters terms in real-time
- [ ] Category sections are collapsible
- [ ] Add term shows modal form
- [ ] Edit term pre-populates form
- [ ] Delete shows confirmation dialog
- [ ] Form validates required fields
- [ ] Success/error toasts on operations

---

### Task 2.3: Add Glossary API Client Functions

**Description**: Add frontend API functions for glossary operations.

**File**: `frontend/src/lib/api.ts`

**Functions**:
```typescript
export interface GlossaryTerm {
  abbreviation: string;
  meaning: string;
  context?: string;
  examples?: string[];
}

export interface GlossaryCategory {
  id: string;
  name: string;
  terms: GlossaryTerm[];
}

export interface PersonaGlossary {
  persona: string;
  name: string;
  description?: string;
  categories: GlossaryCategory[];
  total_terms: number;
}

export async function getGlossary(persona: string): Promise<PersonaGlossary> {
  return apiFetch<PersonaGlossary>(`/api/glossary/${persona}`);
}

export async function searchGlossary(persona: string, query: string, category?: string): Promise<GlossaryTerm[]> {
  const params = new URLSearchParams({ q: query });
  if (category) params.append('category', category);
  return apiFetch<{ results: GlossaryTerm[] }>(`/api/glossary/${persona}/search?${params}`).then(r => r.results);
}

export async function addGlossaryTerm(persona: string, term: GlossaryTermCreate): Promise<GlossaryTerm> {
  return apiFetch<GlossaryTerm>(`/api/glossary/${persona}/terms`, {
    method: 'POST',
    body: JSON.stringify(term),
  });
}

export async function updateGlossaryTerm(persona: string, abbr: string, term: GlossaryTermUpdate): Promise<GlossaryTerm> {
  return apiFetch<GlossaryTerm>(`/api/glossary/${persona}/terms/${encodeURIComponent(abbr)}`, {
    method: 'PUT',
    body: JSON.stringify(term),
  });
}

export async function deleteGlossaryTerm(persona: string, abbr: string): Promise<void> {
  await apiFetch(`/api/glossary/${persona}/terms/${encodeURIComponent(abbr)}`, {
    method: 'DELETE',
  });
}

// Category functions similarly...
```

**Acceptance Criteria**:
- [ ] All functions properly typed
- [ ] Error handling for API failures
- [ ] URL encoding for special characters in abbreviations

---

### Task 2.4: Add TypeScript Types

**Description**: Add glossary types to the types file.

**File**: `frontend/src/lib/types.ts`

**Types**:
```typescript
export interface GlossaryTerm {
  abbreviation: string;
  meaning: string;
  context?: string;
  examples?: string[];
}

export interface GlossaryCategory {
  id: string;
  name: string;
  terms: GlossaryTerm[];
}

export interface PersonaGlossary {
  persona: string;
  name: string;
  description?: string;
  categories: GlossaryCategory[];
  total_terms: number;
}

export interface GlossaryTermCreate {
  category_id: string;
  abbreviation: string;
  meaning: string;
  context?: string;
  examples?: string[];
}

export interface GlossaryTermUpdate {
  meaning?: string;
  context?: string;
  examples?: string[];
  category_id?: string;
}

export interface GlossaryCategoryCreate {
  id: string;
  name: string;
}

export interface GlossaryCategoryUpdate {
  name?: string;
}

export interface GlossarySearchResult {
  abbreviation: string;
  meaning: string;
  category: string;
  context?: string;
}
```

---

## Phase 3: LLM Prompt Injection

### Task 3.1: Create Glossary Prompt Formatter

**Description**: Create a function to format glossary for LLM prompt injection.

**File**: `app/glossary.py` (extend from Task 1.2)

**Function**:
```python
def format_glossary_for_prompt(
    prompts_root: str,
    persona: str,
    max_terms: int = 100,
    categories: Optional[List[str]] = None,
    format_type: str = "markdown"  # or "list"
) -> str:
    """
    Format glossary as a string suitable for LLM prompt injection.
    
    Args:
        prompts_root: Path to prompts directory
        persona: The persona to get glossary for
        max_terms: Maximum terms to include (prioritize by frequency)
        categories: Optional list of category IDs to include
        format_type: Output format (markdown table or simple list)
    
    Returns:
        Formatted string ready for prompt injection
    
    Example markdown output:
        ## Domain Terminology
        
        | Abbreviation | Meaning |
        |-------------|---------|
        | HTN | Hypertension |
        | DM | Diabetes mellitus |
        ...
    
    Example list output:
        Domain Terminology:
        - HTN: Hypertension
        - DM: Diabetes mellitus
        ...
    """
```

**Acceptance Criteria**:
- [ ] Produces valid markdown tables
- [ ] Respects max_terms limit
- [ ] Can filter by categories
- [ ] Handles empty glossary gracefully

---

### Task 3.2: Inject Glossary into Processing Pipeline

**Description**: Modify document processing to include glossary context.

**File**: `app/processing.py`

**Changes**:
```python
from app.glossary import format_glossary_for_prompt

def run_content_understanding_for_files(settings, app_md):
    # ... existing code ...
    
    # Load glossary for persona
    glossary_context = format_glossary_for_prompt(
        settings.app.prompts_root,
        app_md.persona,
        max_terms=50,  # Limit for extraction context
    )
    
    # Include in extraction prompts
    # ...

def run_underwriting_prompts(settings, app_md, ...):
    # ... existing code ...
    
    # Load glossary for analysis prompts
    glossary_context = format_glossary_for_prompt(
        settings.app.prompts_root,
        app_md.persona,
        max_terms=100,
    )
    
    # Inject into prompt template
    # ...
```

**Acceptance Criteria**:
- [ ] Glossary loads without error for all personas
- [ ] Prompts include glossary context
- [ ] Context size is appropriate for model limits

---

### Task 3.3: Update Risk Analysis Prompts

**Description**: Add glossary placeholder to risk analysis prompts.

**File**: `prompts/risk-analysis-prompts.json`

**Changes**:
```json
{
  "prompts": {
    "overall_risk_assessment": {
      "prompt": "You are an expert life insurance underwriter...\n\n## Domain Terminology Reference\n\n{glossary_context}\n\n## UNDERWRITING POLICIES\n\n{underwriting_policies}\n\n..."
    }
  }
}
```

**Acceptance Criteria**:
- [ ] All prompt templates support `{glossary_context}` placeholder
- [ ] Placeholder is optional (empty string if no glossary)

---

## Phase 4: Chat Integration

### Task 4.1: Update Chat System Prompt

**Description**: Inject glossary into chat system prompts.

**File**: `api_server.py` (modify `get_chat_system_prompt` function)

**Changes**:
```python
from app.glossary import format_glossary_for_prompt

def get_chat_system_prompt(
    persona: str,
    policies_context: str,
    app_id: str,
    app_context_parts: list[str],
) -> str:
    """Generate a persona-aware system prompt for Ask IQ chat."""
    
    config = PERSONA_CHAT_CONFIG.get(persona, PERSONA_CHAT_CONFIG["underwriting"])
    
    # Load glossary for persona
    glossary_context = format_glossary_for_prompt(
        settings.app.prompts_root,
        persona,
        max_terms=75,  # Limit for chat context
        format_type="list"  # More compact for chat
    )
    
    return f"""You are an {config['role']}...

## Domain Terminology

The following abbreviations and terms are commonly used in this domain. When you encounter these in documents or user questions, interpret them accordingly:

{glossary_context}

When asked about specific terms or abbreviations, explain them in context.

## Policies Context

{policies_context}

...rest of prompt...
"""
```

**Acceptance Criteria**:
- [ ] Glossary included in chat system prompt
- [ ] Chat can explain abbreviations when asked
- [ ] Chat correctly interprets abbreviations in context

---

### Task 4.2: Add Glossary Lookup Chat Feature

**Description**: Enable explicit term lookup in chat.

**File**: `api_server.py` (chat endpoint)

**Enhancement**:
When user asks "What does [TERM] mean?" or "Define [TERM]":
1. First check glossary for exact match
2. Include glossary definition in response
3. Add context about how term is used in the domain

**Acceptance Criteria**:
- [ ] "What does HTN mean?" returns glossary definition
- [ ] Works for all persona-specific terms
- [ ] Falls back to general knowledge for unknown terms

---

## Phase 5: UI Glossary Dropdown

### Task 5.1: Create GlossaryDropdown Component

**Description**: Create a dropdown component for quick term lookup.

**File**: `frontend/src/components/GlossaryDropdown.tsx`

**Component Structure**:
```tsx
interface GlossaryDropdownProps {
  persona: string;
}

export default function GlossaryDropdown({ persona }: GlossaryDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLetter, setSelectedLetter] = useState<string | null>(null);
  const [glossary, setGlossary] = useState<PersonaGlossary | null>(null);
  
  // Load glossary on mount and persona change
  useEffect(() => {
    getGlossary(persona).then(setGlossary);
  }, [persona]);
  
  // Filter terms based on search and letter selection
  const filteredTerms = useMemo(() => {
    // Flatten all terms
    // Filter by search query
    // Filter by selected letter
    // Sort alphabetically
  }, [glossary, searchQuery, selectedLetter]);
  
  return (
    <div className="relative">
      {/* Trigger button */}
      <button onClick={() => setIsOpen(!isOpen)}>
        <BookOpen className="w-4 h-4" />
        <span>Glossary</span>
        <ChevronDown className="w-3 h-3" />
      </button>
      
      {isOpen && (
        <div className="absolute dropdown-panel">
          {/* Search input */}
          <input 
            type="text"
            placeholder="Search terms..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
          />
          
          {/* Alphabet navigation */}
          <div className="flex flex-wrap gap-1">
            {alphabet.map(letter => (
              <button
                key={letter}
                onClick={() => setSelectedLetter(letter === selectedLetter ? null : letter)}
                className={letter === selectedLetter ? 'selected' : ''}
              >
                {letter}
              </button>
            ))}
          </div>
          
          {/* Terms list */}
          <div className="max-h-64 overflow-y-auto">
            {filteredTerms.map(term => (
              <div key={term.abbreviation} className="term-row">
                <span className="font-mono font-bold">{term.abbreviation}</span>
                <span className="text-slate-600">{term.meaning}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

**Acceptance Criteria**:
- [ ] Dropdown opens/closes on click
- [ ] Search filters terms in real-time
- [ ] A-Z navigation works
- [ ] Terms display abbreviation and meaning
- [ ] Closes on outside click
- [ ] Keyboard accessible

---

### Task 5.2: Integrate with TopNav

**Description**: Add GlossaryDropdown to the top navigation bar.

**File**: `frontend/src/components/TopNav.tsx`

**Changes**:
```tsx
import GlossaryDropdown from './GlossaryDropdown';

export default function TopNav() {
  const { currentPersona } = usePersona();
  
  return (
    <nav>
      {/* ... existing content ... */}
      
      <div className="flex items-center gap-4">
        <PersonaSelector />
        <GlossaryDropdown persona={currentPersona} />
        {/* ... rest of nav ... */}
      </div>
    </nav>
  );
}
```

**Acceptance Criteria**:
- [ ] Glossary dropdown appears beside persona selector
- [ ] Updates when persona changes
- [ ] Responsive on mobile

---

### Task 5.3: Add Keyboard Shortcut

**Description**: Add Ctrl+G / Cmd+G shortcut to open glossary.

**File**: `frontend/src/components/GlossaryDropdown.tsx`

**Enhancement**:
```tsx
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'g') {
      e.preventDefault();
      setIsOpen(true);
      // Focus search input
    }
    if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };
  
  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, []);
```

**Acceptance Criteria**:
- [ ] Ctrl+G opens glossary on Windows
- [ ] Cmd+G opens glossary on Mac
- [ ] Escape closes glossary
- [ ] Focus moves to search input

---

### Task 5.4: Mobile Sidebar Integration

**Description**: Add glossary access to mobile sidebar.

**File**: `frontend/src/components/Sidebar.tsx`

**Changes**:
```tsx
// Add glossary link/button in sidebar for mobile view
<Link href="#" onClick={() => openGlossaryModal()}>
  <BookOpen className="w-5 h-5" />
  <span>Glossary</span>
</Link>
```

**Acceptance Criteria**:
- [ ] Glossary accessible on mobile
- [ ] Opens as modal on small screens
- [ ] Full functionality maintained

---

## Test Files

### tests/test_glossary_phase1_data.py

```python
"""
Tests for Phase 1: Glossary Data Layer

Tests cover:
- Glossary JSON structure and validation
- CRUD operations in glossary module
- API endpoints for glossary management
"""

import pytest
import json
from pathlib import Path
from fastapi.testclient import TestClient


class TestGlossaryJSONStructure:
    """Tests for glossary.json file structure."""
    
    def test_glossary_json_exists(self):
        """Verify glossary.json exists in prompts folder."""
        pass
    
    def test_glossary_json_valid_json(self):
        """Verify glossary.json is valid JSON."""
        pass
    
    def test_glossary_contains_all_personas(self):
        """Verify all four personas are present."""
        pass
    
    def test_glossary_term_has_required_fields(self):
        """Verify each term has abbreviation and meaning."""
        pass
    
    def test_glossary_categories_have_unique_ids(self):
        """Verify category IDs are unique within each persona."""
        pass


class TestGlossaryModule:
    """Tests for app/glossary.py module."""
    
    def test_load_glossary(self):
        """Test loading the full glossary."""
        pass
    
    def test_get_glossary_for_persona_underwriting(self):
        """Test getting underwriting glossary."""
        pass
    
    def test_get_glossary_for_persona_mortgage(self):
        """Test getting mortgage glossary."""
        pass
    
    def test_get_glossary_for_unknown_persona(self):
        """Test handling of unknown persona."""
        pass
    
    def test_search_glossary_exact_match(self):
        """Test searching with exact abbreviation."""
        pass
    
    def test_search_glossary_partial_match(self):
        """Test searching with partial text."""
        pass
    
    def test_search_glossary_case_insensitive(self):
        """Test case-insensitive search."""
        pass
    
    def test_search_glossary_by_meaning(self):
        """Test searching in meaning text."""
        pass
    
    def test_add_term_success(self, temp_glossary):
        """Test adding a new term."""
        pass
    
    def test_add_term_duplicate_raises(self, temp_glossary):
        """Test that duplicate abbreviation raises error."""
        pass
    
    def test_update_term(self, temp_glossary):
        """Test updating an existing term."""
        pass
    
    def test_update_term_not_found(self, temp_glossary):
        """Test updating non-existent term."""
        pass
    
    def test_delete_term(self, temp_glossary):
        """Test deleting a term."""
        pass
    
    def test_format_glossary_for_prompt_markdown(self):
        """Test markdown table formatting."""
        pass
    
    def test_format_glossary_for_prompt_list(self):
        """Test list formatting."""
        pass
    
    def test_format_glossary_respects_max_terms(self):
        """Test max_terms limit is respected."""
        pass


class TestGlossaryAPI:
    """Tests for glossary API endpoints."""
    
    def test_api_list_glossaries(self, client: TestClient):
        """Test GET /api/glossary returns all personas."""
        pass
    
    def test_api_get_glossary_for_persona(self, client: TestClient):
        """Test GET /api/glossary/{persona}."""
        pass
    
    def test_api_get_glossary_not_found(self, client: TestClient):
        """Test 404 for unknown persona."""
        pass
    
    def test_api_search_glossary(self, client: TestClient):
        """Test search endpoint with query."""
        pass
    
    def test_api_search_glossary_no_results(self, client: TestClient):
        """Test search with no matching results."""
        pass
    
    def test_api_add_term(self, client: TestClient, temp_glossary):
        """Test POST term endpoint."""
        pass
    
    def test_api_add_term_duplicate(self, client: TestClient, temp_glossary):
        """Test 409 for duplicate term."""
        pass
    
    def test_api_add_term_invalid_category(self, client: TestClient, temp_glossary):
        """Test 404 for invalid category."""
        pass
    
    def test_api_update_term(self, client: TestClient, temp_glossary):
        """Test PUT term endpoint."""
        pass
    
    def test_api_delete_term(self, client: TestClient, temp_glossary):
        """Test DELETE term endpoint."""
        pass
    
    def test_api_add_category(self, client: TestClient, temp_glossary):
        """Test POST category endpoint."""
        pass
    
    def test_api_delete_category_not_empty(self, client: TestClient, temp_glossary):
        """Test 409 when deleting non-empty category."""
        pass
```

---

### tests/test_glossary_phase2_admin.py

```python
"""
Tests for Phase 2: Admin UI Glossary Panel

Tests cover:
- GlossaryPanel component rendering
- CRUD operations via UI
- Persona switching behavior
"""

import pytest


class TestGlossaryPanelRendering:
    """Tests for GlossaryPanel component."""
    
    def test_panel_renders_with_glossary_data(self):
        """Test panel displays terms and categories."""
        pass
    
    def test_panel_shows_loading_state(self):
        """Test loading indicator while fetching."""
        pass
    
    def test_panel_shows_error_state(self):
        """Test error display on API failure."""
        pass
    
    def test_panel_empty_state(self):
        """Test display when no terms exist."""
        pass


class TestGlossarySearch:
    """Tests for search functionality."""
    
    def test_search_filters_terms(self):
        """Test search input filters displayed terms."""
        pass
    
    def test_search_highlights_matches(self):
        """Test matched text is highlighted."""
        pass
    
    def test_search_debounced(self):
        """Test search is debounced for performance."""
        pass


class TestGlossaryCRUD:
    """Tests for CRUD operations."""
    
    def test_add_term_opens_modal(self):
        """Test Add Term button opens modal."""
        pass
    
    def test_add_term_form_validation(self):
        """Test form validates required fields."""
        pass
    
    def test_add_term_success(self):
        """Test successful term addition."""
        pass
    
    def test_edit_term_prefills_form(self):
        """Test edit modal prefills with existing data."""
        pass
    
    def test_delete_term_confirmation(self):
        """Test delete shows confirmation dialog."""
        pass


class TestPersonaSwitching:
    """Tests for persona context."""
    
    def test_glossary_updates_on_persona_change(self):
        """Test glossary reloads when persona changes."""
        pass
    
    def test_maintains_search_on_persona_change(self):
        """Test search is cleared on persona change."""
        pass
```

---

### tests/test_glossary_phase3_llm.py

```python
"""
Tests for Phase 3: LLM Prompt Injection

Tests cover:
- Glossary formatting for prompts
- Injection into processing pipeline
- Prompt template updates
"""

import pytest


class TestGlossaryFormatting:
    """Tests for prompt formatting functions."""
    
    def test_format_markdown_table(self):
        """Test markdown table output."""
        pass
    
    def test_format_list(self):
        """Test list output."""
        pass
    
    def test_format_respects_max_terms(self):
        """Test max_terms limit."""
        pass
    
    def test_format_category_filter(self):
        """Test filtering by categories."""
        pass
    
    def test_format_empty_glossary(self):
        """Test handling of empty glossary."""
        pass


class TestProcessingIntegration:
    """Tests for processing pipeline integration."""
    
    def test_extraction_includes_glossary(self):
        """Test document extraction prompts include glossary."""
        pass
    
    def test_analysis_includes_glossary(self):
        """Test analysis prompts include glossary."""
        pass
    
    def test_glossary_per_persona(self):
        """Test correct glossary used for each persona."""
        pass


class TestPromptTemplates:
    """Tests for prompt template updates."""
    
    def test_risk_analysis_has_glossary_placeholder(self):
        """Test risk analysis prompts have placeholder."""
        pass
    
    def test_placeholder_replaced_correctly(self):
        """Test placeholder replaced with actual glossary."""
        pass
    
    def test_optional_placeholder(self):
        """Test empty string when no glossary."""
        pass
```

---

### tests/test_glossary_phase4_chat.py

```python
"""
Tests for Phase 4: Chat Integration

Tests cover:
- Glossary in chat system prompt
- Term lookup in chat
- Context-aware interpretation
"""

import pytest


class TestChatSystemPrompt:
    """Tests for chat system prompt modification."""
    
    def test_system_prompt_includes_glossary(self):
        """Test glossary section in system prompt."""
        pass
    
    def test_glossary_per_persona_in_chat(self):
        """Test correct glossary for persona."""
        pass
    
    def test_glossary_compact_format_for_chat(self):
        """Test glossary is appropriately sized for chat."""
        pass


class TestTermLookup:
    """Tests for explicit term lookup."""
    
    def test_what_does_term_mean(self):
        """Test 'What does HTN mean?' response."""
        pass
    
    def test_define_term(self):
        """Test 'Define DM' response."""
        pass
    
    def test_unknown_term_fallback(self):
        """Test response for unknown terms."""
        pass


class TestContextInterpretation:
    """Tests for contextual interpretation."""
    
    def test_abbreviation_in_question(self):
        """Test chat understands abbreviations in questions."""
        pass
    
    def test_abbreviation_in_document_context(self):
        """Test chat interprets abbreviations from docs."""
        pass
```

---

### tests/test_glossary_phase5_ui.py

```python
"""
Tests for Phase 5: UI Glossary Dropdown

Tests cover:
- GlossaryDropdown component
- TopNav integration
- Keyboard shortcuts
- Mobile responsive
"""

import pytest


class TestGlossaryDropdown:
    """Tests for GlossaryDropdown component."""
    
    def test_dropdown_opens_on_click(self):
        """Test dropdown opens when clicked."""
        pass
    
    def test_dropdown_closes_on_outside_click(self):
        """Test dropdown closes on outside click."""
        pass
    
    def test_search_filters_terms(self):
        """Test search input filters terms."""
        pass
    
    def test_alphabet_navigation(self):
        """Test A-Z navigation buttons."""
        pass
    
    def test_term_display(self):
        """Test terms show abbreviation and meaning."""
        pass


class TestKeyboardShortcuts:
    """Tests for keyboard interactions."""
    
    def test_ctrl_g_opens_dropdown(self):
        """Test Ctrl+G opens dropdown."""
        pass
    
    def test_escape_closes_dropdown(self):
        """Test Escape closes dropdown."""
        pass
    
    def test_focus_moves_to_search(self):
        """Test focus on search input when opened."""
        pass


class TestTopNavIntegration:
    """Tests for TopNav integration."""
    
    def test_dropdown_in_header(self):
        """Test dropdown appears in header."""
        pass
    
    def test_updates_with_persona(self):
        """Test dropdown updates on persona change."""
        pass


class TestMobileResponsive:
    """Tests for mobile responsiveness."""
    
    def test_sidebar_has_glossary_link(self):
        """Test glossary in mobile sidebar."""
        pass
    
    def test_mobile_modal_view(self):
        """Test modal view on small screens."""
        pass
```

---

## Implementation Order Summary

| Order | Task | Estimated Effort | Dependencies |
|-------|------|------------------|--------------|
| 1 | Task 1.1: Create glossary.json | 2 hours | None |
| 2 | Task 1.2: Create glossary module | 3 hours | Task 1.1 |
| 3 | Task 1.3: Add API endpoints | 2 hours | Task 1.2 |
| 4 | Task 2.4: Add TypeScript types | 30 min | None |
| 5 | Task 2.3: Add API client functions | 1 hour | Task 1.3, Task 2.4 |
| 6 | Task 2.2: Create GlossaryPanel | 4 hours | Task 2.3 |
| 7 | Task 2.1: Add Glossary tab | 30 min | Task 2.2 |
| 8 | Task 3.1: Create prompt formatter | 1 hour | Task 1.2 |
| 9 | Task 3.2: Inject into processing | 2 hours | Task 3.1 |
| 10 | Task 3.3: Update risk prompts | 1 hour | Task 3.1 |
| 11 | Task 4.1: Update chat system prompt | 2 hours | Task 3.1 |
| 12 | Task 4.2: Add glossary lookup | 1 hour | Task 4.1 |
| 13 | Task 5.1: Create GlossaryDropdown | 3 hours | Task 2.3 |
| 14 | Task 5.2: Integrate with TopNav | 30 min | Task 5.1 |
| 15 | Task 5.3: Add keyboard shortcut | 30 min | Task 5.1 |
| 16 | Task 5.4: Mobile sidebar | 1 hour | Task 5.1 |

**Total Estimated Effort**: ~24 hours

---

## Definition of Done

For each phase to be considered complete:

1. **All tasks implemented** with working code
2. **All tests passing** with >80% coverage
3. **Code reviewed** and approved
4. **Documentation updated** (README, API docs)
5. **No regressions** in existing functionality
6. **Deployed to dev environment** and manually verified

