# Leo — History

## Project Context

underwriting-assistant is an AI-powered underwriting assistant for mortgage and insurance workflows. Built with a Python (FastAPI) backend and Next.js frontend, using Azure OpenAI for document analysis and scoring.

## Learnings

### 2026-01-27: Commercial Brokerage MVP Review

**Context:** Comprehensive architecture review of the Commercial Brokerage persona implementation against spec `specs/012-commercial-brokerage/spec-commercial-brokerage.md`.

**Key Findings:**
- **Architecture:** Production-quality scaffolding — all P0 features have complete implementations
- **Data models:** Fully aligned with spec, no schema gaps
- **Engines:** PlacementEngine, QuoteExtractor, ClientResearchEngine, SubmissionGenerator all complete and production-ready
- **Integration gap:** API endpoints return mock data instead of calling engines (4 endpoints need wiring)
- **Frontend:** Complete component structure, but frontend types don't match backend models exactly

**Decision:** MVP is ship-ready after ~2 hours of engine wiring work

**Patterns Observed:**
- Placement scoring uses composite weights (premium 35%, coverage 30%, financial 20%, completeness 15%)
- Quote extraction uses LLM with structured JSON prompt (confidence scoring built-in)
- Client research uses Azure Responses API with web_search_preview for Bing grounding, falls back to chat_completion
- Carrier financial strength gating follows AM Best FSR tiers (A++ through B+, with combined ratio adjustments)

**File Paths:**
- Backend models: `app/broker/models.py`
- API router: `app/broker/api.py`
- Engines: `app/broker/placement_engine.py`, `quote_extractor.py`, `research_engine.py`, `submission_generator.py`
- Frontend workbench: `frontend/src/components/broker/BrokerWorkbench.tsx`
- Placement policies: `prompts/commercial-brokerage-policies.json`, `data/commercial-brokerage-policies.json`
- Persona config: `app/personas.py` (lines 3488-3894), `frontend/src/lib/personas.ts` (lines 86-96)

**Technical Debt:**
- Frontend types need alignment with backend models
- Storage layer is in-memory (needs PostgreSQL persistence)
- No input validation on file uploads
- QuoteExtractor has 15KB document limit (needs chunking for large docs)

**User Preference:**
- Jawad wants thorough reviews with clear ship/no-ship verdict
- Concise summaries preferred (2-3 sentences at end, not verbose progress updates)

### 2026-03-25: Backend Engines Wired to API Router

**Status Update:** Ben completed integration of all 4 engines (QuoteExtractor, PlacementEngine, ClientResearchEngine, BrokerStorage helper) into `app/broker/api.py`. Engine stubs previously returning mock data are now fully wired and functional.

**Key Changes:**
- API response shapes finalized: `POST /api/broker/submissions/{submission_id}/quotes`, `POST /api/broker/submissions/{submission_id}/compare`, `POST /api/broker/clients/{client_id}/research`
- Error handling: All engines wrapped in try/except for graceful degradation
- Storage integration: Dict ↔ dataclass conversions working correctly

**Impact on Architecture Review:** MVP now ready for ship (integration gap resolved).

### 2026-07-14: Commercial Brokerage UX Redesign

**Context:** The broker UI had a flat tab architecture (Dashboard/Research/Submission/Quotes all at the same level in BrokerWorkbench). This conflicted with the spec's two-level flow: Dashboard → click client → Client Workspace with scoped tabs. Users found the disabled tabs confusing and there was no back navigation.

**Decision:** Restructure to a two-level view: BrokerWorkbench switches between `dashboard` view and `client` view. The `client` view is a new `ClientWorkspace` component containing tabbed sub-views (Research, Submissions, Quote Comparison) all scoped to one `clientId`.

**Architecture Pattern:** Replicate the mortgage workbench pattern — single entity scoping, header with persistent context, tabs within a workspace, props-down/events-up state flow, no global store.

**Key Components:**
- `ClientWorkspace.tsx` (NEW) — tabbed workspace scoped to a client
- `ClientHeader.tsx` (NEW) — persistent context bar with back button
- `ResearchTab.tsx` (NEW) — replaces `ClientResearchPanel.tsx`
- `SubmissionsTab.tsx` (NEW) — submission list + create + drill-into-detail
- `QuoteComparisonTab.tsx` (NEW) — wraps existing `QuoteComparisonTable` with submission selector
- `SubmissionDetail.tsx` (renamed from `SubmissionBuilder.tsx`)
- `ClientResearchPanel.tsx` — DELETE (replaced by ResearchTab)

**New API Endpoints Needed (Ben):**
- `POST /api/broker/submissions/{id}/documents` — client doc upload
- `POST /api/broker/submissions/{id}/generate-package` — ACORD package generation

**Blueprint:** `broker-ux-redesign.md` in session files

**File Paths:**
- Broker components: `frontend/src/components/broker/`
- API client: `frontend/src/lib/broker-api.ts`
- Types: `frontend/src/lib/broker-types.ts`
- Backend router: `app/broker/api.py`
- Page integration: `frontend/src/app/page.tsx` (lines 128-146, no changes needed)
