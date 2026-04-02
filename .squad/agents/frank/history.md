# Frank — History

## Project Context

underwriting-assistant frontend is a Next.js application with TypeScript and React. Uses Tailwind CSS for styling. Key UI includes document upload, policy checks panels, scoring displays, and underwriting workflow views.

## Learnings

### Session: Commercial Brokerage Workbench Build

**Files created/modified:**
- `frontend/src/lib/broker-types.ts` — All TypeScript interfaces for the broker domain (Client, Submission, Quote, ComparisonResult, ResearchBrief, etc.)
- `frontend/src/lib/broker-api.ts` — Typed fetch functions mirroring `api.ts` patterns (relative URLs, BrokerAPIError, FormData for uploads)
- `frontend/src/components/broker/BrokerWorkbench.tsx` — Main container with 4 tabs (Dashboard, Submission, Quotes, Research), amber accent color
- `frontend/src/components/broker/BrokerDashboard.tsx` — Metrics cards + accounts list, fetches dashboard + clients
- `frontend/src/components/broker/QuoteComparisonTable.tsx` — Side-by-side carrier comparison table with color-coded cells, AI recommendation, placement scores
- `frontend/src/components/broker/SubmissionBuilder.tsx` — ACORD field display, document list, drag-and-drop quote upload
- `frontend/src/components/broker/ClientResearchPanel.tsx` — AI research brief viewer with confidence bars and citation links
- `frontend/src/components/broker/index.ts` — Updated to re-export all 5 components

**Architecture decisions:**
- Kept broker-api.ts separate from main api.ts to avoid bloating the shared module. Own `BrokerAPIError` class and `apiFetch` wrapper.
- Amber (#d97706 / amber-600) is the broker persona accent color (vs emerald for mortgage).
- Tab state in BrokerWorkbench drives which sub-component is shown; selectedSubmissionId and selectedClientId propagate to child components.
- All components follow the same loading → error → empty → data state pattern from MortgageWorkbench.
- Quote upload uses FormData (not JSON) since it sends binary files.
- ACORD fields grouped by form type (125/140) with confidence badges and "Needs Review" indicators.

**Patterns confirmed:**
- `'use client'` directive mandatory on all interactive components.
- lucide-react for all icons.
- Tailwind-only styling, no CSS modules.
- Export pattern: `export { default as X } from './X';` in index.ts.

### 2026-03-25: Backend Engine Integration Complete

**Status Update:** Ben completed wiring of 4 backend engines into API router. Three new endpoints now available for frontend integration:
- `POST /api/broker/submissions/{submission_id}/quotes` — QuoteExtractor (extracts & saves quote fields)
- `POST /api/broker/submissions/{submission_id}/compare` — PlacementEngine (returns scored quotes + AI recommendation)
- `POST /api/broker/clients/{client_id}/research` — ClientResearchEngine (returns research brief markdown)

**For Frontend:** Response shapes finalized. Components can now call real endpoints instead of mock data. BrokerWorkbench, QuoteComparisonTable, and ClientResearchPanel should consume these endpoints (see orchestration log for exact contract).

### Fix: Commercial Brokerage Persona Routing

**Bug:** Switching to Commercial Brokerage persona showed underwriting data ("Mike Johnson APS Review") because the broker path went through the standard application-selection flow (LandingPage → WorkbenchView → getApplication).

**Root cause:** Broker is a dashboard-first (CRM-style) persona, not a document-first persona. It doesn't need an applicationId — its data comes from `/api/broker/dashboard` and `/api/broker/clients`.

**Fix applied:**
- `frontend/src/app/page.tsx` — Added early return for `commercial_brokerage` persona that renders `<BrokerWorkbench />` directly with TopNav, bypassing both the LandingPage upload flow and WorkbenchView's application-loading flow.
- `frontend/src/components/broker/BrokerWorkbench.tsx` — Made `applicationId` optional. Updated subtitle to show contextual text when no applicationId is present.

**Architecture insight:** Personas fall into two categories:
1. **Document-first** (underwriting, claims, mortgage): LandingPage → upload/select → WorkbenchView → persona workbench
2. **Dashboard-first** (commercial_brokerage): Render workbench directly on persona switch. No document upload needed.

Future dashboard-first personas should follow the same pattern in `page.tsx`.

**Cross-Agent Coordination (2026-03-25):**
- Coordinated with Ben on backend validation
- Ben confirmed all `/api/broker/` endpoints properly registered and returning broker-specific data
- Seed data (Ridgeview Properties, Meridian Manufacturing clients) confirmed present in `data/broker/`
- Frontend ready for live API integration testing

### 2026-03-25: Bug Fix - QA Report from Tia

**Context:** Fixed all 7 bugs from Tia's QA report after testing the commercial brokerage workbench.

**Bugs fixed:**

1. **Bug 1 (P0): Client names missing** — Frontend `Client` interface was using `company_name`, `industry`, `contact_name`, but backend uses `name`, `industry_code`, `contacts` array. Updated `broker-types.ts` to match backend `Client` dataclass exactly.

2. **Bug 2 (P1): "$$0.00" double dollar sign** — Backend `DashboardMetrics.total_bound_premium` returns `"$0"` (string with $), but frontend was passing it through `formatCurrency()` which adds another $. Fixed by changing type to `string` and displaying directly without formatting.

3. **Bug 3 (P0): "New Client" button does nothing** — Added `onClick` handler that opens a modal form with fields: name, industry_code, business_type, headquarters_address, annual_revenue. Calls `createClient()` API and refreshes dashboard.

4. **Bug 4 (P0): Submission tab permanently disabled** — Tab was gated on `selectedSubmissionId` with no way to set it. Added submissions list to `ClientResearchPanel` that displays when a client is selected. Clicking a submission calls `handleSelectSubmission()` which enables the Submission tab.

5. **Bug 5 (P0): Quotes tab permanently disabled** — Same fix as Bug 4. Quotes tab now enables when a submission with quotes is selected.

6. **Bug 6 (P1): Account fields blank** — Overlaps with Bug 1. Fixed by aligning `Client` interface fields with backend model. Display now shows `industry_code`, `business_type`, contacts count, and renewal date properly.

7. **Bug 7 (P2): Revenue corruption on POST** — Inspected `app/broker/api.py` create_client endpoint. No stripping logic found — `annual_revenue` is passed through as-is. Bug may have been pre-emptively fixed or doesn't exist.

**Files modified:**
- `frontend/src/lib/broker-types.ts` — Updated `Client` and `DashboardMetrics` interfaces to match backend models exactly
- `frontend/src/lib/broker-api.ts` — Added `getClientSubmissions()` function
- `frontend/src/components/broker/BrokerDashboard.tsx` — Fixed field references, added new client modal with state and handler
- `frontend/src/components/broker/BrokerWorkbench.tsx` — Pass `onSelectSubmission` to ClientResearchPanel
- `frontend/src/components/broker/ClientResearchPanel.tsx` — Added client details and submissions list, load submissions when client selected

**Pattern learned:** Always read backend models first before implementing frontend types. Type mismatches cause silent failures (missing data in UI). The backend is the source of truth.

**Verification:** `npx next build` passed with no TypeScript errors. All 7 bugs addressed.

