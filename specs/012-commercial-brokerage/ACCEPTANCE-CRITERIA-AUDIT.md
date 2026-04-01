# Commercial Brokerage — Acceptance Criteria Audit

> **Generated**: 2026-03-26  
> **Purpose**: Track implementation status of every acceptance criterion from US-1 through US-6. Use this to guide the next wave of bug squash and feature completion.

## Legend

| Icon | Status |
|------|--------|
| ✅ | **Fully Implemented** — criterion met end-to-end |
| 🟡 | **Partially Implemented** — core logic exists but gaps remain |
| ❌ | **Not Implemented** — no meaningful implementation |

## Summary

| Story | Fully | Partial | Not Impl | Total |
|-------|-------|---------|----------|-------|
| US-1: Broker Dashboard | 1 | 3 | 0 | 4 |
| US-2: Client Research | 1 | 2 | 2 | 5 |
| US-3: Submission Package | 1 | 2 | 0 | 5 |
| US-4: Quote Collection | 1 | 2 | 1 | 5 |  <!-- Note: US-3 has 2 partial + 1 not-impl for AC5 -->
| US-5: Quote Comparison | 1 | 1 | 3 | 5 |
| US-6: Client Portfolio | 0 | 2 | 3 | 5 |
| **Totals** | **5** | **12** | **9** | **29** | <!-- Note: US-3-AC5 counted as not-impl below -->

---

## US-1: Broker Dashboard (P0)

### AC-1.1 — Dashboard metrics ✅
> Given a broker logs in, When the dashboard loads, Then they see: total accounts count, total bound premium, number of open submissions, and number of renewals due in the next 90 days.

**Status: FULLY IMPLEMENTED**
- Backend `GET /api/broker/dashboard` computes all 4 metrics via `BrokerStorage.get_dashboard_metrics()`
- Frontend `BrokerDashboard.tsx` renders all 4 metric cards
- No gaps

### AC-1.2 — Renewals section 🟡
> Given an account is within 90 days of renewal, When viewing the dashboard, Then it appears in a "Renewals" section with the renewal date highlighted.

**Status: PARTIALLY IMPLEMENTED**
- Backend computes `renewals_due_90_days` count and exposes `renewal_date` on clients
- Frontend shows renewal date inline on account cards
- **Gap**: No dedicated "Renewals" section with a filtered list; no highlighted renewal date styling

### AC-1.3 — Stale submission indicator 🟡
> Given an open submission has had no activity for 7 days, When viewing the dashboard, Then it is flagged with a stale indicator.

**Status: PARTIALLY IMPLEMENTED**
- Backend computes `stale_submissions` count (submissions with `updated_at` > 7 days old)
- `DashboardMetrics` includes `stale_submissions`
- **Gap**: Frontend does not display any stale badge/indicator on submissions or dashboard

### AC-1.4 — Click account opens client profile 🟡
> Given the broker clicks any account card, When the account opens, Then they see the full client profile (US-6).

**Status: PARTIALLY IMPLEMENTED**
- Clicking an account opens `ClientWorkspace` with Research/Submissions/Quotes tabs
- Backend exposes `GET /api/broker/clients/{client_id}`
- **Gap**: Full client profile (policy portfolio, claims summary, contacts, document library) per US-6 is not implemented

---

## US-2: Client Research & Market Intelligence (P0)

### AC-2.1 — Structured research brief ✅
> Given a broker enters a company name, When research runs, Then the system returns: company overview, financials summary, industry risk profile, estimated insurance needs by line, and likely carrier appetite matches.

**Status: FULLY IMPLEMENTED**
- Research engine returns 25+ structured fields matching all required categories
- Frontend renders Business Overview, Financial Summary, Risk Profile, Insurance Needs, and Carrier Appetite cards
- No gaps

### AC-2.2 — Bing-grounded citations 🟡
> Given a public company is searched, When results return, Then the system includes grounded citations from SEC filings, annual reports, and news via Bing.

**Status: PARTIALLY IMPLEMENTED**
- Research engine uses Azure OpenAI Responses API with `web_search_preview` tool
- Citations are extracted from Bing response and displayed as clickable links
- **Gap**: No explicit public-company detection; no guarantee citations are from SEC/annual reports specifically; no source-type labeling (SEC vs news vs report)

### AC-2.3 — AM Best / S&P carrier rating metrics 🟡
> Given AM Best / S&P data is available, When research runs, Then the brief includes per-carrier: FSR, ICR, rating outlook, balance sheet strength, operating performance, combined ratio, NWP-to-surplus ratio.

**Status: PARTIALLY IMPLEMENTED**
- Backend `CarrierProfile` model has all required fields (FSR, ICR, outlook, balance sheet, operating performance, combined ratio, NWP-to-surplus)
- **Gap**: Research brief path only surfaces `carrier`, `rating`, `appetite`, `rationale` — does not pull full carrier metrics from CarrierProfile into the research output. No LSEG integration or uploaded carrier doc parsing

### AC-2.4 — Edit and annotate brief ❌
> Given the research completes, When viewing the brief, Then the broker can edit and annotate it before the client call.

**Status: NOT IMPLEMENTED**
- Research brief is read-only in the UI
- No update/annotate endpoint in backend
- **Gap**: Need inline editing on research cards, annotation support, and a persistence API

### AC-2.5 — Low-confidence field indicators ❌
> Given a private company is searched with limited public data, When results return, Then the system clearly indicates which fields have low-confidence sourcing.

**Status: NOT IMPLEMENTED**
- Only an overall `confidence_level` (High/Medium/Low) exists on the whole brief
- **Gap**: Need per-field confidence scores in the research schema, and UI highlighting for low-confidence individual fields

---

## US-3: Submission Package Generation (P0)

### AC-3.1 — SOV + loss runs → ACORD 140 🟡
> Given a broker uploads an SOV PDF and loss runs, When extraction runs, Then property details and claims history fields are pre-populated in the ACORD 140 form.

**Status: PARTIALLY IMPLEMENTED**
- Backend reads file content from disk, extracts `property_locations` and `loss_history` via LLM
- ACORD 140 template exists with property fields
- **Gap**: Loss history is returned as a JSON array but not cleanly mapped into canonical ACORD 140 loss-history fields (`LossDate`, `CauseOfLoss`, `LossAmountPaid`)

### AC-3.2 — Prior declaration → ACORD 125 🟡
> Given a broker uploads a prior policy declaration, When extraction runs, Then coverage history, limits, and deductibles are pre-populated in ACORD 125.

**Status: PARTIALLY IMPLEMENTED**
- Prior declaration upload supported; extraction includes `prior_carrier`, `prior_premium`, `effective_date`, `lines_of_business`
- ACORD 125 template has Insurance History and Coverage sections
- **Gap**: Coverage limits and deductibles are not extracted as ACORD 125 fields; schema only has basic insurance history

### AC-3.3 — Source document + confidence per field 🟡
> Given auto-populated fields are shown, When the broker reviews them, Then each field shows its source document and a confidence score.

**Status: PARTIALLY IMPLEMENTED**
- Confidence scores are returned per field and displayed as color-coded badges in AcordFormView
- **Gap**: No field-level source document provenance — the UI shows confidence only, not which document a value was extracted from

### AC-3.4 — Generate Submission Package ✅
> Given the ACORD form is complete, When the broker clicks "Generate Submission Package", Then the system produces: a submission cover email, ACORD 125, ACORD 140, SOV, and loss runs bundled as a submission package.

**Status: FULLY IMPLEMENTED**
- Backend compiles cover email, ACORD 125, ACORD 140, SOV, documents, and carrier emails
- Frontend has carrier selection + generate package flow
- Package returned as structured JSON (not zip download, but all content present)

### AC-3.5 — Send to carriers ❌
> Given a submission package is generated, When the broker selects carriers and clicks "Send", Then individual submission emails are dispatched to each selected carrier.

**Status: NOT IMPLEMENTED**
- Backend generates per-carrier email drafts only; no send/dispatch endpoint
- Frontend review UI supports save/copy draft only, no send action
- **Gap**: Need email dispatch integration and send button in UI

---

## US-4: Quote Collection & Extraction (P0)

### AC-4.1 — PDF quote extraction with confidence 🟡
> Given a broker uploads a PDF quote from AIG, When extraction runs, Then premium, limits, deductible, exclusions, and effective date are extracted and displayed with confidence scores.

**Status: PARTIALLY IMPLEMENTED**
- Backend extracts `annual_premium`, `building_limit`, `contents_limit`, `deductible`, `named_perils_exclusions`, `policy_period` with confidence scores
- **Gap**: No real PDF parsing (just raw UTF-8 decode); no separate `effective_date` field; confidence scores stored but not displayed in the UI

### AC-4.2 — Excel quote parsing ❌
> Given a broker uploads an Excel quote from Zurich, When extraction runs, Then the system parses all relevant tabs and maps fields to the canonical quote schema.

**Status: NOT IMPLEMENTED**
- Backend accepts `.xlsx` uploads and tags `source_format = "xlsx"`
- **Gap**: No workbook/tab parsing logic; no sheet-by-sheet extraction or mapping to canonical schema

### AC-4.3 — Multiple quotes in comparison view ✅
> Given multiple quotes are uploaded for the same submission, When all extractions complete, Then all quotes appear in the Quote Comparison view (US-5).

**Status: FULLY IMPLEMENTED**
- Submission model stores `quotes: List[Quote]`
- Compare endpoint scores all quotes; frontend renders all in comparison cards/table
- No gaps

### AC-4.4 — Low-confidence field flagging 🟡
> Given a field could not be extracted with confidence ≥ 60%, When displayed, Then the field is flagged "Needs Review" and highlighted in amber.

**Status: PARTIALLY IMPLEMENTED**
- Backend identifies low-confidence fields (`score < 0.60`) and logs them
- Quotes carry `confidence_scores` in the model
- **Gap**: UI does not show per-field confidence, "Needs Review" badges, or amber highlighting

### AC-4.5 — Missing field clarification prompt 🟡
> Given a quote is missing a required comparison field, When displayed, Then the system prompts the broker to request clarification from the carrier.

**Status: PARTIALLY IMPLEMENTED**
- Backend computes `coverage_gaps` in placement scoring
- Frontend displays gaps in quote cards
- **Gap**: No explicit required-field rules; no actionable prompt to request clarification from carrier

---

## US-5: Quote Comparison & Placement Recommendation (P0)

### AC-5.1 — Normalized comparison table 🟡
> Given two or more quotes are extracted, When the broker opens Quote Comparison, Then they see a normalized table with columns per carrier and rows for: Annual Premium, TIV, Building Limit, Contents Limit, BI, Deductible, Flood Sublimit, Earthquake Sublimit, Named Perils Exclusions, AM Best Rating, Terms.

**Status: PARTIALLY IMPLEMENTED**
- Frontend renders a comparison table with most required rows
- Backend returns comparison data via `POST /compare`
- **Gap**: Backend comparison output is a partial flat summary, not a fully normalized matrix; frontend missing explicit "Terms" row

### AC-5.2 — AI recommendation with rationale ✅
> Given the comparison table is displayed, When the AI recommendation runs, Then the system highlights the recommended carrier with a plain-language rationale citing the top 3 reasons.

**Status: FULLY IMPLEMENTED**
- Backend scoring ranks quotes and builds a plain-language rationale with top 3 reasons
- Frontend highlights recommended carrier and displays AI Recommendation panel
- No gaps

### AC-5.3 — Multi-line carrier combination ❌
> Given a multi-line submission (property + D&O), When comparing quotes, Then the system can model a carrier combination and show the blended total premium.

**Status: NOT IMPLEMENTED**
- No data model, scoring logic, or UI for combining carriers across lines
- **Gap**: Need cross-submission/cross-LOB carrier combination modeling and blended premium calculation

### AC-5.4 — Client presentation export ❌
> Given the broker selects a placement, When they click "Generate Client Presentation", Then the system produces a client-ready comparison summary (exportable as PDF or PPTX).

**Status: NOT IMPLEMENTED**
- No "Generate Client Presentation" action or export in UI or backend
- **Gap**: Need a presentation generation endpoint and PDF/PPTX export capability

### AC-5.5 — Adjustable ranking weights ❌
> Given the broker adjusts weights (e.g., "price is most important"), When the ranking updates, Then the recommended carrier re-sorts accordingly.

**Status: NOT IMPLEMENTED**
- Backend weights are hardcoded (premium 35%, coverage 30%, financial 20%, completeness 15%)
- **Gap**: Need configurable weight parameters in the compare API and a weight-adjustment UI

---

## US-6: Client & Policy Portfolio View (P1)

### AC-6.1 — Full client profile 🟡
> Given a broker opens an account, When the client profile loads, Then they see: company details, policy portfolio (in-force, expired, pending), claims summary, client contacts, carrier/underwriter contacts, and a document library.

**Status: PARTIALLY IMPLEMENTED**
- Client model has core fields (name, industry, business type, contacts)
- ClientWorkspace shows company header + Research/Submissions/Quotes tabs
- **Gap**: No policy portfolio view, no claims summary, no carrier/underwriter contacts, no document library section

### AC-6.2 — Renewal alert + quick action 🟡
> Given a policy is within 90 days of expiry, When viewing the portfolio, Then it is flagged with a renewal alert and a "Start Renewal Submission" quick action.

**Status: PARTIALLY IMPLEMENTED**
- Backend computes renewals due; client model includes `renewal_date`
- Dashboard shows renewal metric; workspace header shows renewal date
- **Gap**: No policy-level expiry flags and no "Start Renewal Submission" quick action button

### AC-6.3 — Ask IQ claims query ❌
> Given a broker asks "What claims has this client had in the last 3 years?" in Ask IQ, When the response returns, Then it cites data from the claims summary in the client profile.

**Status: NOT IMPLEMENTED**
- No Ask IQ endpoint, no claims summary data, no Q&A UI
- **Gap**: Need claims data model, Ask IQ endpoint, and citation wiring

### AC-6.4 — Auto-categorise uploaded documents ❌
> Given new documents are uploaded, When they are processed, Then they are automatically categorised into: Applications, Endorsements, Schedules, Loss Runs, or Quotes.

**Status: NOT IMPLEMENTED**
- Document upload requires manual type selection
- Categories don't match the spec (using SOV, ACORD, loss_runs instead)
- **Gap**: Need automatic classification pipeline (LLM or rule-based)

### AC-6.5 — Document search ❌
> Given the document library has 20+ files, When a broker searches "flood exclusion", Then the relevant clause in the most recent policy declaration is surfaced.

**Status: NOT IMPLEMENTED**
- No document indexing, full-text search, or clause extraction
- **Gap**: Need document indexing/search, clause extraction, and recency-aware ranking

---

## Priority Recommendations for Next Wave

### High Priority (P0 gaps that block demo)
1. **AC-4.1** — Add real PDF text extraction (e.g., PyMuPDF/pdfplumber) to quote extractor
2. **AC-4.4** — Show per-field confidence badges + "Needs Review" amber highlighting in QuotesTab
3. **AC-3.3** — Add source document provenance per extracted ACORD field
4. **AC-1.3** — Display stale submission indicators in dashboard UI
5. **AC-1.2** — Add a dedicated "Renewals" section on dashboard

### Medium Priority (P0 features not yet started)
6. **AC-4.2** — Excel quote parsing (openpyxl tab traversal + field mapping)
7. **AC-5.5** — Configurable ranking weights API + UI sliders
8. **AC-5.4** — Client presentation export (PDF/PPTX generation)
9. **AC-3.5** — Email dispatch integration for submission send
10. **AC-2.4** — Editable/annotatable research briefs

### Lower Priority (P1 and stretch)
11. **AC-6.1** — Full client profile (policy portfolio, claims, contacts, doc library)
12. **AC-6.3** — Ask IQ with claims grounding
13. **AC-6.4** — Auto document categorisation
14. **AC-6.5** — Document search with clause extraction
15. **AC-5.3** — Multi-line carrier combination + blended premium
16. **AC-2.5** — Per-field confidence in research briefs
17. **AC-2.3** — Wire carrier profile metrics into research output
