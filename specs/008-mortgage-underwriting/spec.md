# Feature Specification: Canadian Mortgage Underwriting Persona

**Feature Branch**: `008-mortgage-underwriting`  
**Created**: 2026-01-22  
**Status**: Draft  
**Input**: User description: "Add a mortgage_underwriting persona leveraging the unified RAG service, unified indexer, unified prompts engine, Ask IQ RAG engine, analyzers targeted for mortgage, and risk analysis service. Focused on Canadian mortgage underwriting with OSFI B-20 compliance."

---

## Overview

This specification defines a new **Mortgage Underwriting** persona for the Canadian residential mortgage market. The implementation leverages existing infrastructure from the automotive claims multimodal feature (spec-007) while adapting it for mortgage document processing, regulatory compliance checking, and underwriting decision support.

### Key Differentiators from Automotive Claims

| Aspect | Automotive Claims | Mortgage Underwriting |
|--------|-------------------|----------------------|
| Document Types | Damage photos, repair estimates, police reports | Income docs (T4, pay stubs, NOA), property docs (appraisal, APS), credit reports |
| Multimodal | Images, videos, documents | Primarily documents (PDFs), occasional property photos |
| Regulatory | Insurance regulations | OSFI B-20, provincial mortgage rules |
| Decision | Payout calculation | Approve/Decline/Refer with conditions |
| Risk Focus | Fraud detection, damage severity | Credit risk, income stability, LTV/GDS/TDS |
| Calculations | Liability %, payout range | GDS, TDS, LTV, stress test qualifying rate |

### Goals

1. **Document Processing** - Extract borrower, property, income, and loan data from Canadian mortgage application packages
2. **Regulatory Compliance** - Apply OSFI B-20 rules including MQR stress testing for uninsured mortgages
3. **Unified Infrastructure** - Leverage existing RAG service, indexer, prompts engine, and Ask IQ for policy-aware chat
4. **Risk Analysis** - Identify income inconsistencies, AML flags, and credit risk signals
5. **Evidence-First UX** - Traceable decisions with document provenance for every data point
6. **Policy Engine** - Evaluate applications against configurable underwriting rules with audit trail

---

## User Stories

### US-1: Mortgage Document Package Upload (Priority: P0)
> As an admin, I want to upload a complete mortgage application package (application, income docs, property docs, credit report) via the admin view, so that all documents are processed and analyzed together.

**Acceptance Scenarios**:
1. **Given** an admin uploads a mortgage application PDF via admin view, **When** processing starts, **Then** the system routes it to the mortgage document analyzer.
2. **Given** an admin uploads income documents (T4, pay stubs, NOA) via admin view, **When** processing starts, **Then** the system extracts income fields with source attribution.
3. **Given** an admin uploads property documents (appraisal, purchase agreement) via admin view, **When** processing starts, **Then** the system extracts property and valuation fields.
4. **Given** all documents are processed, **When** viewing the case, **Then** results are aggregated into a unified mortgage case view.

---

### US-2: Canadian Mortgage Field Extraction (Priority: P0)
> As a mortgage underwriter, I want the system to extract standard Canadian mortgage fields (borrower info, income, property, loan terms) from all document types, so that I have structured data for processing.

**Acceptance Scenarios**:
1. **Given** a mortgage application package, **When** extraction completes, **Then** borrower details (name, DOB, SIN, residency status) are extracted with source attribution.
2. **Given** income documents, **When** extraction completes, **Then** employment details, salary, and income sources are structured with document provenance.
3. **Given** property documents, **When** extraction completes, **Then** property type, address, valuation, and purchase price are extracted.
4. **Given** conflicting data across documents (e.g., income on application vs. T4), **When** displayed, **Then** the system shows all values with sources for underwriter resolution.

---

### US-3: OSFI B-20 Stress Test Calculations (Priority: P0)
> As a mortgage underwriter, I want the system to automatically calculate GDS/TDS at both contract rate and OSFI qualifying rate, so that I can assess debt serviceability per regulatory requirements.

**Acceptance Scenarios**:
1. **Given** extracted income and debt data, **When** calculations run, **Then** the system computes monthly housing costs (P&I, taxes, heating, condo fees).
2. **Given** an uninsured mortgage, **When** stress test applies, **Then** the system qualifies at the greater of contract rate + 2% or 5.25% (current MQR floor).
3. **Given** calculated ratios, **When** displayed, **Then** underwriter sees GDS/TDS at contract rate AND qualifying rate with input traceability.
4. **Given** stress test TDS exceeds 44%, **When** policy rules apply, **Then** the system flags the case for review with specific ratio values.

---

### US-4: Policy Rule Engine for Mortgage (Priority: P1)
> As a mortgage underwriter, I want the system to apply Canadian mortgage underwriting policies to evaluate applications, so that I have consistent, policy-based recommendations with audit trail.

**Acceptance Scenarios**:
1. **Given** extracted case data, **When** policy rules run, **Then** the system returns pass/fail/needs_review status for each rule with rationale.
2. **Given** LTV calculation, **When** rules apply, **Then** the system validates LTV against product limits (e.g., >80% requires insurance).
3. **Given** down payment sources, **When** rules apply, **Then** the system flags unverified sources and requests documentation.
4. **Given** credit bureau data, **When** rules apply, **Then** the system evaluates delinquencies, utilization, and score thresholds.
5. **Given** policy findings, **When** viewing the case, **Then** each finding links to the triggering evidence with document/page reference.

---

### US-5: Income Consistency and Fraud Detection (Priority: P1)
> As a mortgage underwriter, I want the system to identify income inconsistencies and potential fraud indicators, so that I can focus review on high-risk areas.

**Acceptance Scenarios**:
1. **Given** income from multiple sources (pay stub, T4, employment letter), **When** analyzed, **Then** the system flags discrepancies exceeding 5%.
2. **Given** bank statements, **When** analyzed, **Then** the system identifies large unexplained deposits requiring source of funds explanation.
3. **Given** document metadata, **When** analyzed, **Then** the system flags potential alterations (font inconsistencies, metadata anomalies).
4. **Given** AML triggers, **When** detected, **Then** the system escalates to compliance workflow without finalizing decision.

---

### US-6: Ask IQ RAG for Mortgage Policies (Priority: P1)
> As a mortgage underwriter, I want to ask natural language questions about underwriting policies and have the system retrieve relevant policy sections, so that I can make informed decisions.

**Acceptance Scenarios**:
1. **Given** a question "What is the MQR for uninsured mortgages?", **When** searched, **Then** the system returns OSFI B-20 MQR policy chunks with citations.
2. **Given** a question "How do I qualify rental income?", **When** searched, **Then** the system returns income qualification policies with rental-specific guidance.
3. **Given** policy chunks retrieved, **When** displayed in chat, **Then** each chunk includes policy ID, section, and effective date.
4. **Given** conversation history, **When** chatting about a specific case, **Then** the system combines case context with policy knowledge.

---

### US-7: Underwriter Workbench UX (Priority: P1)
> As a mortgage underwriter, I want a unified view showing documents, extracted data, calculations, policy checks, and risk signals, so that I can efficiently review and decide applications.

**Acceptance Scenarios**:
1. **Given** a processed case, **When** viewing the workspace, **Then** I see a 3-column layout: Evidence (left), Data+Policy (center), Risk+Narrative (right).
2. **Given** calculated GDS/TDS, **When** viewing calculations tab, **Then** I see input values with provenance badges linking to source documents.
3. **Given** policy rule failures, **When** viewing policy tab, **Then** I see rule details, threshold vs. actual value, and exception request option.
4. **Given** an exception required, **When** requesting, **Then** I can document compensating factors and route to senior approver.
5. **Given** final decision, **When** submitted, **Then** the system locks an audit snapshot with all data, calculations, rules, and user actions.

---

## Architecture

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (Next.js)                              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Mortgage Underwriter Workbench                                       │    │
│  │ - 3-column layout: Evidence | Data+Policy | Risk+Narrative           │    │
│  │ - Provenance chips on all extracted fields                           │    │
│  │ - GDS/TDS calculator with stress test toggle                         │    │
│  │ - Policy rule status list with exception workflow                    │    │
│  │ - Decision buttons: Approve | Refer | Decline | Pending Info         │    │
│  │ (File upload via Admin View - same pattern as other personas)        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ REST API
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND (FastAPI)                               │
│                                                                              │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐    │
│  │ Upload Endpoint    │  │ Mortgage Router    │  │ Mortgage Policy    │    │
│  │ /api/.../upload    │─▶│ - Doc type detect  │  │ Engine             │    │
│  │                    │  │ - Analyzer routing │  │ - Rule evaluation  │    │
│  └────────────────────┘  └────────────────────┘  │ - GDS/TDS calc     │    │
│                                    │             │ - Decision support │    │
│                                    │             └────────────────────┘    │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                   Azure Content Understanding                        │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │ mortgageDocAnalyzer (extends prebuilt-document)               │   │    │
│  │  │ - Canadian mortgage field schema                              │   │    │
│  │  │ - Document type classification                                │   │    │
│  │  │ - Income, property, credit field extraction                   │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│  ┌─────────────────────────────────┴───────────────────────────────────┐    │
│  │                   Unified Services (Reused from spec-007)            │    │
│  │                                                                      │    │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐ │    │
│  │  │ Unified RAG    │  │ Unified        │  │ Risk Analysis          │ │    │
│  │  │ Service        │  │ Indexer        │  │ Service                │ │    │
│  │  │ (persona-aware)│  │ (parameterized)│  │ (fraud/AML signals)    │ │    │
│  │  └────────────────┘  └────────────────┘  └────────────────────────┘ │    │
│  │                                                                      │    │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐ │    │
│  │  │ Ask IQ RAG     │  │ Prompts        │  │ Calculation            │ │    │
│  │  │ Engine         │  │ Engine         │  │ Engine                 │ │    │
│  │  │ (semantic chat)│  │ (per-persona)  │  │ (GDS/TDS/LTV)          │ │    │
│  │  └────────────────┘  └────────────────┘  └────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Azure PostgreSQL Flexible Server                         │
│                          (with pgvector extension)                           │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Schema: workbenchiq                                                   │   │
│  │                                                                       │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐   │   │
│  │  │ mortgage_cases  │  │ mortgage_docs   │  │ mortgage_policy_    │   │   │
│  │  │ - case_id (PK)  │  │ - doc_id (PK)   │  │ chunks              │   │   │
│  │  │ - case_data     │  │ - doc_type      │  │ - embedding VECTOR  │   │   │
│  │  │ - status        │  │ - extractions   │  │ - category          │   │   │
│  │  │ - calculations  │  │ - provenance    │  │ - rule_id           │   │   │
│  │  │ - policy_results│  │ - validation    │  │                     │   │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘   │   │
│  │                                                                       │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐   │   │
│  │  │ mortgage_       │  │ mortgage_       │  │ mortgage_           │   │   │
│  │  │ borrowers       │  │ calculations    │  │ decisions           │   │   │
│  │  │ - borrower_id   │  │ - calc_id       │  │ - decision_id       │   │   │
│  │  │ - income_data   │  │ - gds/tds       │  │ - outcome           │   │   │
│  │  │ - credit_data   │  │ - stress_test   │  │ - conditions        │   │   │
│  │  │ - employment    │  │ - provenance    │  │ - audit_snapshot    │   │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Azure Blob Storage                                       │
│  - Uploaded mortgage documents (PDFs)                                        │
│  - Optional property photos                                                  │
│  - CU raw analysis results                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Mortgage Document Processing Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────────────────────┐
│   Upload     │     │   Document   │     │         Document Router          │
│   Files      │────▶│   Type       │────▶│                                  │
└──────────────┘     │   Detection  │     │  ┌─────────────────────────────┐ │
                     └──────────────┘     │  │ Document Type Classification │ │
                                          │  │                              │ │
                                          │  │ • application_summary        │ │
                                          │  │ • employment_letter          │ │
                                          │  │ • pay_stub                   │ │
                                          │  │ • t4                         │ │
                                          │  │ • notice_of_assessment       │ │
                                          │  │ • bank_statement             │ │
                                          │  │ • gift_letter                │ │
                                          │  │ • purchase_sale_agreement    │ │
                                          │  │ • appraisal_report           │ │
                                          │  │ • credit_report              │ │
                                          │  │ • property_photo             │ │
                                          │  └─────────────────────────────┘ │
                                          └──────────────────────────────────┘
                                                         │
                                                         ▼
                                          ┌──────────────────────────────────┐
                                          │   mortgageDocAnalyzer            │
                                          │   (Azure Content Understanding)   │
                                          │   - Canadian mortgage field schema│
                                          │   - Income extraction             │
                                          │   - Property field extraction     │
                                          │   - Provenance tracking           │
                                          └──────────────────────────────────┘
                                                         │
                                                         ▼
                                          ┌──────────────────────────────────┐
                                          │       Result Aggregator          │
                                          │  - Merge borrower data           │
                                          │  - Combine income sources        │
                                          │  - Validate cross-doc consistency│
                                          │  - Track field provenance        │
                                          └──────────────────────────────────┘
                                                         │
                                                         ▼
                                          ┌──────────────────────────────────┐
                                          │    Calculation Engine            │
                                          │  - Compute monthly income        │
                                          │  - Compute housing costs         │
                                          │  - Apply MQR stress test         │
                                          │  - Calculate GDS/TDS/LTV         │
                                          └──────────────────────────────────┘
                                                         │
                                                         ▼
                                          ┌──────────────────────────────────┐
                                          │    Mortgage Policy Engine        │
                                          │  - Evaluate OSFI rules           │
                                          │  - Apply lender policies         │
                                          │  - Generate policy findings      │
                                          │  - Recommend decision            │
                                          └──────────────────────────────────┘
                                                         │
                                                         ▼
                                          ┌──────────────────────────────────┐
                                          │    Risk Analysis Service         │
                                          │  - Income consistency check      │
                                          │  - Fraud signal detection        │
                                          │  - AML flag assessment           │
                                          │  - Generate risk tier            │
                                          └──────────────────────────────────┘
```

---

## Data Model

### Canonical Mortgage Case Schema

The data model follows the comprehensive schema defined in `mortgage-research/canada_mortgage_case.schema.json`. Key entities:

#### Case Header
| Field | Type | Description |
|-------|------|-------------|
| `caseId` | string | Unique case identifier |
| `status` | enum | intake, in_review, pending_info, approved, declined, referred, cancelled, funded |
| `channel` | enum | branch, mobile, online, broker, call_centre, other |
| `province` | string | Canadian province code (ON, BC, QC, etc.) |
| `lenderId` | string | Lender identifier |

#### Application
| Field | Type | Description |
|-------|------|-------------|
| `purpose` | enum | purchase, refinance, switch, port, construction, other |
| `requestedAmount` | number | Requested mortgage amount |
| `requestedAmortizationMonths` | integer | Requested amortization period |
| `requestedTermMonths` | integer | Requested term |
| `rateType` | enum | fixed, variable, other |
| `occupancy` | enum | owner_occupied, rental, secondary_home, other |
| `productType` | enum | conventional, insured, insurable, heloc, blend_extend, other |

#### Borrower (per borrower)
| Field | Type | Description |
|-------|------|-------------|
| `borrowerId` | string | Borrower identifier |
| `role` | enum | primary, co_borrower, guarantor |
| `identity.fullName` | string | Legal name |
| `identity.dateOfBirth` | date | Date of birth |
| `residency.status` | enum | canadian_citizen, permanent_resident, work_permit, etc. |
| `employment[]` | array | Employment history with employer, position, dates |
| `income[]` | array | Income sources with type, amount, frequency |
| `assets[]` | array | Assets with type, value, source of funds |
| `liabilities[]` | array | Debts with type, balance, monthly payment |
| `creditProfile` | object | Bureau score, delinquencies, utilization |

#### Property
| Field | Type | Description |
|-------|------|-------------|
| `address` | object | Property address (line1, city, region, postalCode) |
| `propertyType` | enum | detached, semi, townhouse, condo, multi_unit, etc. |
| `occupancy` | enum | owner_occupied, rental, secondary_home, other |
| `purchasePrice` | number | Purchase price |
| `estimatedValue` | number | Estimated current value |
| `valuation` | object | Valuation method, value, effective date |
| `taxes.annual` | number | Annual property taxes |
| `condoFeesMonthly` | number | Monthly condo fees (if applicable) |
| `heatingMonthlyEstimate` | number | Estimated monthly heating cost |

#### Loan
| Field | Type | Description |
|-------|------|-------------|
| `amount` | number | Loan amount |
| `amortizationMonths` | integer | Amortization period |
| `termMonths` | integer | Mortgage term |
| `rateType` | enum | fixed, variable, other |
| `contractRatePct` | number | Contract interest rate (%) |
| `paymentFrequency` | enum | monthly, biweekly, accelerated_biweekly, weekly |
| `downPayment` | object | Amount and sources (savings, gift, RRSP, etc.) |

#### Calculations
| Field | Type | Description |
|-------|------|-------------|
| `ltv` | number | Loan-to-value ratio (0.80 = 80%) |
| `combinedLtv` | number | Combined LTV including secondary financing |
| `gds` | number | Gross Debt Service ratio at contract rate |
| `tds` | number | Total Debt Service ratio at contract rate |
| `stressTest.qualifyingRatePct` | number | Qualifying rate used for stress test |
| `stressTest.gds` | number | GDS at qualifying rate |
| `stressTest.tds` | number | TDS at qualifying rate |
| `stressTest.method` | enum | osfi_mqr_uninsured, insurer_guideline, lender_policy |

#### Policy Findings
| Field | Type | Description |
|-------|------|-------------|
| `ruleId` | string | Rule identifier (e.g., CA.OSFI.MQR.UNINSURED) |
| `status` | enum | pass, fail, exception_required, not_applicable, needs_review |
| `severity` | enum | low, medium, high, critical |
| `summary` | string | Human-readable finding summary |
| `rationale` | string | Why this determination was made |
| `evidence[]` | array | Document references (documentId, page, fieldPath) |

#### Risk
| Field | Type | Description |
|-------|------|-------------|
| `riskTier` | enum | low, medium, high, very_high, unknown |
| `signals[]` | array | Risk signals with severity and description |
| `fraudFlags[]` | array | Fraud indicator flags |
| `amlFlags[]` | array | AML/ATF flags |

#### Decision
| Field | Type | Description |
|-------|------|-------------|
| `recommendedOutcome` | enum | approve, decline, refer, pending_info |
| `confidence` | number | Model confidence (0-1) |
| `conditions[]` | array | Conditions required to fund |
| `underwritingNote` | string | AI-generated underwriting narrative |
| `finalOutcome` | enum | Final decision after human review |
| `finalizedBy` | string | User who finalized |
| `finalizedAt` | datetime | Finalization timestamp |

---

## Mortgage Underwriting Policies

The policy rules are stored in `prompts/mortgage-underwriting-policies.json` and follow the YAML structure defined in `mortgage-research/canada_underwriting_rules_catalog.yaml`.

### Policy Categories

| Category | Description |
|----------|-------------|
| `osfi_regulatory` | OSFI B-20 and related regulatory requirements |
| `credit_evaluation` | Credit score, delinquency, and bureau rules |
| `income_qualification` | Income verification and calculation rules |
| `collateral_valuation` | Property and LTV requirements |
| `down_payment` | Source of funds and down payment rules |
| `aml_fraud` | AML/ATF and fraud detection rules |
| `documentation` | Required documentation and completeness |

### Key OSFI B-20 Rules

```json
{
  "version": "1.0",
  "jurisdiction": "CA",
  "effective_date": "2026-01-01",
  "description": "Canadian Mortgage Underwriting Policies - OSFI B-20 Aligned",
  "policies": [
    {
      "id": "CA.OSFI.MQR.UNINSURED",
      "category": "osfi_regulatory",
      "subcategory": "stress_test",
      "name": "Uninsured Mortgage Qualifying Rate (MQR)",
      "description": "OSFI requires uninsured mortgages to be qualified at the greater of contract rate + 2% or 5.25% floor",
      "criteria": [
        {
          "id": "CA.OSFI.MQR.UNINSURED-A",
          "condition": "product_type IN ('conventional', 'insurable') AND NOT insured",
          "action": "Apply qualifying rate = max(contract_rate + 2%, 5.25%)",
          "severity": "critical",
          "rationale": "OSFI mandates stress testing to ensure borrowers can handle rate increases"
        }
      ],
      "source": "https://www.osfi-bsif.gc.ca/en/supervision/financial-institutions/banks/minimum-qualifying-rate-uninsured-mortgages"
    },
    {
      "id": "CA.UW.DSR.GDS_LIMIT",
      "category": "income_qualification",
      "subcategory": "debt_service",
      "name": "GDS Limit at Stress Test Rate",
      "description": "GDS at qualifying rate should not exceed lender limit (typically 39%)",
      "criteria": [
        {
          "id": "CA.UW.DSR.GDS_LIMIT-A",
          "condition": "stress_test_gds <= 0.39",
          "status": "pass",
          "rationale": "GDS within acceptable limits"
        },
        {
          "id": "CA.UW.DSR.GDS_LIMIT-B",
          "condition": "stress_test_gds > 0.39 AND stress_test_gds <= 0.42",
          "status": "needs_review",
          "action": "Document compensating factors",
          "rationale": "GDS slightly elevated, may be approvable with strong file"
        },
        {
          "id": "CA.UW.DSR.GDS_LIMIT-C",
          "condition": "stress_test_gds > 0.42",
          "status": "exception_required",
          "action": "Senior underwriter approval required",
          "rationale": "GDS exceeds policy maximum, exception process required"
        }
      ]
    },
    {
      "id": "CA.UW.DSR.TDS_LIMIT",
      "category": "income_qualification",
      "subcategory": "debt_service",
      "name": "TDS Limit at Stress Test Rate",
      "description": "TDS at qualifying rate should not exceed lender limit (typically 44%)",
      "criteria": [
        {
          "id": "CA.UW.DSR.TDS_LIMIT-A",
          "condition": "stress_test_tds <= 0.44",
          "status": "pass",
          "rationale": "TDS within acceptable limits"
        },
        {
          "id": "CA.UW.DSR.TDS_LIMIT-B",
          "condition": "stress_test_tds > 0.44 AND stress_test_tds <= 0.47",
          "status": "needs_review",
          "action": "Document compensating factors",
          "rationale": "TDS slightly elevated, may be approvable with strong file"
        },
        {
          "id": "CA.UW.DSR.TDS_LIMIT-C",
          "condition": "stress_test_tds > 0.47",
          "status": "exception_required",
          "action": "Senior underwriter approval required",
          "rationale": "TDS exceeds policy maximum, exception process required"
        }
      ]
    },
    {
      "id": "CA.UW.COLLATERAL.LTV_CONVENTIONAL",
      "category": "collateral_valuation",
      "subcategory": "ltv_limits",
      "name": "Conventional Mortgage LTV Limits",
      "description": "Conventional (uninsured) mortgages must have LTV <= 80%",
      "criteria": [
        {
          "id": "CA.UW.COLLATERAL.LTV_CONVENTIONAL-A",
          "condition": "product_type = 'conventional' AND ltv <= 0.80",
          "status": "pass",
          "rationale": "LTV within conventional mortgage limits"
        },
        {
          "id": "CA.UW.COLLATERAL.LTV_CONVENTIONAL-B",
          "condition": "product_type = 'conventional' AND ltv > 0.80",
          "status": "fail",
          "action": "Mortgage insurance required or reduce loan amount",
          "rationale": "Conventional mortgages cannot exceed 80% LTV in Canada"
        }
      ]
    },
    {
      "id": "CA.UW.DP.SOURCE_OF_FUNDS",
      "category": "down_payment",
      "subcategory": "verification",
      "name": "Down Payment Source Verification",
      "description": "All down payment sources must be verified with supporting documentation",
      "criteria": [
        {
          "id": "CA.UW.DP.SOURCE_OF_FUNDS-A",
          "condition": "all down_payment_sources have verified = true",
          "status": "pass",
          "rationale": "All down payment sources verified"
        },
        {
          "id": "CA.UW.DP.SOURCE_OF_FUNDS-B",
          "condition": "any down_payment_source has verified = false",
          "status": "needs_review",
          "action": "Request bank statements, transfer proof, or gift letter as applicable",
          "rationale": "Unverified funds cannot be counted toward down payment"
        }
      ]
    },
    {
      "id": "CA.UW.INCOME.CONSISTENCY",
      "category": "income_qualification",
      "subcategory": "verification",
      "name": "Income Consistency Across Documents",
      "description": "Income stated on application should match supporting documents within tolerance",
      "criteria": [
        {
          "id": "CA.UW.INCOME.CONSISTENCY-A",
          "condition": "income variance across documents <= 5%",
          "status": "pass",
          "rationale": "Income consistent across all sources"
        },
        {
          "id": "CA.UW.INCOME.CONSISTENCY-B",
          "condition": "income variance across documents > 5%",
          "status": "needs_review",
          "action": "Investigate discrepancy and document rationale",
          "rationale": "Income discrepancies must be resolved and explained"
        }
      ]
    },
    {
      "id": "CA.UW.AML.RED_FLAGS",
      "category": "aml_fraud",
      "subcategory": "aml_triage",
      "name": "AML Red Flag Detection",
      "description": "Flag potential AML indicators for compliance review",
      "criteria": [
        {
          "id": "CA.UW.AML.RED_FLAGS-A",
          "condition": "no AML flags detected",
          "status": "pass",
          "rationale": "No AML indicators identified"
        },
        {
          "id": "CA.UW.AML.RED_FLAGS-B",
          "condition": "AML flags detected",
          "status": "refer",
          "action": "Escalate to AML/ATF compliance team",
          "rationale": "Potential AML indicators require specialized review"
        }
      ]
    },
    {
      "id": "CA.UW.CREDIT.MINIMUM_SCORE",
      "category": "credit_evaluation",
      "subcategory": "bureau_score",
      "name": "Minimum Credit Score Requirement",
      "description": "Borrowers must meet minimum credit score threshold",
      "criteria": [
        {
          "id": "CA.UW.CREDIT.MINIMUM_SCORE-A",
          "condition": "credit_score >= 680",
          "status": "pass",
          "rationale": "Credit score meets minimum requirement"
        },
        {
          "id": "CA.UW.CREDIT.MINIMUM_SCORE-B",
          "condition": "credit_score >= 620 AND credit_score < 680",
          "status": "needs_review",
          "action": "Document compensating factors (LTV, income stability, assets)",
          "rationale": "Credit score below preferred threshold"
        },
        {
          "id": "CA.UW.CREDIT.MINIMUM_SCORE-C",
          "condition": "credit_score < 620",
          "status": "exception_required",
          "action": "Senior approval required with strong compensating factors",
          "rationale": "Credit score significantly below threshold"
        }
      ]
    }
  ]
}
```

---

## Requirements

### Functional Requirements

#### Document Processing (P0)
- **FR-001**: System MUST detect mortgage document type on upload (application, T4, pay stub, appraisal, etc.).
- **FR-002**: System MUST route documents to `mortgageDocAnalyzer` for extraction.
- **FR-003**: System MUST extract Canadian mortgage-specific fields per the schema.
- **FR-004**: System MUST track provenance (document, page, bounding region) for each extracted field.
- **FR-005**: System MUST aggregate fields across multiple documents into unified case view.
- **FR-006**: System MUST flag cross-document inconsistencies for underwriter review.

#### Calculation Engine (P0)
- **FR-007**: System MUST compute monthly income from various sources with appropriate annualization.
- **FR-008**: System MUST compute housing costs (P&I, taxes, heating, condo fees).
- **FR-009**: System MUST compute mortgage payment at contract rate.
- **FR-010**: System MUST apply OSFI MQR for uninsured mortgages (max of contract+2%, 5.25%).
- **FR-011**: System MUST compute GDS and TDS at both contract rate and qualifying rate.
- **FR-012**: System MUST compute LTV and combined LTV.
- **FR-013**: System MUST track calculation inputs with provenance to source fields.

#### Policy Engine (P1)
- **FR-014**: System MUST load mortgage underwriting policies from JSON file.
- **FR-015**: System MUST evaluate each applicable rule and record pass/fail/needs_review/exception_required.
- **FR-016**: System MUST link each policy finding to supporting evidence with document references.
- **FR-017**: System MUST support OSFI B-20 regulatory rules.
- **FR-018**: System MUST support configurable lender-specific rules.
- **FR-019**: System MUST generate recommended decision based on policy evaluation.
- **FR-020**: System MUST support exception workflow with compensating factor documentation.

#### RAG Integration (P1)
- **FR-021**: System MUST chunk and embed mortgage underwriting policies using unified indexer.
- **FR-022**: System MUST support semantic search over mortgage policies in Ask IQ.
- **FR-023**: System MUST retrieve relevant policy chunks for underwriting questions.
- **FR-024**: System MUST combine case context with policy knowledge in chat responses.

#### Risk Analysis (P1)
- **FR-025**: System MUST detect income inconsistencies across documents.
- **FR-026**: System MUST flag potential document alterations.
- **FR-027**: System MUST identify large unexplained deposits.
- **FR-028**: System MUST generate risk tier assessment.
- **FR-029**: System MUST escalate AML flags to compliance workflow.

#### UX (P1)
- **FR-030**: Frontend MUST display 3-column underwriter workbench layout.
- **FR-031**: Frontend MUST show provenance chips linking fields to source documents.
- **FR-032**: Frontend MUST display GDS/TDS calculations with input breakdown.
- **FR-033**: Frontend MUST show policy rule status with expand/collapse details.
- **FR-034**: Frontend MUST support decision workflow (Approve, Refer, Decline, Pending Info).
- **FR-035**: Frontend MUST lock audit snapshot on decision submission.

### Non-Functional Requirements

- **NFR-001**: Document extraction MUST complete within 30 seconds per document.
- **NFR-002**: Calculation engine MUST compute all ratios within 1 second.
- **NFR-003**: Policy engine MUST evaluate all rules within 5 seconds.
- **NFR-004**: Audit snapshots MUST be immutable once created.
- **NFR-005**: All extracted fields MUST include source attribution.

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MORTGAGE_UNDERWRITING_ENABLED` | No | `true` | Enable mortgage underwriting persona |
| `MORTGAGE_DOC_ANALYZER` | No | `mortgageDocAnalyzer` | Custom document analyzer ID |
| `MORTGAGE_POLICIES_PATH` | No | `prompts/mortgage-underwriting-policies.json` | Path to policies |
| `OSFI_MQR_FLOOR_PCT` | No | `5.25` | OSFI MQR floor rate |
| `OSFI_MQR_BUFFER_PCT` | No | `2.0` | OSFI MQR buffer over contract rate |
| `GDS_LIMIT_STANDARD` | No | `0.39` | Standard GDS limit |
| `TDS_LIMIT_STANDARD` | No | `0.44` | Standard TDS limit |

### Unified Indexer Configuration

Add to `PERSONA_CONFIG` in `app/rag/unified_indexer.py`:

```python
"mortgage_underwriting": {
    "policies_path": "prompts/mortgage-underwriting-policies.json",
    "table_name": "mortgage_policy_chunks",
    "display_name": "Mortgage Underwriting",
},
```

---

## Integration with Existing Infrastructure

### Unified RAG Service

The mortgage persona integrates with the existing `RAGService` class:

```python
# Initialize RAG service for mortgage persona
rag_service = RAGService(
    settings=settings,
    max_context_tokens=4000,
    use_hybrid_search=True,
    persona="mortgage_underwriting",
)
await rag_service.initialize()

# Query mortgage policies
result = await rag_service.query(
    user_query="What is the stress test rate for uninsured mortgages?",
    use_llm_inference=False,
    top_k=5,
)
```

### Unified Prompts Engine

The mortgage persona uses the existing prompts system with persona-specific prompts:

```python
from app.prompts import load_prompts
from app.personas import PersonaType

prompts = load_prompts(
    storage_root="data/",
    persona=PersonaType.MORTGAGE_UNDERWRITING,
)
```

### Ask IQ Integration

The mortgage persona hooks into Ask IQ chat with persona-aware context:

```python
# In chat endpoint
context = await rag_service.query(user_message)
response = await openai_client.chat_completion(
    messages=[
        {"role": "system", "content": prompts["chat_system_prompt"]},
        {"role": "user", "content": f"Context:\n{context.context}\n\nQuestion: {user_message}"}
    ]
)
```

### Reuse from Automotive Claims

| Component | Automotive Claims | Mortgage Underwriting Reuse |
|-----------|-------------------|-----------------------------|
| MIME Detection | `app/multimodal/mime_detector.py` | Reuse for document type detection |
| Result Aggregator | `app/multimodal/aggregator.py` | Extend for mortgage field merging |
| Policy Loader | `app/claims/policies.py` | Adapt `ClaimsPolicyLoader` → `MortgagePolicyLoader` |
| Policy Engine | `app/claims/engine.py` | Adapt `ClaimsPolicyEngine` → `MortgagePolicyEngine` |
| Policy Chunker | `app/claims/chunker.py` | Reuse `ClaimsPolicyChunker` pattern |
| Policy Indexer | `app/claims/indexer.py` | Reuse via unified indexer |
| RAG Service | `app/rag/service.py` | Reuse with `persona="mortgage_underwriting"` |
| Unified Indexer | `app/rag/unified_indexer.py` | Add mortgage persona to `PERSONA_CONFIG` |

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: 95%+ of mortgage documents correctly classified by type.
- **SC-002**: GDS/TDS calculations match manual calculation within 0.1%.
- **SC-003**: Policy rule evaluation provides finding for 95%+ of applicable rules.
- **SC-004**: Stress test qualifying rate correctly applied per OSFI guidelines.
- **SC-005**: Income inconsistencies flagged when variance exceeds 5%.
- **SC-006**: Underwriter decision time reduced by 30% compared to manual review.

---

## Assumptions

1. All mortgage documents are in PDF format (no handwritten applications).
2. Credit bureau data is provided in structured format or standard report layout.
3. Lender has approved the policy rules configuration.
4. OSFI MQR floor rate (5.25%) is current and will be updated via configuration if it changes.
5. Underwriters have training on the new workbench interface.

---

## Open Questions

1. **Q**: Should we support provincial-specific rules (e.g., Quebec Civil Code)?
   - **Proposed**: Start with federal OSFI rules, add provincial modules in Phase 2.

2. **Q**: How should we handle variable income (self-employed, commission)?
   - **Proposed**: Follow CRA 2-year average with configurable haircuts per income type.

3. **Q**: Should property photos use image analysis for condition assessment?
   - **Proposed**: Defer to Phase 2, focus on document processing for MVP.

4. **Q**: How should exception approvals be routed?
   - **Proposed**: Role-based routing per `approvalThreshold` in policy rules.

---

## Future Enhancements (Out of Scope)

1. **Provincial rule modules** - Quebec, BC, Alberta-specific requirements
2. **Property photo analysis** - Condition assessment from property images
3. **Broker portal integration** - Direct submission from broker systems
4. **Insurer API integration** - Automated MI submission for high-ratio mortgages
5. **Real-time income verification** - Integration with payroll providers
6. **Fraud score model** - ML-based fraud risk scoring

---

## Document Types and Extraction Focus

### Required Documents Checklist

| Document Type | Key Fields to Extract | Confidence Priority |
|---------------|----------------------|---------------------|
| `application_summary` | Borrower info, loan request, property address, occupancy | High |
| `employment_letter` | Employer name, position, start date, salary, employment type | High |
| `pay_stub` | Gross pay, pay period, YTD earnings, employer name | High |
| `t4` | Employment income, employer name, SIN, tax year | High |
| `notice_of_assessment` | Total income, tax owing/refund, tax year | High |
| `bank_statement` | Account balance, transactions, large deposits | Medium |
| `gift_letter` | Donor name, gift amount, relationship, signed date | High |
| `purchase_sale_agreement` | Property address, purchase price, closing date, conditions | High |
| `appraisal_report` | Property value, property type, as-of date, appraiser | High |
| `credit_report` | Credit score, trade lines, delinquencies, inquiries | High |

---

## References

- [OSFI Guideline B-20](https://www.osfi-bsif.gc.ca/en/guidance/guidance-library/residential-mortgage-underwriting-practices-procedures-guideline-b-20)
- [OSFI Minimum Qualifying Rate](https://www.osfi-bsif.gc.ca/en/supervision/financial-institutions/banks/minimum-qualifying-rate-uninsured-mortgages)
- [mortgage-research/canadian_underwriting_decisioning_manual.md](../../../mortgage-research/canadian_underwriting_decisioning_manual.md)
- [mortgage-research/canada_underwriting_rules_catalog.yaml](../../../mortgage-research/canada_underwriting_rules_catalog.yaml)
- [mortgage-research/canada_mortgage_case.schema.json](../../../mortgage-research/canada_mortgage_case.schema.json)
- [mortgage-research/underwriter_workbench_ux_spec.md](../../../mortgage-research/underwriter_workbench_ux_spec.md)
