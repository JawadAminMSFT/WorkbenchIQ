# Feature Specification: Commercial Brokerage Workbench

**Feature Branch**: `feature-commercial-brokerage`
**Created**: 2026-03-25
**Status**: Draft
**Input**: Broker Dashboard meeting (March 25 2026) with Naveen Dhar (FSI Industry Architect), Jawad Amin, Mona Chitalia. Reference: Broker Workbench Shared Folder (quote-comparison-tool-v2.pptx, ACORD sample documents, sample carrier quotes).

---

## Overview

This specification defines a new **Commercial Brokerage** persona for WorkbenchIQ. It targets retail commercial insurance brokers who today work entirely through disconnected emails, spreadsheets, and carrier portals — with no integrated AI-assisted view.

A commercial broker's core job has three stages:
1. **Client Research & Prospecting** — Understand the client's business, financials, and insurance gaps before the sales conversation.
2. **Submission Management** — Fill ACORD forms from client data, assemble a submission package, and distribute to multiple carriers.
3. **Quote Comparison & Placement** — Collect quotes back in varied formats (PDF, Excel, email), normalize them, compare side-by-side, and recommend the optimal carrier combination.

The MVP focuses on **commercial property insurance** (ACORD 125 + ACORD 140), with the data model and UI built to be **extensible** to additional lines (D&O, Workers Comp, Benefits, General Liability) without rearchitecting.

This persona sits alongside — but is distinct from — a future **Commercial Underwriting** persona (Amol's demo). Brokerage = the broker's side; Underwriting = the carrier/insurer's side.

### Goals

1. **Broker Dashboard** — Unified view of all accounts, premiums, upcoming renewals, and open submissions.
2. **AI-Powered Client Research** — Grounded research using Bing (SEC filings, IR, news) and optional AM Best / S&P data.
3. **ACORD Application Generation** — AI-assisted form fill from uploaded client documents and conversation context.
4. **Quote Extraction & Normalization** — Parse quotes received in any format (PDF, Excel) into a common schema.
5. **Quote Comparison & Placement Engine** — Side-by-side comparison table with AI-recommended placement rationale.
6. **Client & Policy Portfolio** — Per-account view of all policies, contacts, claims history, and documents.
7. **Ask IQ** — Context-aware chat grounded in submission data, quotes, and uploaded documents.

---

## User Stories

### US-1: Broker Dashboard (Priority: P0)
> As a commercial broker, I want a single dashboard that shows all my accounts, active submissions, upcoming renewals, and key metrics, so that I can prioritise my day without switching between tools.

**Why this priority**: The entry point of the persona — without it the broker has no orientation.

**Acceptance Scenarios**:
1. **Given** a broker logs in, **When** the dashboard loads, **Then** they see: total accounts count, total bound premium, number of open submissions, and number of renewals due in the next 90 days.
2. **Given** an account is within 90 days of renewal, **When** viewing the dashboard, **Then** it appears in a "Renewals" section with the renewal date highlighted.
3. **Given** an open submission has had no activity for 7 days, **When** viewing the dashboard, **Then** it is flagged with a stale indicator.
4. **Given** the broker clicks any account card, **When** the account opens, **Then** they see the full client profile (US-6).

---

### US-2: Client Research & Market Intelligence (Priority: P0)
> As a commercial broker, I want to enter a prospect's company name and receive an AI-generated research brief, so that I can walk into the client conversation informed.

**Why this priority**: Research is the first step in every commercial engagement. Brokers today do this manually across multiple tools.

**Acceptance Scenarios**:
1. **Given** a broker enters a company name, **When** research runs, **Then** the system returns: company overview, financials summary, industry risk profile, estimated insurance needs by line, and likely carrier appetite matches.
2. **Given** a public company is searched, **When** results return, **Then** the system includes grounded citations from SEC filings, annual reports, and news via Bing.
3. **Given** AM Best / S&P data is available (via LSEG integration or uploaded carrier profile documents), **When** research runs, **Then** the brief includes — for each recommended carrier — their Financial Strength Rating (FSR), Issuer Credit Rating (ICR), rating outlook, balance sheet strength tier, operating performance tier, combined ratio, and NWP-to-surplus ratio.
4. **Given** the research completes, **When** viewing the brief, **Then** the broker can edit and annotate it before the client call.
5. **Given** a private company is searched with limited public data, **When** results return, **Then** the system clearly indicates which fields have low-confidence sourcing.

---

### US-3: Submission Package Generation (Priority: P0)
> As a commercial broker, I want to upload client documents and have the system auto-populate an ACORD application form, so that I spend minutes — not hours — preparing a submission.

**Why this priority**: Submission preparation is the most time-consuming manual task for brokers.

**Note**: Files are uploaded via the admin view pattern used across all WorkbenchIQ personas. The broker uploads documents (prior declarations, SOV, loss runs) and the system generates a pre-filled ACORD application.

**Acceptance Scenarios**:
1. **Given** a broker uploads a Statement of Values (SOV) PDF and loss runs, **When** extraction runs, **Then** property details and claims history fields are pre-populated in the ACORD 140 form.
2. **Given** a broker uploads a prior policy declaration, **When** extraction runs, **Then** coverage history, limits, and deductibles are pre-populated in ACORD 125.
3. **Given** auto-populated fields are shown, **When** the broker reviews them, **Then** each field shows its source document and a confidence score.
4. **Given** the ACORD form is complete, **When** the broker clicks "Generate Submission Package", **Then** the system produces: a submission cover email, ACORD 125, ACORD 140, SOV, and loss runs bundled as a submission package.
5. **Given** a submission package is generated, **When** the broker selects carriers and clicks "Send", **Then** individual submission emails are dispatched to each selected carrier.

---

### US-4: Quote Collection & Extraction (Priority: P0)
> As a commercial broker, I want to upload quotes received from carriers in any format and have the system extract the key terms into a structured view, so that I can compare them without manually re-keying data.

**Why this priority**: Carriers respond in wildly different formats. Normalisation is the prerequisite for comparison.

**Acceptance Scenarios**:
1. **Given** a broker uploads a PDF quote from AIG, **When** extraction runs, **Then** premium, limits, deductible, exclusions, and effective date are extracted and displayed with confidence scores.
2. **Given** a broker uploads an Excel quote from Zurich, **When** extraction runs, **Then** the system parses all relevant tabs and maps fields to the canonical quote schema.
3. **Given** multiple quotes are uploaded for the same submission, **When** all extractions complete, **Then** all quotes appear in the Quote Comparison view (US-5).
4. **Given** a field could not be extracted with confidence ≥ 60%, **When** displayed, **Then** the field is flagged "Needs Review" and highlighted in amber.
5. **Given** a quote is missing a required comparison field (e.g., aggregate limit), **When** displayed, **Then** the system prompts the broker to request clarification from the carrier.

---

### US-5: Quote Comparison & Placement Recommendation (Priority: P0)
> As a commercial broker, I want a side-by-side comparison of all carrier quotes with an AI-recommended placement, so that I can quickly identify the best option for my client.

**Why this priority**: Quote comparison is the broker's core analytical task. This is the primary differentiator of the persona.

**Acceptance Scenarios**:
1. **Given** two or more quotes are extracted for a submission, **When** the broker opens Quote Comparison, **Then** they see a normalized table with columns per carrier and rows for: Annual Premium, Total Insured Value, Building Limit, Contents Limit, Business Interruption, Deductible, Flood Sublimit, Earthquake Sublimit, Named Perils Exclusions, AM Best Rating, Terms.
2. **Given** the comparison table is displayed, **When** the AI recommendation runs, **Then** the system highlights the recommended carrier with a plain-language rationale citing the top 3 reasons (e.g., "Best premium-to-limit ratio; broadest flood coverage; A+ rated carrier").
3. **Given** a multi-line submission (property + D&O), **When** comparing quotes, **Then** the system can model a carrier combination (e.g., AIG for property, Zurich for D&O) and show the blended total premium.
4. **Given** the broker selects a placement, **When** they click "Generate Client Presentation", **Then** the system produces a client-ready comparison summary (exportable as PDF or PPTX).
5. **Given** the broker adjusts weights (e.g., "price is most important"), **When** the ranking updates, **Then** the recommended carrier re-sorts accordingly.

---

### US-6: Client & Policy Portfolio View (Priority: P1)
> As a commercial broker, I want a complete profile for each client showing their policies, contacts, claims history, and documents in one place, so that I always have full context when interacting with them.

**Why this priority**: Brokers need institutional memory per account; today this lives in siloed CRM and email.

**Acceptance Scenarios**:
1. **Given** a broker opens an account, **When** the client profile loads, **Then** they see: company details, policy portfolio (in-force, expired, pending), claims summary, client contacts, carrier/underwriter contacts, and a document library.
2. **Given** a policy is within 90 days of expiry, **When** viewing the portfolio, **Then** it is flagged with a renewal alert and a "Start Renewal Submission" quick action.
3. **Given** a broker asks "What claims has this client had in the last 3 years?" in Ask IQ, **When** the response returns, **Then** it cites data from the claims summary in the client profile.
4. **Given** new documents are uploaded, **When** they are processed, **Then** they are automatically categorised into: Applications, Endorsements, Schedules, Loss Runs, or Quotes.
5. **Given** the document library has 20+ files, **When** a broker searches "flood exclusion", **Then** the relevant clause in the most recent policy declaration is surfaced.

---

### US-7: Ask IQ — Brokerage Chat (Priority: P1)
> As a commercial broker, I want to ask questions about a submission, a quote, or a client's history in plain language, so that I can get answers without navigating through multiple screens.

**Why this priority**: Ask IQ drives adoption by making the workbench feel conversational.

**Acceptance Scenarios**:
1. **Given** a broker asks "Which quote has the best flood coverage?", **When** the response returns, **Then** it compares the flood sublimits across all extracted quotes and cites the source document.
2. **Given** a broker asks "What is missing from the Ridgeview submission?", **When** the response returns, **Then** it lists any unfilled required ACORD fields and any documents not yet received.
3. **Given** a broker asks "Summarise what I know about Ridgeview Properties", **When** the response returns, **Then** it combines data from the client profile, research brief, and uploaded documents.
4. **Given** policy knowledge has been loaded, **When** a broker asks "Is Ridgeview's flood coverage sufficient for a coastal property?", **Then** the response cites specific policy sections and coverage guidelines.

---

### US-8: Admin — Carrier & Policy Configuration (Priority: P1)
> As an admin, I want to configure the list of carriers, ACORD form templates, and placement rules, so that the workbench stays current with the broker's book of business.

**Acceptance Scenarios**:
1. **Given** an admin uploads a new carrier quote template (PDF or Excel), **When** saved, **Then** the quote extractor uses it as a reference layout for that carrier.
2. **Given** an admin updates the carrier list, **When** a broker generates a submission package, **Then** the updated carrier list appears for selection.
3. **Given** an admin uploads underwriting guidelines JSON, **When** saved, **Then** the placement engine uses the updated rules for carrier appetite matching.
4. **Given** an admin uploads an AM Best Credit Report PDF for a carrier, **When** processed by `ambReportAnalyzer`, **Then** the carrier's profile is updated with FSR, ICR, outlook, balance sheet strength, operating performance, business profile, ERM, combined ratio, surplus, and report date.
5. **Given** an admin uploads an MD&A annual statement PDF for a carrier, **When** processed by `ambReportAnalyzer`, **Then** the carrier's profile is updated with DWP, combined ratio, total admitted assets, loss reserves, RBC adequacy, reinsurance retention, and geographic/LOB breakdown.
6. **Given** a carrier's profile is updated with new AM Best data, **When** the placement engine next scores quotes for that carrier, **Then** it uses the refreshed FSR, combined ratio, and NWP-to-surplus ratio in its scoring.

---

## Architecture

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (Next.js)                              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Commercial Brokerage Interface                                        │    │
│  │ - Broker Dashboard (accounts, renewals, open submissions)            │    │
│  │ - Client Research view (Bing grounded brief)                         │    │
│  │ - Submission Builder (ACORD form fill + package gen)                 │    │
│  │ - Quote Comparison view (side-by-side table + placement rec)         │    │
│  │ - Client Profile view (policies, contacts, claims, docs)             │    │
│  │ - Ask IQ Chat drawer                                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ REST API
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND (FastAPI)                               │
│                                                                              │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐    │
│  │ Submission         │  │ Quote Extractor    │  │ Placement Engine   │    │
│  │ Endpoint           │  │ - PDF parser       │  │ - Carrier match    │    │
│  │ /api/.../upload    │  │ - Excel parser     │  │ - Rule evaluation  │    │
│  │                    │  │ - Field normaliser │  │ - Combo analysis   │    │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘    │
│                                    │                                         │
│  ┌────────────────────┐  ┌─────────┴──────────┐  ┌────────────────────┐    │
│  │ Research Module    │  │ Azure Content       │  │ ACORD Form         │    │
│  │ - Bing grounding   │  │ Understanding       │  │ Generator          │    │
│  │ - AM Best / S&P    │  │                     │  │ - Field extraction │    │
│  │   (optional LSEG)  │  │ brokerDocAnalyzer   │  │ - Form population  │    │
│  │                    │  │ brokerQuoteAnalyzer │  └────────────────────┘    │
│  │ Carrier Profile    │  │ ambReportAnalyzer   │                            │
│  │ Engine             │  │ (AM Best Credit +   │                            │
│  │ - FSR scoring      │  │  MD&A filings)      │                            │
│  └────────────────────┘  └─────────────────────┘                           │
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
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  ┌──────────┐  │   │
│  │  │ clients      │  │ submissions  │  │ quotes      │  │ placements│  │   │
│  │  │ - id (PK)    │  │ - id (PK)    │  │ - id (PK)   │  │ - id (PK)│  │   │
│  │  │ - name       │  │ - client_id  │  │ - sub_id    │  │ - sub_id │  │   │
│  │  │ - profile_json│  │ - lob        │  │ - carrier   │  │ - quotes │  │   │
│  │  │ - contacts   │  │ - status     │  │ - data_json │  │ - rationale│  │   │
│  │  └──────────────┘  └──────────────┘  └─────────────┘  └──────────┘  │   │
│  │                                                                       │   │
│  │  ┌──────────────────────────────┐  ┌──────────────────────────────┐  │   │
│  │  │ carrier_profiles             │  │ broker_policy_chunks (RAG)   │  │   │
│  │  │ - id (PK)                    │  │ - id (PK), policy_id         │  │   │
│  │  │ - carrier_name, naic_code    │  │ - chunk_text                 │  │   │
│  │  │ - fsr, icr, outlook          │  │ - embedding VECTOR           │  │   │
│  │  │ - amb_report_json (Credit)   │  │ - category                   │  │   │
│  │  │ - mda_report_json (MD&A)     │  └──────────────────────────────┘  │   │
│  │  │ - report_date, mda_year      │                                     │   │
│  │  └──────────────────────────────┘                                     │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Azure Blob Storage                                       │
│  - Uploaded source documents (SOV, loss runs, property photos, prior decls) │
│  - Generated ACORD forms and submission packages                             │
│  - Received carrier quotes (PDF, Excel)                                      │
│  - Client research briefs                                                    │
│  - AM Best Credit Report PDFs and MD&A annual statement PDFs (per carrier)  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Submission & Quote Processing Flow

```
┌──────────────┐    ┌──────────────┐    ┌─────────────────────────────────────┐
│  Upload      │    │  MIME Type   │    │         Analyzer Router              │
│  Client Docs │───▶│  Detection   │───▶│                                      │
│  & Quotes    │    └──────────────┘    │  ┌──────────┐  ┌──────────────────┐ │
└──────────────┘                        │  │ PDF/DOCX │  │ XLSX/CSV         │ │
                                        │  └────┬─────┘  └────┬─────────────┘ │
                                        │       │              │               │
                                        │  ┌────▼─────┐  ┌────▼─────────────┐ │
                                        │  │ broker   │  │ broker           │ │
                                        │  │ DocAnalyzer  │ QuoteAnalyzer   │ │
                                        │  └──────────┘  └─────────────────┘ │
                                        └─────────────────────────────────────┘
                                                        │
                                                        ▼
                                        ┌──────────────────────────────────────┐
                                        │         Field Normaliser             │
                                        │  - Map carrier-specific labels       │
                                        │    to canonical schema               │
                                        │  - Assign confidence scores          │
                                        └──────────────────────────────────────┘
                                                        │
                                                        ▼
                                        ┌──────────────────────────────────────┐
                                        │       Placement Engine               │
                                        │  - Carrier appetite match            │
                                        │  - Coverage adequacy check           │
                                        │  - Combination optimisation          │
                                        │  - Generate rationale                │
                                        └──────────────────────────────────────┘
```

---

## Data Model

### Client / Account

| Field | Type | Description |
|-------|------|-------------|
| `ClientID` | uuid | Unique identifier |
| `ClientName` | string | Business name |
| `IndustryCode` | string | NAICS or SIC code |
| `BusinessType` | string | LLC, Inc, partnership, etc. |
| `YearsInBusiness` | number | Years operating |
| `AnnualRevenue` | string | Estimated annual revenue |
| `EmployeeCount` | number | Number of employees |
| `HeadquartersAddress` | string | Primary business address |
| `PropertyLocations` | array | All insured property locations |
| `RenewalDate` | date | Next policy renewal date |
| `BrokerNotes` | string | Broker-added annotations |
| `ResearchBrief` | object | AI-generated client research output |

### Submission

| Field | Type | Description |
|-------|------|-------------|
| `SubmissionID` | uuid | Unique identifier |
| `ClientID` | uuid | Parent client |
| `LineOfBusiness` | string | property, d_and_o, workers_comp, general_liability, benefits |
| `ACORDFormType` | array | e.g., ["125", "140"] |
| `Status` | string | draft, submitted, quoted, bound, declined, lapsed |
| `EffectiveDate` | date | Requested coverage start date |
| `ExpirationDate` | date | Requested coverage end date |
| `TotalInsuredValue` | string | Total value being insured |
| `CoverageRequested` | object | Limits, deductibles, special conditions |
| `SubmittedCarriers` | array | List of carrier names submitted to |
| `Documents` | array | See Document schema |
| `SubmissionDate` | date | Date package sent to carriers |
| `CreatedDate` | date | Date submission created |

### Document

| Field | Type | Description |
|-------|------|-------------|
| `DocumentID` | uuid | Unique identifier |
| `SubmissionID` | uuid | Parent submission |
| `DocumentType` | string | acord_125, acord_140, sov, loss_runs, property_photos, prior_declaration, submission_email, other |
| `FileName` | string | Original filename |
| `BlobUrl` | string | Azure Blob Storage URL |
| `ExtractedFields` | object | JSON of fields extracted by Azure CU |
| `ConfidenceScores` | object | Per-field confidence (0.0–1.0) |
| `UploadedAt` | datetime | Upload timestamp |

### Quote

| Field | Type | Description |
|-------|------|-------------|
| `QuoteID` | uuid | Unique identifier |
| `SubmissionID` | uuid | Parent submission |
| `CarrierName` | string | Insurer name (e.g., AIG, Zurich) |
| `SourceFormat` | string | pdf, xlsx, email, portal |
| `SourceFileName` | string | Original file |
| `ReceivedDate` | date | Date quote was received |
| `Status` | string | raw, extracted, reviewed, selected, declined |

#### Quote Extracted Fields (Canonical Schema)

| Field | Type | Description |
|-------|------|-------------|
| `AnnualPremium` | string | Total annual premium |
| `TotalInsuredValue` | string | Total value being covered |
| `BuildingLimit` | string | Building replacement limit |
| `ContentsLimit` | string | Contents/equipment limit |
| `BusinessInterruptionLimit` | string | BI / loss of income limit |
| `Deductible` | string | Base deductible |
| `FloodSublimit` | string | Flood coverage sublimit |
| `EarthquakeSublimit` | string | Earthquake coverage sublimit |
| `NamedPerilsExclusions` | array | Explicitly excluded perils |
| `SpecialConditions` | array | Endorsements or conditions |
| `PolicyPeriod` | string | Coverage start–end dates |
| `CarrierAMBestRating` | string | AM Best financial strength rating |
| `QuoteReferenceNumber` | string | Carrier's internal reference |
| `ExpiryDate` | date | Quote valid until |
| `Underwriter` | string | Carrier underwriter name/email |

#### AI-Computed Fields (Placement Engine Output)

| Field | Type | Description |
|-------|------|-------------|
| `PlacementScore` | number | Composite score (0–100) |
| `PlacementRank` | number | Rank among all quotes for this submission |
| `RecommendationRationale` | string | Plain-language recommendation |
| `CoverageAdequacy` | string | Adequate, Partial, Insufficient |
| `CoverageGaps` | array | Identified gaps vs. requested coverage |
| `PremiumPercentile` | string | How premium compares to market (Low / Market / Above Market) |

### Placement

| Field | Type | Description |
|-------|------|-------------|
| `PlacementID` | uuid | Unique identifier |
| `ClientID` | uuid | Client |
| `SubmissionID` | uuid | Related submission |
| `SelectedQuotes` | array | QuoteIDs in the placement (one per line) |
| `TotalAnnualPremium` | string | Sum of all selected quote premiums |
| `EffectiveDate` | date | Binding effective date |
| `ExpirationDate` | date | Policy expiry date |
| `PlacementRationale` | string | AI-generated placement summary |
| `BoundDate` | date | Date coverage was bound |
| `BrokerNotes` | string | Broker annotations |

### Carrier Profile (AM Best Data)

Carrier profiles are populated from uploaded AM Best Credit Reports and MD&A annual statement filings. They feed directly into the Placement Engine's carrier scoring and appetite-matching logic. Each carrier in the carrier list may have one AMB Credit Report and one MD&A on file.

#### AMB Credit Report Fields

These fields are extracted from AM Best Credit Reports (e.g., `Acuity - AMB Credit Report (Feb 2025).pdf`).

| Field | Type | Description |
|-------|------|-------------|
| `CarrierID` | uuid | Unique identifier |
| `CarrierName` | string | Legal company name |
| `AMBNumber` | string | AM Best company identifier (e.g., 001234) |
| `NAICCode` | string | NAIC company code |
| `FinancialStrengthRating` | string | AM Best FSR letter grade: A++, A+, A, A-, B++, B+, B, B-, C++, C+, C, C-, D, E, F, S |
| `IssuerCreditRating` | string | AM Best long-term ICR: aaa, aa+, aa, aa-, a+, a, a-, bbb+, bbb, bbb-, bb+, bb, etc. |
| `RatingOutlook` | string | Stable, Positive, Negative, Under Review — Developing, Under Review — Positive, Under Review — Negative |
| `BalanceSheetStrength` | string | Strongest, Very Strong, Strong, Adequate, Weak, Very Weak |
| `OperatingPerformance` | string | Strongest, Strong, Adequate, Weak, Very Weak |
| `BusinessProfile` | string | Favorable, Neutral, Limited |
| `ERMAssessment` | string | Very Strong, Strong, Appropriate, Weak, Very Weak |
| `NetPremiumsWritten` | string | Most recent year NPW ($000s) |
| `PolicyholdersSurplus` | string | Policyholders' surplus ($000s) |
| `NetLossRatio` | string | Net loss ratio, most recent year (%) |
| `NetExpenseRatio` | string | Net underwriting expense ratio, most recent year (%) |
| `CombinedRatio` | string | Net combined ratio, most recent year (%) |
| `ReturnOnSurplus` | string | Return on surplus, most recent year (%) |
| `FiveYearAvgCombinedRatio` | string | 5-year average combined ratio (%) |
| `ReportDate` | date | AM Best report publication date |
| `AMBReportYear` | string | Year of data covered by the report (e.g., 2024) |

#### MD&A Report Fields (Statutory Annual Statement)

These fields are extracted from Management Discussion & Analysis filings (e.g., `Preferred - MD&A 2025.pdf`). These are statutory documents filed with state regulators and represent the most current audited financials.

| Field | Type | Description |
|-------|------|-------------|
| `DirectWrittenPremium` | string | Direct written premium, most recent year ($000s) |
| `DWPGrowthRate` | string | Year-over-year DWP growth rate (%) |
| `NetPremiumsEarned` | string | Net premiums earned, most recent year ($000s) |
| `TotalAdmittedAssets` | string | Total admitted assets ($000s) |
| `TotalInvestedAssets` | string | Total cash and invested assets ($000s) |
| `LossAndLAEReserves` | string | Unpaid losses and LAE reserves ($000s) |
| `UnearnedPremiums` | string | Unearned premium reserve ($000s) |
| `RBCTotalAdjustedCapital` | string | Risk-Based Capital — Total Adjusted Capital ($000s) |
| `RBCControlLevel` | string | RBC — Authorized control level requirement ($000s) |
| `NWPtoSurplusRatio` | string | Net written premium to surplus ratio (e.g., 1.45:1) |
| `ReinsurancePerRiskRetention` | string | Per-risk reinsurance retention (e.g., $750K) |
| `CATRetention` | string | Catastrophe programme retention (e.g., $15M) |
| `ReinsuranceCessionRate` | string | % of gross premiums ceded to reinsurers (e.g., 16.1%) |
| `GeographicConcentration` | array | States licensed and operating, with DWP % per state |
| `LinesOfBusinessWritten` | array | LOBs with net premiums earned ($000s) and % of total |
| `MDARYear` | string | Year covered by MD&A (e.g., 2024) |
| `NetIncome` | string | Net income for the year ($000s) |
| `UnderwritingGainLoss` | string | Underwriting gain/(loss) for the year ($000s) |
| `NetInvestmentIncome` | string | Net investment income ($000s) |

#### Sample Carrier Profiles (Seeded from Uploaded AM Best Reports)

The following five carriers are pre-seeded for development and demo using the uploaded reports:

| Carrier | NAIC | Geography | Key LOBs | Notable (from MD&A 2024) |
|---------|------|-----------|----------|--------------------------|
| Acuity, A Mutual Insurance Company | — | Midwest/national | Commercial multi-peril, auto, workers comp | High-growth, strong balance sheet |
| Indiana Farmers Mutual Insurance | — | Indiana-focused | Farm/agri, commercial, personal lines | Regional, conservative underwriting |
| Midwest Family Mutual Insurance | — | Midwest regional | Personal and small commercial | Small carrier, community focus |
| Preferred Mutual Insurance Company | 15024 | NY, MA, NH, NJ | Auto (46.3%), homeowners (31.6%), commercial multi-peril (18.4%) | DWP $407M (+20.4%), combined ratio 99.8%, RBC TAC $270M |
| Society Insurance, A Mutual Company | 15261 | WI-focused, 9 states | Commercial multi-peril (58.5%), workers comp (20%), commercial auto (8%) | Commercial niche (restaurants, bars), combined ratio 109.3%, NWP/surplus 1.45:1 |

---

## ACORD Field Schema

The following fields are extracted from uploaded client documents to pre-populate ACORD forms.

### ACORD 125 — Commercial Lines Application (Source: Prior Declarations, SOV, Broker Notes)

| Field | Type | Description |
|-------|------|-------------|
| `InsuredName` | string | Legal business name |
| `FEIN` | string | Federal Employer ID Number |
| `BusinessPhone` | string | Primary contact phone |
| `BusinessAddress` | string | Mailing address |
| `BusinessType` | string | Corporation, LLC, Partnership, etc. |
| `YearsInBusiness` | number | Operating years |
| `SICCode` | string | Standard Industry Classification code |
| `AnnualGrossRevenue` | string | Annual revenue |
| `NumberOfEmployees` | number | Full-time + part-time headcount |
| `PriorCarrier` | string | Current/prior insurer name |
| `PriorPremium` | string | Prior year total premium |
| `EffectiveDateRequested` | date | Requested policy start |
| `LinesOfBusinessRequested` | array | Lines being quoted |

### ACORD 140 — Property Section (Source: SOV, Loss Runs, Prior Declarations, Property Photos)

| Field | Type | Description |
|-------|------|-------------|
| `PropertyLocations` | array | All property entries |
| `Location.Address` | string | Street address |
| `Location.Occupancy` | string | How property is used |
| `Location.Construction` | string | Frame, Masonry, Steel, etc. |
| `Location.YearBuilt` | number | Year of construction |
| `Location.SquareFootage` | number | Total floor area |
| `Location.BuildingValue` | string | Replacement cost value |
| `Location.ContentsValue` | string | Contents/equipment value |
| `Location.BIValue` | string | Business interruption value |
| `Location.ProtectionClass` | string | ISO Protection Class (1–10) |
| `LossHistory` | array | Past 5 years of claims |
| `LossHistory.Date` | date | Date of loss |
| `LossHistory.CauseOfLoss` | string | Peril (fire, water, theft, etc.) |
| `LossHistory.AmountPaid` | string | Total claim payout |
| `LossHistory.Description` | string | Brief description |
| `PriorPolicyNumber` | string | Expiring policy number |
| `PriorExpirationDate` | date | Current policy expiry |

### Statement of Values (SOV) Fields

| Field | Type | Description |
|-------|------|-------------|
| `SOVLocations` | array | All property entries from SOV |
| `SOVLocation.SiteNumber` | string | Site reference number |
| `SOVLocation.Address` | string | Full address |
| `SOVLocation.BuildingDescription` | string | Property description |
| `SOVLocation.TotalInsuredValue` | string | TIV per location |
| `SOVLocation.BuildingValue` | string | Building TIV |
| `SOVLocation.ContentsValue` | string | Contents TIV |
| `SOVLocation.BIValue` | string | Business interruption value |
| `TotalSOVValue` | string | Sum of all TIVs |

---

## Carrier Appetite & Placement Rules

Placement rules are stored in `data/commercial-brokerage-policies.json` and follow the same structure as other WorkbenchIQ policy files.

### Rule Categories

| Category | Description |
|----------|-------------|
| `carrier_appetite` | Rules for matching a submission to carriers based on property type, TIV, geography |
| `coverage_adequacy` | Rules for validating that quote limits meet or exceed client's insured value |
| `quote_completeness` | Rules for flagging quotes missing required fields |
| `premium_benchmarking` | Rules for rating a premium as below/at/above market |
| `carrier_financial_strength` | Rules for evaluating carrier solvency and financial health using AM Best FSR, combined ratio, NWP-to-surplus ratio, and RBC adequacy from the carrier profile |
| `placement_optimisation` | Rules for scoring and ranking quotes; multi-line combination logic |

### Example Policies

```json
{
  "version": "1.0",
  "effective_date": "2026-01-01",
  "description": "Commercial Brokerage Placement Rules",
  "policies": [
    {
      "id": "APP-001",
      "category": "carrier_appetite",
      "name": "Property TIV Carrier Routing",
      "description": "Route property submissions to appropriate carriers based on Total Insured Value",
      "criteria": [
        {
          "id": "APP-001-A",
          "condition": "TIV < $5M AND protection_class <= 6",
          "action": "Standard market carriers (e.g., Travelers, Intact, Aviva)",
          "rationale": "Small-to-mid commercial property within standard appetite"
        },
        {
          "id": "APP-001-B",
          "condition": "TIV $5M–$25M OR protection_class > 6",
          "action": "Mid-market and specialty carriers; consider surplus lines",
          "rationale": "Above standard threshold or poor protection class"
        },
        {
          "id": "APP-001-C",
          "condition": "TIV > $25M OR coastal property OR flood zone A/AE",
          "action": "Wholesale broker / MGA referral; Lloyd's markets",
          "rationale": "Large or high-hazard risk exceeds retail carrier appetite"
        }
      ]
    },
    {
      "id": "COV-001",
      "category": "coverage_adequacy",
      "name": "Building Limit Adequacy",
      "description": "Validate that the quoted building limit covers the replacement cost value",
      "criteria": [
        {
          "id": "COV-001-A",
          "condition": "quoted_building_limit >= sov_building_value",
          "action": "Pass — coverage is adequate",
          "rationale": "Client is fully covered for building replacement"
        },
        {
          "id": "COV-001-B",
          "condition": "quoted_building_limit >= 0.80 * sov_building_value AND < sov_building_value",
          "action": "Warning — co-insurance penalty risk; recommend increasing limit",
          "rationale": "Below 100% but above 80% co-insurance threshold"
        },
        {
          "id": "COV-001-C",
          "condition": "quoted_building_limit < 0.80 * sov_building_value",
          "action": "Flag — significant co-insurance exposure; carrier may reject claim proportionally",
          "rationale": "Below 80% co-insurance threshold triggers penalty clauses"
        }
      ]
    },
    {
      "id": "BENCH-001",
      "category": "premium_benchmarking",
      "name": "Premium Market Comparison",
      "description": "Rate the quoted premium against the market range for this risk profile",
      "criteria": [
        {
          "id": "BENCH-001-A",
          "condition": "premium < 0.85 * market_median_premium",
          "action": "Flag as Below Market — verify coverage terms are equivalent",
          "rationale": "Significantly below market may indicate reduced coverage or carrier error"
        },
        {
          "id": "BENCH-001-B",
          "condition": "premium BETWEEN 0.85 * market_median AND 1.15 * market_median",
          "action": "Market Rate — no action required",
          "rationale": "Within acceptable market range"
        },
        {
          "id": "BENCH-001-C",
          "condition": "premium > 1.15 * market_median_premium",
          "action": "Above Market — negotiate or seek additional quotes",
          "rationale": "Higher than comparable risks; may warrant pushback"
        }
      ]
    },
    {
      "id": "FSR-001",
      "category": "carrier_financial_strength",
      "name": "Carrier Financial Strength Gate",
      "description": "Evaluate carrier solvency and financial health from AM Best profile before including in placement recommendation",
      "criteria": [
        {
          "id": "FSR-001-A",
          "condition": "FinancialStrengthRating IN ['A++', 'A+', 'A'] AND RatingOutlook != 'Under Review — Negative'",
          "action": "Eligible for placement — display FSR badge in green",
          "rationale": "AM Best A or better indicates superior financial stability; acceptable for commercial property placement"
        },
        {
          "id": "FSR-001-B",
          "condition": "FinancialStrengthRating == 'A-' AND RatingOutlook IN ['Stable', 'Positive']",
          "action": "Eligible for placement — display FSR badge in yellow; note to broker",
          "rationale": "A- is acceptable but warrants monitoring; stable or positive outlook mitigates concern"
        },
        {
          "id": "FSR-001-C",
          "condition": "FinancialStrengthRating IN ['B++', 'B+'] OR RatingOutlook IN ['Negative', 'Under Review — Negative']",
          "action": "Flag for broker review — include warning in quote comparison: 'Carrier financial strength below preferred threshold'",
          "rationale": "B-range carriers carry higher insolvency risk; negative outlook may indicate deteriorating position"
        },
        {
          "id": "FSR-001-D",
          "condition": "FinancialStrengthRating NOT IN ['A++','A+','A','A-','B++','B+'] OR FinancialStrengthRating IS NULL",
          "action": "Exclude from automated placement recommendation; broker must manually override to include",
          "rationale": "Unrated or below B+ carriers pose unacceptable financial risk for commercial property placement"
        }
      ],
      "supplementary_checks": [
        {
          "id": "FSR-001-S1",
          "condition": "CombinedRatio > 108 for most recent two consecutive years",
          "action": "Add underwriting performance warning even if FSR is A- or better",
          "rationale": "Persistent underwriting losses may signal future rating action; brokers should assess capacity risk"
        },
        {
          "id": "FSR-001-S2",
          "condition": "NWPtoSurplusRatio > 3.0",
          "action": "Flag leverage risk — carrier may be capacity-constrained",
          "rationale": "NWP/surplus > 3:1 indicates potential surplus strain; carrier may restrict new business or apply stricter terms"
        }
      ]
    },
    {
      "id": "OPT-001",
      "category": "placement_optimisation",
      "name": "Best Value Placement Score",
      "description": "Composite scoring for placement recommendation",
      "scoring_factors": [
        {
          "factor": "Premium competitiveness",
          "weight": 0.35,
          "description": "Lower premium scores higher, adjusted for coverage breadth"
        },
        {
          "factor": "Coverage completeness",
          "weight": 0.30,
          "description": "Fewer exclusions and higher sublimits score higher"
        },
        {
          "factor": "Carrier financial strength",
          "weight": 0.20,
          "description": "FSR tier scoring: A++ or A+ = 100pts; A = 85pts; A- = 70pts; B++ = 50pts; B+ or below = 25pts; unrated = 10pts. Combined ratio adjustment (from MD&A): < 95% = +10pts; 95–102% = 0pts; 103–108% = -10pts; > 108% = -20pts. NWP-to-surplus > 3:1 triggers a -10pt risk flag."
        },
        {
          "factor": "Quote completeness",
          "weight": 0.15,
          "description": "All required fields populated without ambiguity"
        }
      ]
    }
  ]
}
```

---

## Requirements

### Functional Requirements

#### Dashboard (P0)
- **FR-001**: System MUST display broker dashboard with: total accounts, total bound premium, open submissions count, renewals due within 90 days.
- **FR-002**: System MUST allow filtering/sorting accounts by premium, renewal date, submission status.
- **FR-003**: System MUST flag submissions with no activity for >7 days.

#### Client Research (P0)
- **FR-004**: System MUST accept a company name and return an AI-generated research brief.
- **FR-005**: System MUST use Bing grounding for public company data (SEC filings, annual reports, news).
- **FR-006**: System MUST support optional AM Best / S&P data when LSEG integration is configured.
- **FR-007**: System MUST cite sources for every factual claim in the research brief.
- **FR-008**: System MUST indicate confidence level for fields sourced from limited public data.

#### Submission (P0)
- **FR-009**: System MUST accept uploads of: ACORD forms, SOV (PDF/Excel), loss runs (PDF/Excel), prior declarations, property photos via admin view.
- **FR-010**: System MUST route documents to `brokerDocAnalyzer` for field extraction.
- **FR-011**: System MUST pre-populate ACORD 125 and ACORD 140 fields from extracted data.
- **FR-012**: System MUST display confidence scores per extracted field.
- **FR-013**: System MUST generate a complete submission package (cover email + all docs) on demand.
- **FR-014**: System MUST support sending the submission package to multiple selected carriers.
- **FR-015**: System MUST be architected to support additional ACORD form types beyond 125/140 via configuration.

#### Quote Extraction (P0)
- **FR-016**: System MUST accept carrier quote uploads in PDF and Excel formats.
- **FR-017**: System MUST route quote documents to `brokerQuoteAnalyzer`.
- **FR-018**: System MUST extract all canonical quote fields (see Quote schema) from carrier documents.
- **FR-019**: System MUST normalise carrier-specific field names to the canonical schema.
- **FR-020**: System MUST flag fields with extraction confidence < 60% as "Needs Review".

#### Quote Comparison (P0)
- **FR-021**: System MUST display a side-by-side comparison table for all quotes on a submission.
- **FR-022**: Comparison table MUST include all canonical quote fields as rows, carriers as columns.
- **FR-023**: System MUST run the placement engine and return a ranked recommendation with rationale.
- **FR-024**: System MUST support broker-adjustable weighting (price vs. coverage vs. carrier rating).
- **FR-025**: System MUST generate a client-ready placement summary (PDF export).

#### Client Portfolio (P1)
- **FR-026**: System MUST display per-client policy portfolio with status (in-force, expired, pending).
- **FR-027**: System MUST display claims history summary per client.
- **FR-028**: System MUST display client contacts and carrier/underwriter contacts per account.
- **FR-029**: System MUST auto-categorise uploaded documents into defined document types.
- **FR-030**: System MUST support full-text and semantic search across all documents for a client.

#### RAG / Ask IQ (P1)
- **FR-031**: System MUST support an Ask IQ chat drawer scoped to the current submission or client.
- **FR-032**: System MUST ground chat responses in extracted submission data, quotes, and client documents.
- **FR-033**: System MUST chunk and embed placement rules and carrier guidelines for RAG retrieval.
- **FR-034**: System MUST display citations linking chat responses to source documents.

#### Admin (P1)
- **FR-035**: Admin view MUST support upload and replacement of `commercial-brokerage-policies.json`.
- **FR-036**: Admin view MUST support carrier list management (add, edit, remove carriers).
- **FR-037**: Admin view MUST support upload of carrier quote templates to guide extraction.

#### Carrier Intelligence — AM Best Integration (P1)
- **FR-038**: Admin view MUST support upload of AM Best Credit Report PDFs and MD&A annual statement PDFs per carrier.
- **FR-039**: System MUST route AM Best document uploads to `ambReportAnalyzer` and auto-detect whether the document is an AMB Credit Report or an MD&A filing.
- **FR-040**: System MUST extract all AMB Credit Report fields (FSR, ICR, outlook, balance sheet strength, operating performance, business profile, ERM, 5-year ratios) and populate the carrier's `CarrierProfile` record.
- **FR-041**: System MUST extract all MD&A fields (DWP, combined ratio, total admitted assets, loss reserves, RBC TAC and control level, NWP-to-surplus ratio, reinsurance retentions, geographic concentration, LOB breakdown) and populate the carrier's `CarrierProfile` record.
- **FR-042**: System MUST match the extracted `NAICCode` or `CarrierName` from the AM Best report to an existing carrier in the carrier list; if no match, prompt admin to confirm or create a new carrier entry.
- **FR-043**: Placement engine MUST incorporate `FinancialStrengthRating` and `CombinedRatio` from the carrier profile when computing the carrier financial strength component of the placement score (OPT-001).
- **FR-044**: Quote comparison view MUST display each carrier's FSR, ICR, rating outlook, and most recent combined ratio sourced from the stored carrier profile alongside the quote data.

### Non-Functional Requirements

- **NFR-001**: Document extraction MUST complete within 30 seconds per document.
- **NFR-002**: Quote extraction from PDF MUST complete within 45 seconds per document.
- **NFR-003**: Quote extraction from Excel MUST complete within 20 seconds per document.
- **NFR-004**: Placement recommendation MUST be generated within 10 seconds of all quotes being extracted.
- **NFR-005**: Client research brief MUST be returned within 60 seconds.
- **NFR-006**: System MUST support SOV Excel files with up to 500 property locations.
- **NFR-007**: System MUST support submission packages with up to 20 documents.
- **NFR-008**: System MUST handle quote PDFs up to 10MB.
- **NFR-009**: AM Best Credit Report extraction MUST complete within 30 seconds per document.
- **NFR-010**: MD&A annual statement extraction MUST complete within 45 seconds per document (MD&A filings can be 10–20 pages of dense financial tables).

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BROKER_PERSONA_ENABLED` | No | `true` | Enable commercial brokerage persona |
| `BROKER_DOC_ANALYZER` | No | `brokerDocAnalyzer` | Custom document analyzer ID |
| `BROKER_QUOTE_ANALYZER` | No | `brokerQuoteAnalyzer` | Custom quote analyzer ID |
| `BROKER_POLICIES_PATH` | No | `data/commercial-brokerage-policies.json` | Path to placement rules |
| `BING_GROUNDING_ENABLED` | No | `true` | Enable Bing for client research |
| `LSEG_INTEGRATION_ENABLED` | No | `false` | Enable AM Best / S&P via LSEG |
| `LSEG_API_KEY` | If above true | — | LSEG API key |
| `SOV_MAX_LOCATIONS` | No | `500` | Max property locations in a single SOV |
| `DEFAULT_LINE_OF_BUSINESS` | No | `property` | Default LOB for new submissions |
| `AMB_REPORT_ANALYZER` | No | `ambReportAnalyzer` | Custom analyzer ID for AM Best Credit Report and MD&A parsing |
| `CARRIER_PROFILE_AUTO_UPDATE` | No | `true` | Auto-update carrier profile when new AM Best report is uploaded |

### Azure Content Understanding Analyzer Setup

Two custom analyzers must be provisioned before use. See `scripts/setup_broker_analyzers.py` for automated setup.

**`brokerDocAnalyzer`** — extends `prebuilt-document`:
- Field schema: all ACORD 125, ACORD 140, and SOV fields listed in the data model.
- Optimised for: ACORD PDFs, Statement of Values, loss run schedules, prior policy declarations.

**`brokerQuoteAnalyzer`** — extends `prebuilt-document`:
- Field schema: all canonical Quote fields listed in the data model.
- Optimised for: carrier quote PDFs and Excel workbooks.
- Includes a carrier-specific field mapping table (configurable per carrier via admin).

**`ambReportAnalyzer`** — extends `prebuilt-document`:
- Field schema: all AMB Credit Report fields + MD&A fields listed in the Carrier Profile data model.
- Optimised for: AM Best Credit Report PDFs (structured rating/financial tables) and statutory MD&A annual statement PDFs.
- Detects report type automatically (AMB Credit Report vs. MD&A) from document header and extracts the corresponding field set.
- Key extraction targets: FSR letter grade, ICR, rating outlook, BCAR tier labels, 5-year financial data table, lines of business table, geographic premium distribution table, reinsurance programme summary, RBC data table.
- Carrier matching: links extracted `NAICCode` or `CarrierName` to the carrier list for automatic profile update.

### Line of Business Extensibility

New lines of business can be added by providing:
1. `data/acord-forms/<lob>-fields.json` — field schema for the relevant ACORD form.
2. `data/analyzers/<lob>-analyzer-config.json` — Azure CU analyzer configuration.
3. `data/commercial-brokerage-policies.json` — updated placement rules for the new LOB.
4. Optional: sample carrier quotes for the new LOB to seed the quote extractor.

The frontend will automatically render a new LOB tab in the Submission Builder when the backend returns it in the `/api/personas/commercial-brokerage/lob` endpoint.

---

## Sample Data

The following sample files from Naveen Dhar's Broker Workbench Shared Folder serve as ground-truth inputs for development and testing:

| File | Type | Purpose |
|------|------|---------|
| `ACORD_125_Ridgeview.pdf` | ACORD form | Commercial application for Ridgeview Properties |
| `ACORD_140_Property_Ridgeview.pdf` | ACORD form | Property section for Ridgeview |
| `SOV_Ridgeview.pdf` | SOV | Statement of values for Ridgeview |
| `LossRuns_Ridgeview.pdf` | Loss runs | Claims history for Ridgeview |
| `Property_Photos_Summary_Ridgeview.pdf` | Photos | Property photo summary |
| `sample-quote-aig.pdf` | Carrier quote | AIG quote (PDF format) |
| `sample-quote-zurich.xlsx` | Carrier quote | Zurich quote (Excel format) |
| `Application email.docx` | Submission email | Template submission cover email |

**Carrier AM Best Reports (for Carrier Profile Seeding)**

| File | Report Type | Carrier | Key Data Points |
|------|-------------|---------|-----------------|
| `Acuity - AMB Credit Report (Feb 2025).pdf` | AMB Credit Report | Acuity | FSR, ICR, outlook, balance sheet / operating performance tiers, 5-year ratios |
| `Acuity - MD&A 2025.pdf` | MD&A (2024 statutory) | Acuity | DWP, combined ratio, admitted assets, RBC, LOB breakdown, reinsurance |
| `IN Farmers - AMB Credit Report (Jun 2024).pdf` | AMB Credit Report | Indiana Farmers Mutual | FSR, ICR, outlook, balance sheet / operating performance tiers, 5-year ratios |
| `IN Farmers - MD&A 2025.pdf` | MD&A (2024 statutory) | Indiana Farmers Mutual | DWP, combined ratio, geographic concentration (Indiana focus), RBC |
| `Midwest Family - AMB Credit Report (Apr 2025).pdf` | AMB Credit Report | Midwest Family Mutual | FSR, ICR, outlook, balance sheet / operating performance tiers |
| `Midwest Family - MD&A 2025.pdf` | MD&A (2024 statutory) | Midwest Family Mutual | DWP, combined ratio, Midwest geographic concentration, RBC |
| `Preferred - AMB Credit Report (Jul 2024).pdf` | AMB Credit Report | Preferred Mutual Insurance | FSR, ICR, outlook, balance sheet / operating performance tiers |
| `Preferred - MD&A 2025.pdf` | MD&A (2024 statutory) | Preferred Mutual Insurance | DWP $407M (+20.4%), combined ratio 99.8%, auto (46.3%) + HO (31.6%) + CMP (18.4%), TAC $270M, NE market |
| `Society - AMB Credit Report (Jun 2024).pdf` | AMB Credit Report | Society Insurance | FSR, ICR, outlook, balance sheet / operating performance tiers |
| `Society - MD&A 2025.pdf` | MD&A (2024 statutory) | Society Insurance | DWP (commercial niche), combined ratio 109.3%, WI-focused (9 states), CMP 58.5% + WC 20%, NWP/surplus 1.45:1 |

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: ACORD field extraction accuracy ≥ 90% on Ridgeview sample set (validated against manual entry).
- **SC-002**: Quote extraction accuracy ≥ 85% across AIG PDF and Zurich Excel formats.
- **SC-003**: Placement engine returns a recommendation for 95%+ of multi-quote submissions.
- **SC-004**: Submission package generation reduces time from hours to < 5 minutes.
- **SC-005**: Broker satisfaction rating of 4+/5 for quote comparison usefulness (validated with Naveen Dhar and pilot users).
- **SC-006**: Client research brief judged "useful or better" by broker in 80%+ of trials.

---

## Assumptions

1. MVP scope is commercial **property** insurance only (ACORD 125 + 140). Other lines (D&O, Workers Comp, GL, Benefits) are explicitly deferred to Phase 2.
2. The retail-broker-to-insurer flow is in scope. Wholesale broker / MGA intermediary flow is deferred.
3. Mud map / syndicated placement (Lloyd's, Bermuda, excess & surplus) is explicitly out of scope for MVP.
4. AM Best and S&P data are optional in MVP (Bing grounding handles public data). LSEG integration is a Phase 2 enhancement.
5. The system does not send emails directly in MVP — it generates a submission package for the broker to send via their existing email client.
6. The Commercial Underwriting persona (Amol's demo — NFIP data, flood risk, property risk maps) is a separate persona. The Brokerage persona does not replicate it.
7. Sample data from Naveen Dhar's shared folder is used for all development testing and demo purposes.
8. Quotes are uploaded by the broker. Automated inbox polling (email-to-quote parsing) is deferred to Phase 2.
9. The five carrier profiles seeded from Naveen Dhar's AM Best sample reports (Acuity, Indiana Farmers, Midwest Family, Preferred Mutual, Society Insurance) are used for all development testing and demo purposes. All five are commercial P&C carriers appropriate for commercial property submissions.
10. AM Best report PDFs vary in layout between carriers and report years. The `ambReportAnalyzer` uses the structured section headers (e.g., "Balance Sheet Strength", "Financial Performance") as extraction anchors. Scanned/image-only reports may require OCR pre-processing before field extraction.

---

## Open Questions

1. **Q**: Should the submission package email be sent from within WorkbenchIQ (via Outlook API) or downloaded and sent manually?
   - **Proposed**: Download/copy for MVP; Outlook send integration in Phase 2.

2. **Q**: How should multi-location SOV files be handled when some locations have missing fields?
   - **Proposed**: Extract what is available; flag missing fields per location; broker completes manually.

3. **Q**: Should quote comparison support weighting customisation per broker, or per submission?
   - **Proposed**: Per-submission for MVP (simpler UX), with broker-level defaults configurable in admin.

4. **Q**: Is the placement score algorithm proprietary? Does it need to be auditable/explainable?
   - **Proposed**: Scores are fully explainable with rule citations; no black-box ML in the engine.

5. **Q**: What carrier list should be seeded? Canada-specific (Aviva, Intact, Economical) or US-focused?
   - **Proposed**: Seed with both markets; make carrier list admin-configurable from day one.

6. **Q**: Should the system support ACORD XML / IVANS integration for electronic submissions to carriers?
   - **Proposed**: Defer IVANS/ACORD XML to Phase 2; PDF package is sufficient for MVP.

7. **Q**: How stale can a carrier's AM Best profile be before the placement engine flags it as potentially outdated?
   - **Proposed**: Surface a warning in the quote comparison view when a carrier's AM Best report is older than 12 months. Admin can suppress the warning per carrier.

8. **Q**: Should the `ambReportAnalyzer` attempt to extract AM Best data from LSEG/Bloomberg-formatted reports in addition to native AM Best PDFs?
   - **Proposed**: Native AM Best PDF format only for MVP. LSEG-formatted exports to be handled in Phase 2 when the LSEG integration is built.

---

## Future Enhancements (Out of Scope for MVP)

1. **Wholesale Broker / MGA Flow** — Multi-tier submission routing with wholesale intermediary.
2. **Mud Map Builder** — Visualise syndicated risk placement layers (Lloyd's, Bermuda, E&S markets).
3. **Inbox Parsing** — Automatically parse inbound carrier quote emails and attach to submissions.
4. **IVANS / ACORD XML** — Electronic submission to carrier management systems.
5. **LSEG / AM Best / S&P Live Integration** — Real-time financial strength data via LSEG API, replacing manual PDF uploads for carrier profiles. Enables automatic refresh of FSR, ICR, and financial ratios without admin intervention.
6. **Additional Lines of Business** — D&O, Workers Comp, General Liability, Benefits, Cyber.
7. **Renewal Automation** — Auto-generate renewal submission from prior year's bound placement.
8. **Carrier Portal Integration** — Direct API submission to carrier rating portals (Applied Epic, etc.).
9. **Client Portal** — Broker-branded portal for clients to view their own coverage and documents.
10. **Commission Tracking** — Track earned premiums and broker commissions per placement.
