# Tasks: Canadian Mortgage Underwriting Persona

**Input**: Design documents from `/specs/008-mortgage-underwriting/`  
**Prerequisites**: spec.md ✅

---

## Format: `[ID] [Priority] [Phase] Description`

- **[P]**: Can run in parallel with other [P] tasks (different files, no dependencies)
- **[Phase]**: Which phase this task belongs to
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `app/` at repository root
- **Mortgage Module**: `app/mortgage/` (new package)
- **RAG**: `app/rag/` (extend existing)
- **Policies**: `prompts/mortgage-underwriting-policies.json`
- **Tests**: `tests/` at repository root
- **Scripts**: `scripts/` at repository root

---

## Phase 0: Setup Script (One-Command Setup)

**Purpose**: Create unified PowerShell setup script for one-command configuration

**Reference**: `scripts/setup_automotive_claims.ps1` (pattern to follow)

### Setup Script

- [ ] T000 Create `scripts/setup_mortgage_underwriting.ps1` with:
  - Parameter handling: `-StartServers`, `-SkipAzureSetup`, `-VerifyOnly`, `-IndexPoliciesOnly`
  - Environment validation (Python, Node.js, .env file)
  - Python dependency installation (`uv sync` or `pip install`)
  - Package structure creation (`app/mortgage/`, subdirectories)
  - Configuration file updates (config.py, personas.py, unified_indexer.py)
  - Azure analyzer creation via `setup_mortgage_analyzers.py`
  - Policies file creation (`prompts/mortgage-underwriting-policies.json`)
  - Policy indexing via `index_mortgage_policies.py`
  - Frontend dependency installation (`npm install`)
  - Server startup (API + frontend) when `-StartServers` flag provided
  - Browser launch to http://localhost:3000

- [ ] T000a Create `scripts/setup_mortgage_analyzers.py` with:
  - `--create-all` flag to create mortgage document analyzer
  - `--verify` flag to check analyzer exists
  - `--delete` flag for cleanup
  - Field definitions for T4, pay stub, employment letter, appraisal, etc.

- [ ] T000b Create `scripts/index_mortgage_policies.py` with:
  - Load policies from `prompts/mortgage-underwriting-policies.json`
  - Use unified indexer with `persona="mortgage_underwriting"`
  - Verify chunk count after indexing

**Checkpoint**: `.\scripts\setup_mortgage_underwriting.ps1 -StartServers` runs end-to-end

---

## Phase 1: Infrastructure & Configuration

**Purpose**: Set up package structure, environment variables, and persona configuration

**Test File**: `tests/test_mortgage_phase1_config.py`

### Package Structure

- [ ] T001 Create `app/mortgage/` package directory
- [ ] T002 [P] Create `app/mortgage/__init__.py` with public exports:
  ```python
  from .engine import MortgagePolicyEngine
  from .calculator import MortgageCalculator
  from .policies import MortgagePolicyLoader
  ```
- [ ] T003 [P] Create `app/mortgage/constants.py` with status enums and constants

### Configuration

- [ ] T004 Add mortgage underwriting environment variables to `app/config.py`:
  - `MORTGAGE_UNDERWRITING_ENABLED`
  - `MORTGAGE_DOC_ANALYZER`
  - `MORTGAGE_POLICIES_PATH`
  - `OSFI_MQR_FLOOR_PCT`
  - `OSFI_MQR_BUFFER_PCT`
  - `GDS_LIMIT_STANDARD`
  - `TDS_LIMIT_STANDARD`
- [ ] T005 Create `app/config.py::MortgageUnderwritingSettings` dataclass with from_env pattern

### Persona Update

- [ ] T006 Add `MORTGAGE_UNDERWRITING` to `PersonaType` enum in `app/personas.py` (distinct from existing MORTGAGE stub)
- [ ] T007 Create comprehensive `MORTGAGE_UNDERWRITING_FIELD_SCHEMA` in `app/personas.py` per Canada schema
- [ ] T008 Create `MORTGAGE_UNDERWRITING_DEFAULT_PROMPTS` in `app/personas.py`
- [ ] T009 Update `PERSONA_CONFIGS` registry with mortgage_underwriting persona config
- [ ] T010 Mark existing `MORTGAGE` stub as legacy alias to `MORTGAGE_UNDERWRITING`

### Unified Indexer Update

- [ ] T011 Add `mortgage_underwriting` to `PERSONA_CONFIG` in `app/rag/unified_indexer.py`:
  ```python
  "mortgage_underwriting": {
      "policies_path": "prompts/mortgage-underwriting-policies.json",
      "table_name": "mortgage_policy_chunks",
      "display_name": "Mortgage Underwriting",
  },
  ```

### Frontend Persona Update

- [ ] T012 Update `PersonaId` type in `frontend/src/lib/personas.ts` to include `mortgage_underwriting`
- [ ] T013 Update `PERSONAS` object with mortgage_underwriting configuration
- [ ] T014 Create `MortgageWorkbench` component stub in `frontend/src/components/mortgage/`

**Checkpoint**: Configuration validated, persona appears in UI dropdown

---

## Phase 2: Document Type Classification & Routing

**Purpose**: Implement mortgage document type detection and analyzer routing

**Test File**: `tests/test_mortgage_phase2_router.py`

### Document Type Detection

- [ ] T015 Create `app/mortgage/doc_classifier.py` with `MortgageDocClassifier` class
- [ ] T016 Implement `classify_document(file_bytes, filename)` returning document type enum:
  - `application_summary`
  - `employment_letter`
  - `pay_stub`
  - `t4`
  - `notice_of_assessment`
  - `bank_statement`
  - `gift_letter`
  - `purchase_sale_agreement`
  - `appraisal_report`
  - `credit_report`
  - `other`
- [ ] T017 Add filename-based heuristics for document classification
- [ ] T018 Add content-based classification fallback using first page text

### Document Router

- [ ] T019 Create `app/mortgage/router.py` with `MortgageDocRouter` class
- [ ] T020 Implement `get_analyzer_id(doc_type, settings)` routing logic
- [ ] T021 Implement `route_document(file_bytes, filename, settings)` returning `(doc_type, analyzer_id)`
- [ ] T022 Add validation for supported file types (PDF primary)

### Content Understanding Extensions

- [ ] T023 Extend `app/content_understanding_client.py` with mortgage-specific analyze function
- [ ] T024 Add document type parameter to analyzer request
- [ ] T025 Implement provenance extraction (page, bounding region) from CU response

**Checkpoint**: Documents correctly classified and routed to analyzer

---

## Phase 3: Custom Analyzer Setup

**Purpose**: Create and deploy custom Azure CU analyzer for mortgage documents

**Test File**: `tests/test_mortgage_phase3_analyzers.py`

### Analyzer Schema

- [ ] T026 Create `scripts/setup_mortgage_analyzers.py` CLI script
- [ ] T027 Define `mortgageDocAnalyzer` schema extending `prebuilt-document`:
  - Borrower fields (name, DOB, SIN, residency)
  - Employment fields (employer, position, start date, salary)
  - Income fields (base, bonus, commission, other)
  - Property fields (address, type, value, taxes)
  - Loan fields (amount, term, rate, amortization)
  - Credit fields (score, delinquencies)

### Field Schema Definition

```python
MORTGAGE_DOC_ANALYZER_SCHEMA = {
    "analyzerId": "mortgageDocAnalyzer",
    "name": "Canadian Mortgage Document Analyzer",
    "description": "Extracts Canadian mortgage application data from various document types",
    "baseAnalyzerId": "prebuilt-document",
    "fieldSchema": {
        "fields": {
            # Borrower Identity
            "BorrowerFullName": {"type": "string", "method": "extract"},
            "BorrowerDateOfBirth": {"type": "date", "method": "extract"},
            "BorrowerSIN": {"type": "string", "method": "extract"},
            "BorrowerResidencyStatus": {"type": "string", "method": "extract"},
            
            # Employment
            "EmployerName": {"type": "string", "method": "extract"},
            "EmployerAddress": {"type": "string", "method": "extract"},
            "PositionTitle": {"type": "string", "method": "extract"},
            "EmploymentStartDate": {"type": "date", "method": "extract"},
            "EmploymentType": {"type": "string", "method": "extract"},
            
            # Income
            "GrossAnnualSalary": {"type": "string", "method": "extract"},
            "GrossPayPeriodAmount": {"type": "string", "method": "extract"},
            "PayPeriodFrequency": {"type": "string", "method": "extract"},
            "YTDEarnings": {"type": "string", "method": "extract"},
            "BonusAmount": {"type": "string", "method": "extract"},
            "CommissionAmount": {"type": "string", "method": "extract"},
            
            # Property
            "PropertyAddress": {"type": "string", "method": "extract"},
            "PropertyType": {"type": "string", "method": "extract"},
            "PurchasePrice": {"type": "string", "method": "extract"},
            "AppraisedValue": {"type": "string", "method": "extract"},
            "PropertyTaxesAnnual": {"type": "string", "method": "extract"},
            "CondoFeesMonthly": {"type": "string", "method": "extract"},
            
            # Loan
            "RequestedLoanAmount": {"type": "string", "method": "extract"},
            "RequestedAmortization": {"type": "string", "method": "extract"},
            "RequestedTerm": {"type": "string", "method": "extract"},
            "InterestRate": {"type": "string", "method": "extract"},
            "DownPaymentAmount": {"type": "string", "method": "extract"},
            
            # Credit
            "CreditScore": {"type": "number", "method": "extract"},
            "CreditBureau": {"type": "string", "method": "extract"},
            
            # Gift
            "GiftDonorName": {"type": "string", "method": "extract"},
            "GiftAmount": {"type": "string", "method": "extract"},
            "GiftRelationship": {"type": "string", "method": "extract"},
            
            # Tax Documents
            "TaxYear": {"type": "string", "method": "extract"},
            "TotalIncomeFromT4": {"type": "string", "method": "extract"},
            "TotalIncomeFromNOA": {"type": "string", "method": "extract"},
        }
    }
}
```

### Analyzer Deployment

- [ ] T028 Implement `create_analyzer(settings, analyzer_id, schema)` in setup script
- [ ] T029 Implement `get_analyzer(settings, analyzer_id)` to check if exists
- [ ] T030 Implement `update_analyzer(settings, analyzer_id, schema)` for updates
- [ ] T031 Add idempotent deployment (create if not exists, update if changed)
- [ ] T032 Add verification step that tests analyzer with sample mortgage document

**Checkpoint**: Custom analyzer deployed and responding in Azure

---

## Phase 4: Document Processing & Extraction

**Purpose**: Implement document processing with field extraction and provenance

**Test File**: `tests/test_mortgage_phase4_processing.py`

### Processing Service

- [ ] T033 Create `app/mortgage/processor.py` with `MortgageDocProcessor` class
- [ ] T034 Implement `process_document(doc_info, settings)` for single document processing
- [ ] T035 Implement `process_package(documents, settings)` for full package processing
- [ ] T036 Add progress tracking callback for UI updates
- [ ] T037 Add retry logic with exponential backoff for failed analyses

### Field Extraction

- [ ] T038 Create `app/mortgage/extractors/base_extractor.py` with `BaseFieldExtractor`
- [ ] T039 Create `app/mortgage/extractors/borrower_extractor.py`
- [ ] T040 Implement `extract_borrower_fields(cu_result)` returning borrower data with provenance
- [ ] T041 [P] Create `app/mortgage/extractors/income_extractor.py`
- [ ] T042 Implement `extract_income_fields(cu_result)` with annualization logic
- [ ] T043 [P] Create `app/mortgage/extractors/property_extractor.py`
- [ ] T044 Implement `extract_property_fields(cu_result)` with valuation handling
- [ ] T045 [P] Create `app/mortgage/extractors/loan_extractor.py`
- [ ] T046 Implement `extract_loan_fields(cu_result)` with term parsing
- [ ] T047 [P] Create `app/mortgage/extractors/credit_extractor.py`
- [ ] T048 Implement `extract_credit_fields(cu_result)` with score normalization

### Result Aggregation

- [ ] T049 Create `app/mortgage/aggregator.py` with `MortgageCaseAggregator` class
- [ ] T050 Implement `aggregate_borrower_data(docs)` merging borrower info across documents
- [ ] T051 Implement `aggregate_income_data(docs)` combining income sources with reconciliation
- [ ] T052 Implement `detect_inconsistencies(case_data)` flagging cross-document conflicts
- [ ] T053 Implement `build_canonical_case(docs)` creating unified case model per schema

### Provenance Tracking

- [ ] T054 Create `app/mortgage/provenance.py` with `ProvenanceTracker` class
- [ ] T055 Implement `track_field(field_name, value, doc_id, page, region)` for field attribution
- [ ] T056 Implement `get_field_sources(field_name)` returning all sources for a field
- [ ] T057 Implement `resolve_conflict(field_name, winner_doc_id, note)` for conflict resolution

### JSON Storage Integration

- [ ] T058 Create `app/mortgage/storage.py` with JSON-based storage operations
- [ ] T059 Implement `save_mortgage_case(case_id, case_data)` persisting to `data/applications/{case_id}/metadata.json`
- [ ] T060 Implement `save_content_understanding(case_id, extraction_result)` saving to `content_understanding.json`
- [ ] T061 Implement `update_mortgage_case(case_id, updates)` merging updates into existing case
- [ ] T062 Implement `get_mortgage_case(case_id)` loading full case from JSON storage

**Note**: Following unified approach - applications/conversations stored as JSON files, only policy chunks in PostgreSQL.

**Checkpoint**: Documents processed, fields extracted with provenance, data stored in JSON

---

## Phase 5: Calculation Engine

**Purpose**: Implement GDS/TDS/LTV calculations with OSFI stress test

**Test File**: `tests/test_mortgage_phase5_calculator.py`

### Calculation Service

- [ ] T063 Create `app/mortgage/calculator.py` with `MortgageCalculator` class
- [ ] T064 Implement `compute_monthly_income(income_sources)` with annualization and haircuts
- [ ] T065 Implement `compute_mortgage_payment(principal, rate, amortization)` using standard formula
- [ ] T066 Implement `compute_housing_costs(piti, condo_fees, heating)` summing components
- [ ] T067 Implement `compute_qualifying_rate(contract_rate, settings)` applying OSFI MQR
- [ ] T068 Implement `compute_gds(housing_costs, monthly_income)` returning ratio
- [ ] T069 Implement `compute_tds(housing_costs, other_debts, monthly_income)` returning ratio
- [ ] T070 Implement `compute_ltv(loan_amount, property_value)` returning ratio
- [ ] T071 Implement `compute_combined_ltv(loan_amount, secondary_financing, property_value)`

### Stress Test Implementation

- [ ] T072 Create `app/mortgage/stress_test.py` with `OSFIStressTest` class
- [ ] T073 Implement `apply_mqr(contract_rate, floor_rate, buffer)` returning qualifying rate
- [ ] T074 Implement `compute_stress_gds(case_data, qualifying_rate)` computing stressed GDS
- [ ] T075 Implement `compute_stress_tds(case_data, qualifying_rate)` computing stressed TDS
- [ ] T076 Implement `is_insured_mortgage(product_type)` determining if MQR applies

### Calculation Provenance

- [ ] T077 Create `CalculationResult` dataclass with inputs, formula, result, and provenance
- [ ] T078 Implement input tracking - link each calculation input to source field
- [ ] T079 Implement `save_calculations(case_id, calculations)` persisting to `mortgage_calculations`
- [ ] T080 Implement `get_calculations(case_id)` with full audit trail

### Income Qualification Rules

- [ ] T081 Implement income type haircuts (commission @ 50%, bonus @ 50%, rental @ 50% with offset)
- [ ] T082 Implement probationary income handling (reduce or exclude)
- [ ] T083 Implement self-employed income averaging (2-year average of net income)
- [ ] T084 Implement variable income blending (base + averaged variable)

**Checkpoint**: All calculations complete with provenance and stress test applied

---

## Phase 6: Mortgage Policy Engine

**Purpose**: Implement policy-based application evaluation with OSFI compliance

**Test File**: `tests/test_mortgage_phase6_policy_engine.py`

### Policy Data

- [ ] T085 Create `prompts/mortgage-underwriting-policies.json` with policies per spec
- [ ] T086 Create `app/mortgage/policies.py` with `MortgagePolicyLoader` class (adapt from claims)
- [ ] T087 Implement `load_policies(path)` returning structured policy objects
- [ ] T088 Implement `get_policies_by_category(category)` filtering
- [ ] T089 Implement `get_osfi_rules()` returning regulatory rules

### Policy Engine

- [ ] T090 Create `app/mortgage/engine.py` with `MortgagePolicyEngine` class
- [ ] T091 Implement `evaluate_gds_tds(calculations)` applying DSR limit policies
- [ ] T092 Implement `evaluate_ltv(calculations, product_type)` applying LTV policies
- [ ] T093 Implement `evaluate_credit(credit_profile)` applying credit score policies
- [ ] T094 Implement `evaluate_down_payment(down_payment_sources)` applying source verification policies
- [ ] T095 Implement `evaluate_income_consistency(case_data)` applying consistency policies
- [ ] T096 Implement `evaluate_documentation(documents)` applying completeness policies
- [ ] T097 Implement `evaluate_case(case_data)` running all applicable rules

### Policy Findings

- [ ] T098 Create `PolicyFinding` dataclass per schema (ruleId, status, severity, summary, evidence)
- [ ] T099 Implement evidence linking - attach document/page/field references to each finding
- [ ] T100 Implement finding aggregation - combine findings into overall recommendation

### Decision Support

- [ ] T101 Implement `generate_recommendation(findings)` computing recommended outcome
- [ ] T102 Implement `generate_conditions(findings)` creating conditions list for approval
- [ ] T103 Implement `generate_underwriting_note(case_data, findings)` AI-drafted narrative
- [ ] T104 Implement exception handling - track which rules allow exceptions

### Persistence

- [ ] T105 Implement `save_policy_findings(case_id, findings)` to database
- [ ] T106 Implement `save_decision(case_id, decision)` to `mortgage_decisions` table
- [ ] T107 Implement `lock_audit_snapshot(case_id)` creating immutable decision record

**Checkpoint**: Policy engine evaluates applications and generates recommendations

---

## Phase 7: Risk Analysis Service

**Purpose**: Implement income consistency checking and fraud/AML signal detection

**Test File**: `tests/test_mortgage_phase7_risk.py`

### Income Consistency

- [ ] T108 Create `app/mortgage/risk/income_analyzer.py` with `IncomeConsistencyAnalyzer`
- [ ] T109 Implement `compare_income_sources(t4, pay_stub, application)` returning variance
- [ ] T110 Implement `flag_inconsistencies(case_data, threshold_pct)` returning signals
- [ ] T111 Implement `analyze_income_stability(employment_history)` assessing tenure/gaps

### Fraud Detection

- [ ] T112 Create `app/mortgage/risk/fraud_detector.py` with `MortgageFraudDetector`
- [ ] T113 Implement `detect_document_anomalies(documents)` checking metadata/fonts
- [ ] T114 Implement `detect_large_deposits(bank_statements, threshold)` flagging unexplained funds
- [ ] T115 Implement `detect_employment_red_flags(employment_data)` checking employer validity
- [ ] T116 Implement `detect_straw_buyer_indicators(case_data)` checking occupancy/relationship patterns

### AML Triage

- [ ] T117 Create `app/mortgage/risk/aml_triage.py` with `AMLTriageService`
- [ ] T118 Implement `check_source_of_funds(down_payment_sources)` verifying fund origins
- [ ] T119 Implement `check_pep_indicators(borrower_data)` (placeholder for PEP screening)
- [ ] T120 Implement `escalate_to_compliance(case_id, flags)` triggering compliance workflow

### Risk Tier Assessment

- [ ] T121 Create `app/mortgage/risk/risk_scorer.py` with `RiskTierScorer`
- [ ] T122 Implement `compute_risk_tier(signals)` returning low/medium/high/very_high
- [ ] T123 Implement `get_top_risk_contributors(case_data)` returning prioritized risk factors
- [ ] T124 Implement `save_risk_assessment(case_id, assessment)` persisting to database

**Checkpoint**: Risk signals detected and risk tier computed

---

## Phase 8: RAG for Mortgage Policies

**Purpose**: Enable semantic search over mortgage underwriting policies in Ask IQ

**Test File**: `tests/test_mortgage_phase8_rag.py`

### Policy Chunking

- [ ] T125 Create `app/mortgage/chunker.py` with `MortgagePolicyChunker` class
- [ ] T126 Implement `chunk_policy(policy)` creating semantic chunks
- [ ] T127 Implement chunking for all chunk types: header, criteria, modifying_factor, reference

### Embedding & Indexing (via Unified Indexer)

- [ ] T128 Verify `mortgage_underwriting` config in `app/rag/unified_indexer.py`
- [ ] T129 Create `scripts/index_mortgage_policies.py` CLI for manual indexing
- [ ] T130 Implement indexing using existing unified indexer pattern:
  ```python
  indexer = UnifiedPolicyIndexer(persona="mortgage_underwriting", settings=settings)
  await indexer.index_all()
  ```
- [ ] T131 Add progress logging and validation

### Search Integration

- [ ] T132 Verify `app/rag/persona_search.py` supports `mortgage_underwriting` persona
- [ ] T133 Add mortgage-specific category inference in `app/rag/inference.py`:
  - `osfi_regulatory` - OSFI B-20, MQR
  - `credit_evaluation` - Credit score, bureau
  - `income_qualification` - GDS, TDS, income types
  - `collateral_valuation` - LTV, appraisal
  - `down_payment` - Source of funds
  - `aml_fraud` - AML, fraud detection
- [ ] T134 Test semantic search with mortgage-specific queries
- [ ] T135 Test hybrid search (keyword + semantic) for mortgage policies

### Ask IQ Integration

- [ ] T136 Update Ask IQ chat endpoint to support `mortgage_underwriting` persona
- [ ] T137 Implement case-aware context injection for mortgage questions
- [ ] T138 Add policy citation formatting for mortgage responses

**Checkpoint**: Ask IQ retrieves relevant mortgage policies for underwriting questions

---

## Phase 9: API Endpoints

**Purpose**: Expose mortgage processing, calculations, and decisions via REST API

**Test File**: `tests/test_mortgage_phase9_api.py`

### Case Management Endpoints

- [ ] T139 Create `POST /api/mortgage/cases` endpoint for new case creation
- [ ] T140 Create `GET /api/mortgage/cases/{caseId}` endpoint with full case retrieval
- [ ] T141 Create `PUT /api/mortgage/cases/{caseId}/status` for status updates
- [ ] T142 Create `GET /api/mortgage/cases` with filtering (status, province, risk tier)

### Document Upload Endpoints

- [ ] T143 Create `POST /api/mortgage/cases/{caseId}/documents` for document upload
- [ ] T144 Implement document classification on upload
- [ ] T145 Create `GET /api/mortgage/cases/{caseId}/documents` listing all documents
- [ ] T146 Create `GET /api/mortgage/cases/{caseId}/documents/{docId}` with extractions

### Processing Endpoints

- [ ] T147 Create `POST /api/mortgage/cases/{caseId}/process` to trigger package processing
- [ ] T148 Create `GET /api/mortgage/cases/{caseId}/processing-status` for progress
- [ ] T149 Add WebSocket or SSE endpoint for real-time processing updates

### Calculation Endpoints

- [ ] T150 Create `GET /api/mortgage/cases/{caseId}/calculations` returning all calculations
- [ ] T151 Create `POST /api/mortgage/cases/{caseId}/calculations/recalculate` for manual recalc
- [ ] T152 Add calculation override support with audit note

### Policy Evaluation Endpoints

- [ ] T153 Create `GET /api/mortgage/cases/{caseId}/policy-findings` returning all findings
- [ ] T154 Create `POST /api/mortgage/cases/{caseId}/policy-findings/{findingId}/exception` for exception request
- [ ] T155 Add exception approval endpoint for senior underwriters

### Decision Endpoints

- [ ] T156 Create `POST /api/mortgage/cases/{caseId}/decision` for submitting decision
- [ ] T157 Create `GET /api/mortgage/cases/{caseId}/decision` returning decision with audit
- [ ] T158 Create `GET /api/mortgage/cases/{caseId}/audit-snapshot` for audit export

### Risk Endpoints

- [ ] T159 Create `GET /api/mortgage/cases/{caseId}/risk` returning risk assessment
- [ ] T160 Create `POST /api/mortgage/cases/{caseId}/risk/escalate` for AML escalation

**Checkpoint**: Full API functional, can process cases and submit decisions

---

## Phase 10: Frontend UX - Mortgage Workbench

**Purpose**: Build underwriter workbench interface for mortgage case review

**Test File**: Manual testing / E2E tests

### Workbench Layout

- [ ] T161 Create `frontend/src/components/mortgage/MortgageWorkbench.tsx` with 3-column layout
- [ ] T162 Create left column: `EvidencePanel.tsx` with document list
- [ ] T163 Create center column: `DataPolicyPanel.tsx` with tabs
- [ ] T164 Create right column: `RiskNarrativePanel.tsx` with risk and notes

### Evidence Panel (Left)

- [ ] T165 Create `frontend/src/components/mortgage/evidence/DocumentList.tsx`
- [ ] T166 Implement document grouping by type (Income, Property, Credit, etc.)
- [ ] T167 Implement document status badges (ok, missing, expired, low_confidence)
- [ ] T168 Implement document viewer with page navigation
- [ ] T169 Implement field highlight overlay showing extracted regions
- [ ] T170 Add provenance chip - hover shows doc/page/region

### Data Worksheet Tab

- [ ] T171 Create `frontend/src/components/mortgage/data/DataWorksheet.tsx`
- [ ] T172 Implement canonical data tree (Borrowers, Property, Loan sections)
- [ ] T173 Implement field display with value, confidence, source badges
- [ ] T174 Implement inline edit with note requirement
- [ ] T175 Implement conflict banner when multiple sources disagree
- [ ] T176 Create conflict resolver side-by-side comparison

### Calculations Tab

- [ ] T177 Create `frontend/src/components/mortgage/calculations/CalculationsView.tsx`
- [ ] T178 Implement GDS/TDS display at contract rate AND stress rate
- [ ] T179 Implement LTV display with progress bar
- [ ] T180 Implement inputs table with provenance links
- [ ] T181 Implement toggle for conservative overrides
- [ ] T182 Add "Explain this" drawer expanding calculation formula

### Policy Checks Tab

- [ ] T183 Create `frontend/src/components/mortgage/policy/PolicyCheckList.tsx`
- [ ] T184 Implement rule list with status chips (pass/fail/needs_review/exception_required)
- [ ] T185 Implement rule detail drawer showing:
  - Rule intent & threshold
  - Inputs used with evidence links
  - System rationale
  - Underwriter resolution actions
- [ ] T186 Implement exception request form with compensating factors

### Conditions Tab

- [ ] T187 Create `frontend/src/components/mortgage/conditions/ConditionsPanel.tsx`
- [ ] T188 Implement auto-generated conditions list
- [ ] T189 Implement condition templates linked to missing/failed requirements
- [ ] T190 Implement "Send to borrower/broker" pack generation

### Risk Panel (Right)

- [ ] T191 Create `frontend/src/components/mortgage/risk/RiskPanel.tsx`
- [ ] T192 Implement risk tier badge with top contributors
- [ ] T193 Implement fraud/AML signals section (if any)
- [ ] T194 Implement AI draft underwriting note (editable) with citations
- [ ] T195 Implement "What would change the decision?" recommendations

### Decision Controls

- [ ] T196 Create `frontend/src/components/mortgage/decision/DecisionPanel.tsx`
- [ ] T197 Implement decision buttons: Approve | Refer | Decline | Pending Info
- [ ] T198 Implement conditions checklist for funding
- [ ] T199 Implement exception approval workflow (role-based)
- [ ] T200 Implement audit snapshot lock confirmation

### Queue/Inbox View

- [ ] T201 Create `frontend/src/components/mortgage/queue/CaseQueue.tsx`
- [ ] T202 Implement table with columns: Case ID, Applicant(s), Province, Purpose, LTV, GDS/TDS, Flags, SLA timer
- [ ] T203 Implement filters: risk tier, missing docs, exceptions, channel, province
- [ ] T204 Implement bulk actions: assign, request docs, set status

### Persona Page Integration

- [ ] T205 Update `frontend/src/app/page.tsx` to render `MortgageWorkbench` for mortgage_underwriting
- [ ] T206 Add mortgage_underwriting to persona selector with 🏠 icon

**Checkpoint**: Full UX complete, underwriters can review and decide cases

---

## Phase 11: PostgreSQL Policy Chunks Migration

**Purpose**: Create the single PostgreSQL table for policy RAG (applications stored in JSON)

**Test File**: `tests/test_mortgage_phase11_migrations.py`

**Note**: This phase only creates the `mortgage_policy_chunks` table. Applications, documents, 
borrowers, calculations, and decisions are stored in JSON files following the unified pattern.

### Migration File

- [ ] T207 Create `migrations/012_create_mortgage_policy_chunks.sql`:
  ```sql
  -- Only table needed for mortgage persona (applications use JSON storage)
  CREATE TABLE IF NOT EXISTS workbenchiq.mortgage_policy_chunks (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      policy_id VARCHAR(50) NOT NULL,
      policy_version VARCHAR(20) NOT NULL DEFAULT '1.0',
      policy_name VARCHAR(200) NOT NULL,
      chunk_type VARCHAR(30) NOT NULL,
      chunk_sequence INTEGER NOT NULL DEFAULT 0,
      category VARCHAR(50) NOT NULL,
      subcategory VARCHAR(50),
      criteria_id VARCHAR(50),
      risk_level VARCHAR(30),
      action_recommendation TEXT,
      content TEXT NOT NULL,
      content_hash VARCHAR(64) NOT NULL,
      token_count INTEGER NOT NULL DEFAULT 0,
      embedding VECTOR(1536) NOT NULL,
      embedding_model VARCHAR(50) DEFAULT 'text-embedding-3-small',
      metadata JSONB DEFAULT '{}',
      created_at TIMESTAMPTZ DEFAULT NOW(),
      updated_at TIMESTAMPTZ DEFAULT NOW()
  );
  ```
- [ ] T208 Create HNSW vector index for embedding search
- [ ] T209 Create unique index for upsert operations
- [ ] T210 Add mortgage_underwriting to `PERSONA_CONFIG` in unified indexer
- [ ] T211 Create `prompts/mortgage-underwriting-policies.json` policy file
- [ ] T212 Run unified indexer to populate mortgage policy chunks
- [ ] T213 Update `app/database/migrate.py` to include new migration

### Verification

- [ ] T214 Verify `mortgage_policy_chunks` table created with correct schema
- [ ] T215 Verify vector index is functional
- [ ] T216 Test semantic search against mortgage policies

**Checkpoint**: Policy RAG table created, indexed, and populated

---

## Validation Checklist

After Phase 10 completion (MVP):

- [ ] V001 Documents correctly classified by type (application, T4, pay stub, etc.)
- [ ] V002 Fields extracted with provenance linking to source document/page
- [ ] V003 GDS/TDS calculated correctly at contract rate
- [ ] V004 OSFI MQR stress test applied to uninsured mortgages
- [ ] V005 LTV computed and validated against product limits
- [ ] V006 Policy findings generated with pass/fail/needs_review status
- [ ] V007 Income inconsistencies detected when variance > 5%
- [ ] V008 Risk tier computed based on signals
- [ ] V009 Ask IQ retrieves relevant mortgage policies
- [ ] V010 Underwriter can review case in 3-column workbench
- [ ] V011 Underwriter can submit decision with conditions
- [ ] V012 Case data persisted to JSON files (metadata.json, content_understanding.json)
- [ ] V013 Policy chunks indexed in PostgreSQL for RAG search

---

## Test File Mapping

| Phase | Test File | Description |
|-------|-----------|-------------|
| Phase 1 | `tests/test_mortgage_phase1_config.py` | Config loading, persona registry |
| Phase 2 | `tests/test_mortgage_phase2_router.py` | Document classification, routing |
| Phase 3 | `tests/test_mortgage_phase3_analyzers.py` | Analyzer creation/verification |
| Phase 4 | `tests/test_mortgage_phase4_processing.py` | Document processing, extraction |
| Phase 5 | `tests/test_mortgage_phase5_calculator.py` | GDS/TDS/LTV calculations |
| Phase 6 | `tests/test_mortgage_phase6_policy_engine.py` | Policy evaluation |
| Phase 7 | `tests/test_mortgage_phase7_risk.py` | Risk analysis, fraud detection |
| Phase 8 | `tests/test_mortgage_phase8_rag.py` | Policy chunking, search |
| Phase 9 | `tests/test_mortgage_phase9_api.py` | REST API endpoints |
| Phase 10 | Manual / E2E | Frontend UX testing |
| Phase 11 | `tests/test_mortgage_phase11_migrations.py` | Policy chunks table migration |

---

## Reuse from Existing Codebase

| Component | Source | Adaptation |
|-----------|--------|------------|
| Unified RAG Service | `app/rag/service.py` | Use with `persona="mortgage_underwriting"` |
| Unified Indexer | `app/rag/unified_indexer.py` | Add `mortgage_underwriting` to `PERSONA_CONFIG` |
| Policy Loader | `app/claims/policies.py` | Copy and adapt for `MortgagePolicyLoader` |
| Policy Engine | `app/claims/engine.py` | Copy and adapt for `MortgagePolicyEngine` |
| Policy Chunker | `app/claims/chunker.py` | Copy and adapt for `MortgagePolicyChunker` |
| MIME Detector | `app/multimodal/mime_detector.py` | Reuse for PDF detection |
| Persona Config | `app/personas.py` | Extend with `MORTGAGE_UNDERWRITING` |
| Prompts System | `app/prompts.py` | Use existing pattern |
| Content Understanding | `app/content_understanding_client.py` | Extend for mortgage analyzer |

---

## Learnings & Notes

*(To be updated during implementation)*

### Canadian Mortgage Specifics
- OSFI MQR floor rate (5.25%) may change - use configuration variable
- GDS/TDS limits vary by lender - make configurable
- Rental income haircut (typically 50%) with offset rules
- Self-employed income requires 2-year average from T1/NOA

### Document Types
- T4 is the primary employment income document
- NOA (Notice of Assessment) confirms CRA-reported income
- Pay stubs should be within 30 days of application
- Gift letters require relationship declaration and "no repayment" clause

### Calculation Notes
- Monthly income = Annual / 12 (after haircuts)
- Mortgage payment formula: P&I = P * [r(1+r)^n] / [(1+r)^n - 1]
- Heating estimate: typically $75-$150/month if not specified
- Condo fees: only 50% counted toward GDS in some lender policies
