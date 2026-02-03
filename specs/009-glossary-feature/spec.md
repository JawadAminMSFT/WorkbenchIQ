# Feature Specification: Persona-Based Glossary System

**Feature Branch**: `009-glossary-feature`  
**Created**: 2026-02-03  
**Status**: Draft  
**Author**: Copilot  

---

## Overview

This specification defines a **Persona-Based Glossary System** for WorkbenchIQ that enables domain-specific terminology management across different industry personas. The glossary system will:

1. Store industry-specific abbreviations and terminology as JSON in the prompts folder
2. Provide admin UI for CRUD operations on glossary terms
3. Inject glossary context into LLM prompts for document processing and risk analysis
4. Integrate with the chat experience for automatic term understanding
5. Add a glossary dropdown UI component for quick reference during work

### Business Value

| Persona | Use Case | Value |
|---------|----------|-------|
| Life & Health Underwriting | Medical abbreviations (HTN, DM, CABG) | Accurate interpretation of APS medical records |
| Life & Health Claims | Medical/claims terms | Faster claims adjudication with understood terminology |
| Mortgage Underwriting | Financial/regulatory acronyms (GDS, TDS, OSFI, MQR) | Consistent OSFI B-20 compliance language |
| Automotive Claims | Auto industry/damage terms (PDR, TL, OEM, AI) | Standardized damage assessment vocabulary |

---

## Glossary Data Structure

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "version": { "type": "string" },
    "effective_date": { "type": "string", "format": "date" },
    "last_updated": { "type": "string", "format": "date" },
    "description": { "type": "string" },
    "personas": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "description": { "type": "string" },
          "categories": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "id": { "type": "string" },
                "name": { "type": "string" },
                "terms": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "abbreviation": { "type": "string" },
                      "meaning": { "type": "string" },
                      "context": { "type": "string" },
                      "examples": { "type": "array", "items": { "type": "string" } }
                    },
                    "required": ["abbreviation", "meaning"]
                  }
                }
              },
              "required": ["id", "name", "terms"]
            }
          }
        },
        "required": ["name", "categories"]
      }
    }
  },
  "required": ["version", "personas"]
}
```

### File Location

```
prompts/
├── glossary.json                          # Main glossary file with all personas
├── life-health-underwriting-policies.json # Existing
├── automotive-claims-policies.json        # Existing
└── ...
```

---

## Proposed Glossary Content

### Life & Health Underwriting / Claims (Provided by User)

| Category | Abbreviation | Meaning |
|----------|-------------|---------|
| General | Hx | History |
| General | PMHx | Past medical history |
| General | FHx | Family history |
| General | SHx | Social history |
| General | ROS | Review of systems |
| General | PE | Physical exam |
| General | CC | Chief complaint |
| General | Dx | Diagnosis |
| General | Tx | Treatment |
| General | Rx | Prescription |
| General | Sx | Symptoms |
| General | FU / F/U | Follow-up |
| General | PRN | As needed |
| General | WNL | Within normal limits |
| General | NAD | No acute distress |
| General | r/o | Rule out |
| General | s/p | Status post |
| Vitals | BP | Blood pressure |
| Vitals | HR | Heart rate |
| Vitals | RR | Respiratory rate |
| Vitals | BMI | Body mass index |
| Vitals | SpO₂ | Oxygen saturation |
| Cardiac | HTN | Hypertension |
| Cardiac | HLD | Hyperlipidemia |
| Cardiac | CAD | Coronary artery disease |
| Cardiac | MI | Myocardial infarction |
| Cardiac | CHF | Congestive heart failure |
| Cardiac | AF / Afib | Atrial fibrillation |
| Cardiac | EKG / ECG | Electrocardiogram |
| Cardiac | Echo | Echocardiogram |
| Cardiac | CABG | Coronary artery bypass graft |
| Cardiac | SOB | Shortness of breath |
| Endocrine | DM | Diabetes mellitus |
| Endocrine | T1DM / T2DM | Type 1 / Type 2 diabetes |
| Endocrine | A1C / HbA1c | Hemoglobin A1c |
| Endocrine | TSH | Thyroid-stimulating hormone |
| Respiratory | COPD | Chronic obstructive pulmonary disease |
| Respiratory | OSA | Obstructive sleep apnea |
| Respiratory | CPAP | Continuous positive airway pressure |
| Respiratory | PFT | Pulmonary function test |
| Neuro / MH | CVA | Stroke |
| Neuro / MH | TIA | Transient ischemic attack |
| Neuro / MH | Sz | Seizure |
| Neuro / MH | MDD | Major depressive disorder |
| Neuro / MH | GAD | Generalized anxiety disorder |
| Neuro / MH | PTSD | Post-traumatic stress disorder |
| Neuro / MH | SI / HI | Suicidal / homicidal ideation |
| MSK | OA | Osteoarthritis |
| MSK | RA | Rheumatoid arthritis |
| MSK | DJD | Degenerative joint disease |
| MSK | LBP | Low back pain |
| MSK | ROM | Range of motion |
| GI / Renal | GERD | Gastroesophageal reflux disease |
| GI / Renal | IBS | Irritable bowel syndrome |
| GI / Renal | NAFLD | Non-alcoholic fatty liver disease |
| GI / Renal | LFTs | Liver function tests |
| GI / Renal | Cr | Creatinine |
| GI / Renal | eGFR | Estimated GFR |
| Oncology | CA | Cancer |
| Oncology | bx | Biopsy |
| Oncology | Mets | Metastases |
| Oncology | NED | No evidence of disease |
| Oncology | Stage I–IV | Cancer stage |
| Meds | ACEi | ACE inhibitor |
| Meds | ARB | Angiotensin receptor blocker |
| Meds | BB | Beta blocker |
| Meds | CCB | Calcium channel blocker |
| Meds | SSRI | Selective serotonin reuptake inhibitor |
| Meds | NSAID | Non-steroidal anti-inflammatory |
| Social | ETOH | Alcohol |
| Social | tob | Tobacco |
| Social | ppd | Packs per day |
| Social | denies | Patient denies |

### Mortgage Underwriting (New - AI Generated)

| Category | Abbreviation | Meaning |
|----------|-------------|---------|
| Regulatory | OSFI | Office of the Superintendent of Financial Institutions |
| Regulatory | B-20 | OSFI Guideline B-20 (Residential Mortgage Underwriting) |
| Regulatory | CMHC | Canada Mortgage and Housing Corporation |
| Regulatory | FINTRAC | Financial Transactions and Reports Analysis Centre |
| Regulatory | AML | Anti-Money Laundering |
| Regulatory | KYC | Know Your Customer |
| Ratios | GDS | Gross Debt Service (ratio) |
| Ratios | TDS | Total Debt Service (ratio) |
| Ratios | LTV | Loan-to-Value (ratio) |
| Ratios | PITH | Principal, Interest, Taxes, Heating |
| Ratios | MQR | Mortgage Qualifying Rate |
| Ratios | DSR | Debt Service Ratio |
| Income | NOA | Notice of Assessment (CRA) |
| Income | T4 | Statement of Remuneration Paid |
| Income | T1 | Individual Income Tax Return |
| Income | YTD | Year-to-Date |
| Income | GIC | Guaranteed Investment Certificate |
| Income | RRSP | Registered Retirement Savings Plan |
| Income | TFSA | Tax-Free Savings Account |
| Income | HELOC | Home Equity Line of Credit |
| Property | APS | Agreement of Purchase and Sale |
| Property | MLS | Multiple Listing Service |
| Property | GFA | Gross Floor Area |
| Property | SFH | Single Family Home |
| Property | PUD | Planned Unit Development |
| Property | ARV | After Repair Value |
| Property | BPO | Broker Price Opinion |
| Loan | ARM | Adjustable Rate Mortgage |
| Loan | VRM | Variable Rate Mortgage |
| Loan | FRM | Fixed Rate Mortgage |
| Loan | LOC | Line of Credit |
| Loan | MTG | Mortgage |
| Loan | P&I | Principal and Interest |
| Loan | POF | Proof of Funds |
| Credit | FICO | Fair Isaac Corporation (credit score) |
| Credit | Beacon | Equifax credit score (Canada) |
| Credit | TU | TransUnion |
| Credit | EFX | Equifax |
| Credit | UTL | Utilization |
| Credit | ROI | Return on Investment |
| Status | A/C | Approved with Conditions |
| Status | DTC | Decline to Credit |
| Status | TBD | To Be Determined |
| Status | UW | Underwriter / Underwriting |
| Status | COE | Close of Escrow |
| Status | COI | Certificate of Insurance |

### Automotive Claims (New - AI Generated)

| Category | Abbreviation | Meaning |
|----------|-------------|---------|
| Damage Assessment | PDR | Paintless Dent Repair |
| Damage Assessment | TL | Total Loss |
| Damage Assessment | RTV | Repairable Total Value |
| Damage Assessment | AOI | Area of Impact |
| Damage Assessment | POI | Point of Impact |
| Damage Assessment | DOL | Direction of Loss |
| Parts | OEM | Original Equipment Manufacturer |
| Parts | A/M | Aftermarket |
| Parts | LKQ | Like Kind and Quality (used parts) |
| Parts | R&I | Remove and Install |
| Parts | R&R | Remove and Replace |
| Parts | ADAS | Advanced Driver Assistance Systems |
| Parts | ECU | Electronic Control Unit |
| Parts | SRS | Supplemental Restraint System (airbags) |
| Parts | ABS | Anti-lock Braking System |
| Estimate | RO | Repair Order |
| Estimate | LBR | Labor |
| Estimate | PNT | Paint |
| Estimate | MATL | Materials |
| Estimate | BT | Blend Time |
| Estimate | CT | Clear Time |
| Estimate | FRT | Flat Rate Time |
| Estimate | PDL | Paint/Damage Line |
| Vehicle | VIN | Vehicle Identification Number |
| Vehicle | YMM | Year, Make, Model |
| Vehicle | ODO | Odometer |
| Vehicle | EV | Electric Vehicle |
| Vehicle | ICE | Internal Combustion Engine |
| Vehicle | AWD | All-Wheel Drive |
| Vehicle | FWD | Front-Wheel Drive |
| Vehicle | RWD | Rear-Wheel Drive |
| Valuation | ACV | Actual Cash Value |
| Valuation | FMV | Fair Market Value |
| Valuation | NADA | National Automobile Dealers Association |
| Valuation | KBB | Kelley Blue Book |
| Valuation | CCC | CCC Intelligent Solutions (estimating) |
| Valuation | Mitchell | Mitchell International (estimating) |
| Liability | COL | Collision |
| Liability | COMP | Comprehensive |
| Liability | BI | Bodily Injury |
| Liability | PD | Property Damage |
| Liability | UM/UIM | Uninsured/Underinsured Motorist |
| Liability | PIP | Personal Injury Protection |
| Liability | MP | Medical Payments |
| Process | IA | Independent Adjuster |
| Process | DRP | Direct Repair Program |
| Process | SIU | Special Investigations Unit |
| Process | FNOL | First Notice of Loss |
| Process | POL | Proof of Loss |
| Process | RV | Rental Vehicle |
| Process | S/V | Salvage Value |
| Process | SB | Subrogation |

---

## Phased Implementation Plan

### Phase 1: Data Layer & Glossary JSON (Backend Foundation)

**Objective**: Create the glossary data structure and backend APIs

**Tasks**:
1. Create `prompts/glossary.json` with initial content for all 4 personas
2. Create `app/glossary.py` module with CRUD operations
3. Add glossary API endpoints to `api_server.py`:
   - `GET /api/glossary` - List all glossaries
   - `GET /api/glossary/{persona}` - Get glossary for a specific persona
   - `GET /api/glossary/{persona}/search?q=term` - Search glossary
   - `POST /api/glossary/{persona}/terms` - Add term
   - `PUT /api/glossary/{persona}/terms/{abbreviation}` - Update term
   - `DELETE /api/glossary/{persona}/terms/{abbreviation}` - Delete term
   - `POST /api/glossary/{persona}/categories` - Add category
   - `PUT /api/glossary/{persona}/categories/{id}` - Update category
   - `DELETE /api/glossary/{persona}/categories/{id}` - Delete category
4. Add Pydantic models for request/response validation

**Deliverables**:
- `prompts/glossary.json`
- `app/glossary.py`
- API endpoints in `api_server.py`

**Tests**: `tests/test_glossary_phase1_data.py`
- Unit tests for glossary CRUD operations
- API endpoint integration tests
- Search functionality tests

---

### Phase 2: Admin UI - Glossary Management Pane

**Objective**: Add a "Glossary" tab to the Admin page for managing terms

**Tasks**:
1. Add 'glossary' to `AdminTab` type in `frontend/src/app/admin/page.tsx`
2. Create `frontend/src/components/admin/GlossaryPanel.tsx`:
   - Term list with search/filter
   - Category grouping (collapsible sections)
   - Add/Edit/Delete term modals
   - Category management
   - Persona selector integration (reacts to current persona)
3. Add API client functions to `frontend/src/lib/api.ts`:
   - `getGlossary(persona)`
   - `searchGlossary(persona, query)`
   - `addGlossaryTerm(persona, term)`
   - `updateGlossaryTerm(persona, abbreviation, term)`
   - `deleteGlossaryTerm(persona, abbreviation)`
   - `addGlossaryCategory(persona, category)`
   - `updateGlossaryCategory(persona, id, category)`
   - `deleteGlossaryCategory(persona, id)`
4. Add TypeScript types to `frontend/src/lib/types.ts`

**Deliverables**:
- `GlossaryPanel.tsx` component
- Admin page integration
- API client functions

**Tests**: `tests/test_glossary_phase2_admin.py`
- Component rendering tests
- CRUD operation tests via API
- Persona switching tests

---

### Phase 3: LLM Prompt Injection

**Objective**: Include glossary context in LLM prompts for document processing and risk analysis

**Tasks**:
1. Modify `app/prompts.py` to load glossary context per persona
2. Create `app/glossary.py::format_glossary_for_prompt(persona)` function:
   - Returns formatted glossary as markdown table
   - Includes only relevant categories based on document type
3. Update `app/processing.py` to inject glossary into:
   - `run_content_understanding_for_files()` - Document extraction prompts
   - `run_underwriting_prompts()` - Analysis prompts
4. Update `prompts/risk-analysis-prompts.json` to include glossary placeholder `{glossary_context}`
5. Update all persona-specific prompt templates to accept glossary injection

**Deliverables**:
- Glossary formatting function
- Updated processing pipeline
- Modified prompt templates

**Tests**: `tests/test_glossary_phase3_llm.py`
- Prompt injection tests
- Glossary formatting tests
- End-to-end processing tests with glossary context

---

### Phase 4: Chat Integration

**Objective**: Inject glossary into chat system prompts for automatic term understanding

**Tasks**:
1. Update `get_chat_system_prompt()` in `api_server.py` to include glossary context
2. Add glossary section to system prompt for each persona:
   ```
   ## Domain Glossary
   The following abbreviations and terms are commonly used:
   {glossary_table}
   
   When the user or documents use these abbreviations, understand them in context.
   ```
3. Optimize glossary size for chat context (prioritize most common terms)
4. Add ability to ask "What does {term} mean?" and get glossary-based response

**Deliverables**:
- Updated chat system prompt generation
- Optimized glossary context for chat

**Tests**: `tests/test_glossary_phase4_chat.py`
- Chat response tests with abbreviation understanding
- Glossary lookup tests
- Context size optimization tests

---

### Phase 5: UI Glossary Dropdown Component

**Objective**: Add a glossary quick-reference dropdown beside the persona selector

**Tasks**:
1. Create `frontend/src/components/GlossaryDropdown.tsx`:
   - Positioned beside `PersonaSelector` in header
   - Alphabetical A-Z navigation
   - Search box for quick lookup
   - Category filters
   - Hover/click to see full meaning
   - Copy abbreviation/meaning buttons
2. Update `frontend/src/components/TopNav.tsx` to include `GlossaryDropdown`
3. Update `frontend/src/components/Sidebar.tsx` for mobile view
4. Add keyboard shortcut (Ctrl+G or Cmd+G) to open glossary
5. Add "Jump to term" functionality from document viewer

**Deliverables**:
- `GlossaryDropdown.tsx` component
- TopNav/Sidebar integration
- Keyboard shortcuts

**Tests**: `tests/test_glossary_phase5_ui.py`
- Component rendering tests
- Navigation tests (A-Z, search)
- Integration tests with document viewer

---

## API Specification

### Endpoints

#### GET /api/glossary
List all available glossaries.

**Response**:
```json
{
  "glossaries": [
    {
      "persona": "underwriting",
      "name": "Life & Health Underwriting",
      "term_count": 58,
      "category_count": 12
    },
    ...
  ]
}
```

#### GET /api/glossary/{persona}
Get the complete glossary for a specific persona.

**Response**:
```json
{
  "persona": "underwriting",
  "name": "Life & Health Underwriting",
  "description": "Medical and insurance terminology for life/health underwriting",
  "categories": [
    {
      "id": "general",
      "name": "General",
      "terms": [
        {
          "abbreviation": "Hx",
          "meaning": "History",
          "context": "Medical context",
          "examples": ["PMHx includes prior surgeries"]
        }
      ]
    }
  ],
  "total_terms": 58
}
```

#### GET /api/glossary/{persona}/search
Search for terms matching a query.

**Query Parameters**:
- `q` (required): Search query
- `category` (optional): Filter by category

**Response**:
```json
{
  "query": "HTN",
  "results": [
    {
      "abbreviation": "HTN",
      "meaning": "Hypertension",
      "category": "Cardiac",
      "context": "Common cardiovascular condition"
    }
  ],
  "total": 1
}
```

#### POST /api/glossary/{persona}/terms
Add a new term to the glossary.

**Request**:
```json
{
  "category_id": "cardiac",
  "abbreviation": "PCI",
  "meaning": "Percutaneous Coronary Intervention",
  "context": "Cardiac procedure",
  "examples": ["Patient underwent PCI in 2024"]
}
```

#### PUT /api/glossary/{persona}/terms/{abbreviation}
Update an existing term.

#### DELETE /api/glossary/{persona}/terms/{abbreviation}
Delete a term from the glossary.

---

## User Interface Mockups

### Admin Glossary Panel

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Admin Panel                                              [Persona: ▼]   │
├─────────────────────────────────────────────────────────────────────────┤
│ [Documents] [Prompts] [Policies] [Glossary] [Analyzer]                  │
├─────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │ Glossary Management - Life & Health Underwriting                    │ │
│ │ ┌───────────────────────────────────┬───────────────────────────┐   │ │
│ │ │ [Search terms...]         [+ Add] │ Categories: [All ▼]       │   │ │
│ │ └───────────────────────────────────┴───────────────────────────┘   │ │
│ │                                                                     │ │
│ │ ▼ General (17 terms)                                                │ │
│ │   ┌─────────┬─────────────────────────────┬──────────┐             │ │
│ │   │ Abbrev  │ Meaning                     │ Actions  │             │ │
│ │   ├─────────┼─────────────────────────────┼──────────┤             │ │
│ │   │ Hx      │ History                     │ [✏️] [🗑️] │             │ │
│ │   │ PMHx    │ Past medical history        │ [✏️] [🗑️] │             │ │
│ │   │ FHx     │ Family history              │ [✏️] [🗑️] │             │ │
│ │   │ ...     │ ...                         │          │             │ │
│ │   └─────────┴─────────────────────────────┴──────────┘             │ │
│ │                                                                     │ │
│ │ ▶ Vitals (5 terms)                                                  │ │
│ │ ▶ Cardiac (10 terms)                                                │ │
│ │ ▶ Endocrine (4 terms)                                               │ │
│ │ ▶ ...                                                               │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### Glossary Dropdown (Header)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ WorkbenchIQ    [🏠 Life & Health Underwriting ▼] [📖 Glossary ▼]        │
│                                                                         │
│                                    ┌────────────────────────────────┐   │
│                                    │ [Search...]              ⌘G    │   │
│                                    ├────────────────────────────────┤   │
│                                    │ A B C D E F G H I J K L M      │   │
│                                    │ N O P Q R S T U V W X Y Z      │   │
│                                    ├────────────────────────────────┤   │
│                                    │ A1C   Hemoglobin A1c           │   │
│                                    │ ACEi  ACE inhibitor            │   │
│                                    │ AF    Atrial fibrillation      │   │
│                                    │ ARB   Angiotensin receptor...  │   │
│                                    │ BB    Beta blocker             │   │
│                                    │ ...                            │   │
│                                    └────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Test Plan Summary

| Phase | Test File | Coverage |
|-------|-----------|----------|
| Phase 1 | `tests/test_glossary_phase1_data.py` | Data layer, CRUD ops, API endpoints |
| Phase 2 | `tests/test_glossary_phase2_admin.py` | Admin UI rendering, form validation |
| Phase 3 | `tests/test_glossary_phase3_llm.py` | Prompt injection, formatting |
| Phase 4 | `tests/test_glossary_phase4_chat.py` | Chat integration, term lookup |
| Phase 5 | `tests/test_glossary_phase5_ui.py` | Dropdown component, navigation |

---

## Dependencies

### Backend
- Existing `app/prompts.py` module
- Existing `app/personas.py` module
- FastAPI framework
- Pydantic for validation

### Frontend
- Existing `PersonaSelector` component
- Existing admin page structure
- React/Next.js
- Tailwind CSS
- Lucide icons

### No New External Dependencies Required

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Large glossary increases prompt token usage | Medium | Medium | Optimize glossary format, use category filtering |
| Term collisions across personas | Low | Low | Unique term IDs per persona |
| Admin accidentally deletes critical terms | Medium | Low | Confirmation dialogs, versioning |
| Glossary out of sync with industry standards | Medium | Medium | Regular review process, user feedback |

---

## Success Criteria

1. **Phase 1**: All API endpoints functional, glossary loads/saves correctly
2. **Phase 2**: Admin users can add/edit/delete terms without errors
3. **Phase 3**: LLM outputs correctly interpret abbreviations in context
4. **Phase 4**: Chat correctly understands and explains domain terminology
5. **Phase 5**: Users can quickly look up terms with < 2 click interactions

---

## Future Enhancements (Out of Scope)

1. **Glossary Import/Export** - CSV/Excel import for bulk term management
2. **Usage Analytics** - Track which terms are most queried
3. **Auto-Suggest** - Suggest terms to add based on document content
4. **Multi-Language** - Support glossaries in French/other languages
5. **RAG Integration** - Index glossary for semantic search

